# Kimi K3 昇腾推理 Profiling 综合分析报告

> 分析日期：2026-10-14/15 ｜ 分析工具：model-infer-perf-breakdown / model-infer-profiling skill
> 数据：4 份 prof（见 §1）｜ 分析产物目录：`vllm-ascend-workspace/perf_breakdown/glm52_dspark7_fullgraph_ms8k/`

---

## 0. 执行摘要

1. **D 基线（globalbs32_dspark7，2026-10-15 更正数据）迭代 170.8ms = 133.9ms 主图 + 36.9ms 步间空隙**；空隙空闲仅 12%（被 allReduce 25.5ms + 采样填充）。⚠ 此前基于 `glm52_dspark7_8k` 的 46ms 迭代/四专项/逐层拆解结论**随错误数据作废**。
2. **新 D 基线三类占比：通信 44.3% 主导**（HcclLaunchAicpuKernel 54.4ms + hcom_allReduce 24.5ms/步，二者非双计）> 计算 33.3% > 访存 22.3%；attn 组计算 bound（54/46）、MoE 组均衡（51/49）+ 组内通信 23%；attention 用 FIA（非 ep32 的 FlashMla 大小核）。
3. **A5 新栈（ep32）系统性解决了 8k 的四大问题**：步间空隙流水化（空闲 62%→4%）、KDA/激活/attn-residual 三处算子融合（每层主流算子 36→23 个）、attention 换 MLA 栈、通信标准化 HCCL。
4. **ep64 证实 A5 栈批量扩展性**：BS32→BS128（4×），迭代仅 +9.8%（58.1→63.8ms），等效吞吐 ≈3.6×；通信占比微涨至 15.5%。
5. **通信细粒度逐层 RS/AG 是贯穿全部 4 份数据的共性遗留问题**（每次 ~18–24µs、每步 380 次左右、占比 7→15.5% 随规模上升），是下一阶段第一优化优先级。
6. **P 阶段（A3 PD 分离 prefill）的主要矛盾不同**：KV broadcast 半重叠（1.36s/前向，期间主流仅 51% 在算）+ 量化/反量化占主计算 25%+；设备利用率 97.4% 但近半时间在通信。
7. **P/D bound 形态对比**：D = 访存主导（53.4%）+ 通信 14.5%，MoE 访存 bound（Cube 未喂饱）；P = 通信主导（去重 a2a 双计后 ≈55%，KV broadcast/a2a），MoE 偏访存、attention 偏计算。
8. **数据局限**：后三份 prof 均仅 rank0、未开 memory 采集、HCCL 带宽计数未采上；负载不均与显存仅在 8k 有跨卡证据。

---

## 1. 数据集与配置总览

| # | 目录 | 阶段 | 芯片/并行 | 模型配置 | 采集窗口 | 步数 |
|---|---|---|---|---|---|---|
| D1 | `kimik3_d_old/globalbs32_dspark7`（**2026-10-15 更正**，原 glm52_dspark7_8k 数据有误已删） | decode | dspark7 投机解码, global BS32 | ~93 层家族：69 KDA（RecurrentKda）+ 24 MLA（**FusedInferAttentionScore**）+ 92 MoE；DSpark draft 5 层 | 3.22s | 24 |
| D2 | `kimik3_A5_d_ep32` | decode | A5, BS32/EP32/DCP, 无 draft | ~93 层 ≈ 1 + 23×[3 KDA-MoE + 1 MLA-MoE]（69 RecurrentKda + 24 MLA + 92 MoE） | 2.09s | 39 |
| D3 | `kimik3_A5_d_ep64` | decode | A5, BS128/EP64, 无 draft | 同 D2（92 MoE ✓ / 69 KDA ✓） | 2.09s | 36–37 |
| D4 | `kimik3_A3_p`（kimi-k3-1006-pd-prof_random_40k_p） | **prefill（PD 分离）** | A3, random 40k tokens | ~96 层 = 4 dense 头 + 92 MoE（72 KDA + 24 MLA 全注意力） | 10.75s | 6 chunk 前向 |

**跨数据集不可直接比绝对迭代时间**（配置不同）；可比的是栈级/结构级结论。

**方法备注**：4 份 csv 均无 `Step Id` 列，均用主计算流 gap 检测（>3ms）合成步边界；D1 另因首尾残缺步剔除 2 步。

---

## 2. D 基线（globalbs32_dspark7）分析结论

> ⚠ 原 §2（glm52_dspark7_8k 四专项：46ms 迭代/通信 3.9ms/负载不均/显存 89GB/步间空隙 5.5ms 纯空闲）基于**错误数据，已整体作废**。详细过程见 `analysis_rank_compare.txt`（保留仅作历史）。

- **迭代 170.8ms = 133.9 主图 + 36.9 步间空隙**；空隙空闲仅 12%（N/A allReduce 25.5ms + 采样 5.4ms 填充）
- **三类占比（busy 归属，Σ178ms/步）**：通信 44.3%（78.9ms：HcclLaunchAicpuKernel 54.4 + hcom_allReduce 汇总 24.5，互不嵌套非双计）> 计算 33.3% > 访存 22.3% —— **通信主导**
- Top5：HcclLaunch 54.4ms(通信) / FIA 29.2ms(计算，主干24+draft5) / GroupedMatmul 13.9(访存) / SituMxQuant 12.1(计算) / MatMulV3 7.8(计算)
- attn 组 35.0ms/步 **计算 bound**（54/46）；MoE 组 40.0ms/步 均衡（51/49）+ **组内通信 23%**（Dispatch/Combine 9.05ms）
- 栈：与 ep32 同代（RecurrentKda/SituQuant/V5），差异 = attention 用 FIA 而非 FlashMla、含 draft、通信以 allReduce 为主
- 局限：仅 rank0、无 memory 采集

## 3. 栈演进对照（⚠ 基于已作废的 glm52 数据，保留作历史参考；新基线已是同代栈，与 ep32 的实际差异 = attention 后端 FIA→FlashMla 大小核、draft 有无、通信 allReduce→RS/AG）

以下"旧算子→新算子"表中 LightningIndexer/SparseFlashAttention/SwigluGroupQuant 等旧栈特征在新基线中已不存在（新基线直接是 RecurrentKda/SituQuant 栈），该表描述的是更早版本的演进

### 3.1 算子栈替换对照

| 模块 | D1（8k/dspark7） | D2（ep32/A5） | 性质 |
|---|---|---|---|
| KDA | LightningIndexer(35µs)+SFA(76µs)+Transpose 胶水（chunk_kda） | **RecurrentKda + CausalConv1dV2 融合核**；KDA 投影独立侧流（506） | 算子融合 + 多流 |
| attention | GQA 路径 SparseFlashAttention | **FlashMlaWithKvcache + MlaPrologV3 + 量化 KV/Query triton 核** | MLA 栈 |
| MoE 激活 | SwigluGroupQuant + GroupedMatmul 分立 | **SituMxQuant + GroupedMatmulSituQuant 融合**；专家单层 ~111µs 持平（BS32 下） | 融合 |
| 量化 matmul | QuantBatchMatmulV3 | V5（主流）+ WeightNz V4（专家流） | 升级 |
| attn residual | LayerNormV4/MatMulV3/rope 碎算子拼装 | **AttnResFwdFused**（csv 中名字为 "0" 的核，187/步, 1.66ms/步） | 融合 |
| 通信 | aiv 自绘核（vector core） | HCCL 标准 AICPU（hcom_*） | 路径标准化 |
| 算子密度 | 主流 ~36 算子/层（3000/83 层） | **~23 算子/层**（2163/93 层，层数还更多） | 融合总收益 |

### 3.2 问题解决对照

| D1 暴露的问题 | D2 的状态 | 证据 |
|---|---|---|
| 步间纯空闲 5.5ms（12%） | ✅ **已解决**：gap 5.08ms 内 union busy 4.87ms，**空闲仅 4%**（D1 为 62%）；TP 通信 launch/下步预处理/采样被流水填入空隙（流 562/560/61/57/559） | gap 剖析 |
| draft eager + 采样在步外 | ✅ 配置移除（无 draft 算子） | 锚点计数 |
| KDA 拼装开销 | ✅ 专用融合核 | LightningIndexer/SFA/Transpose 消失 |
| 激活/量化分立 | ✅ Situ 融合 | SwiGlu 类消失 |
| MoE 多流覆盖浅（overlap 17.3%） | ✅ 专家流 busy 10.2ms ≈ 主流步内空闲 10ms，基本全遮蔽 | 流统计 |
| 通信细粒度 | ⚠️ **未解决且占比升高**（8.5ms/步，14.6%） | hcom AG 194 次 + RS 186 次/步 |

---

## 4. 规模扩展：D2 → D3（ep32 → ep64）

| 指标 | D2 (BS32/EP32) | D3 (BS128/EP64) | 解读 |
|---|---|---|---|
| 迭代 | 53.1+5.0 ≈ 58.1ms | 57.2+6.6 ≈ 63.8ms | **BS×4 迭代仅 +9.8%，吞吐 ≈3.6×** |
| 主流 busy | 43.1ms | 43.6–44.7ms | 主流算子时间几乎不变 |
| 专家流 | 10.2ms | 9.5ms | MoE 专家时间持平 |
| 主流步内空闲 | ~10ms | 12.5ms（专家流遮蔽大部分） | 多流 overlap 维持 |
| 通信/步 | 8.5ms (14.6%) | **9.87ms (15.5%)**：AG 194 次 4.47 + RS 186 次 3.98 + a2a 29 次 0.75 + AR 12 次 0.67 | 单次成本 ~18–24µs 不变；EP 切分本身无额外开销，绝对值随规模微涨 |
| gap 利用 | 空闲 4% | 空闲 2% | 流水保持 |

**结论**：A5 栈在 BS32→BS128 区间扩展性优秀；通信占比随规模继续走高，成为第一优先级。

---

## 5. P 阶段（D4，A3 PD 分离 prefill）

### 5.1 拓扑与节奏
- prefill 走 **Chunk 路径**：`ChunkKdaFwd`（432 次）替代 decode 的 RecurrentKda；MLA 用 `FusedInferAttentionScore`（288 次）
- 40k tokens 分 **6 个 chunk 前向 × ~1.8s**；全局利用率 **97.4%**（10469/10749ms union busy）

### 5.2 主要矛盾：KV broadcast 半重叠
| 项 | 量化 |
|---|---|
| hcom_broadcast | **4 次 × 1.36–1.39s**，各横跨一个前向后 ~76% 窗口 |
| broadcast 期间主流计算占比 | **仅 ~51%**（695ms 计算/1360ms 窗口）→ 前向后半段被 KV 传输拖住 |
| send（KV 分块外送） | 96 次 × ~10.5ms = 1.01s |
| EP alltoallv（MoE dispatch） | 1656 次 / 1.63s |
| TP RS / AG | 1152 次 0.92s / 1800 次 0.80s（细粒度逐层，与 decode 同病） |

### 5.3 计算热点（主计算流 47，全窗口 5.65s）
| 算子 | 总时长 |
|---|---|
| GroupedMatmulWeightNz | 1.40s（1104 次） |
| ChunkKdaFwd | 1.33s（432 次） |
| QuantMatmulWeightNz | 0.94s |
| FusedInferAttentionScore | 0.49s（288 次） |
| **量化/反量化小计（DynamicQuantV2 0.67 + DequantSituQuant 0.78 + WeightNz 0.94）** | **≈ 主计算 25%+**——P 未上 D2 的 Situ 融合 |

### 5.4 P 阶段问题清单
1. **KV 广播未全重叠**（预计 TTFT 可压 ~-30%）：分层细粒度流水（算完一层发一层）或 KV 压缩
2. 量化/反量化占主计算 25%+：prefill 侧 Situ 融合迁移
3. TP RS/AG 细粒度逐层（同 decode）
4. 前 2 个前向无 KV 广播（warmup/本地？）——冷启动 chunk 调度可查

---

## 6. P vs D：访存 / 通信 / 计算 bound 对比

> 判定口径：计算 = `aic_mac + aiv_vec + scalar` 流水时间（Cube 乘加 + Vector ALU）；访存 = `mte1/2/3 + aiv_mte2/3 + fixpipe`（搬运引擎 + 回写）；通信按算子名单（hcom / AicpuKernel / aiv_* / AivKernel）。MIX 核 AIC/AIV 双流水并行、比率可 >100%，故按流水时间判定。busy 按流求和（多流重叠可 >wall），占比按 busy 归属。D=ep32（A5@BS32），P=A3_p（A3@40k chunk）——形态对比，非同条件 A/B。

### 6.1 三类占比（每步，按 busy 归属）

| | **D**（53.6ms wall/步） | **P**（1791ms wall/前向） |
|---|---|---|
| **通信** | 10.2ms / **14.5%** | **去重后 ≈1783ms / 54.7%**（原始 2056ms/63.0% 含 a2a 双计：`AivKernel` 执行片段与 `hcom_alltoallv` 汇总为同一批通信，1656 个一一对应、75% 落在汇总窗口内；另含 KV broadcast 0.92s 汇总口径，与计算重叠） |
| **计算 bound** | 22.7ms / 32.1% | 623ms / 19.1% |
| **访存 bound** | 37.7ms / **53.4%** | 583ms / 17.9% |

D = "访存主导 + 通信次之" 的 decode 形态；P = "通信主导"（broadcast/a2a/send 占 63%）。

### 6.2 算子耗时 Top10 × bound

**D（ep32）**

| # | 算子 | ms/步 | n/步 | bound | 流水 mac/mte/vec % |
|---|---|---|---|---|---|
| 1 | GroupedMatmulSituQuant | 10.39 | 92 | **访存** | 53/185/68 |
| 2 | MatMulV3Common | 6.59 | 314 | **访存** | 36/99/0 |
| 3 | **FlashMlaWithKvcache·big_quant**（量化 cache，512+64 拆存） | 5.15 | 24 | **计算** | 59/41 |
| 3b | **FlashMlaWithKvcache·small_bf16**（bf16 cache，576 合并） | 1.23 | 29 | 计算 | 57/43 |
| 4 | GroupedMatmulWeightNz | 5.53 | 92 | **访存** | 49/173/65 |
| 5 | SituMxQuant | 5.46 | 92 | 计算 | 0/21/29 |
| 6 | QuantMatmulWeightNz V4 | 4.26 | 184 | **访存** | 19/104/18 |
| 7 | QuantMatmulV5 | 4.05 | 255 | **访存** | 25/119/0 |
| 8 | MoeDistributeDispatchV3 | 2.39 | 92 | 通信 | — |
| 9 | MoeDistributeCombineV3 | 1.88 | 92 | 通信 | — |
| 10 | RecurrentKda | 1.82 | 69 | 计算 | 0/19/70 |

**P（A3_p）**

| # | 算子 | ms/前向 | n/前向 | bound | 流水 mac/mte/vec % |
|---|---|---|---|---|---|
| 1 | **all2all**（=`AivKernel` 执行片段 ≡ `hcom_alltoallv` 汇总，MindStudio 显示为 all2all） | 271.3 | 276 | **通信** | —/64/— |
| 2 | GroupedMatmulWeightNz（Insight: gmm） | 232.8 | 184 | **访存** | 37/150/11 |
| 3–6 | hcom_broadcast ×4（N/A 汇总行，Insight 算子榜不收录） | ~228 | 1 | **通信**（KV 广播，含等待） | — |
| 7 | ChunkKdaFwd（Insight: chunkKDA） | 222.2 | 72 | **计算** | 1/16/16（vec 主导） |
| 8 | QuantMatmulWeightNz V3 | 156.2 | 496 | **访存** | 50/125/23 |
| 9 | DequantSituQuant | 130.8 | 184 | 计算 | 0/17/72 |
| 10 | DynamicQuantV2 | 111.0 | 496 | **访存** | 0/26/66 |

> **与 MindStudio Insight 的对照**：Insight 算子总耗时 = 全窗口总量（本表 ×6）；名字为算子层（all2all/gmm/chunkKDA）而本表用 csv 原始 `Name`；Insight 算子榜不收录 N/A 流 hcom 汇总行（broadcast/AG/RS 汇总在通信视图）。已验证等式：gmm 232.8×6=1396.6ms ✓、chunkKDA 222.2×6=1333.5ms ✓、all2all 271.3×6≈1627.6ms（hcom_alltoallv）≈1638ms（AivKernel 片段）✓。

### 6.3 Attention / MoE 的 bound 结论

| 组 | D | P |
|---|---|---|
| **Attention** | **计算 bound**（流水 59% vs 访存 41%；FlashMla 计算 + RecurrentKda vec 计算） | 均衡偏计算（51% vs 49%；ChunkKdaFwd 计算主导 + FusedInfer 拉回访存） |
| **MoE** | **访存 bound + 通信显著**（44% vs 56%；dispatch/combine 组内 4.3ms = MoE 的 14%，另有 RS/AG 在组外） | **访存 bound**（48% vs 52%；a2a dispatch 记在通信桶未入组，计入则通信占比更高） |

### 6.3b MLA 深挖（2026-10-16 追加）
- **FlashMla 大小核流水**：big_quant scalar 合计 28.8%（aic_scalar 单项最大 16.7%）；small_bf16 scalar 合计 23.5% > mac 21.2%——scalar bound 来源 = block_table 逐页间接寻址 + KV 首轴非连续（MTE 无法跨页 burst）+ 逐 tile scale
- **KV 首轴非连续（PR #18256）**：cache [pages,128,h,dim] 的 stride(0) > 128×h×dim。K3 成因：① hybrid 池（MLA 页 + KDA conv/SSM state 页共池对齐，物理页含 padding）；② component-major：nope(512)/rope(64) 按页交错存同一 raw buffer（stride(0)=2×page，页序 [nope₀][rope₀][nope₁]…）；③ 多层共享 backing。对策：as_strided 保几何 + strided 读写全路由 npu_mla_prolog_v3（profiling 中 MlaPrologV3 24/步 的来源）

### 6.4 核心洞察

1. **D 的 MoE（占 busy 43%）是访存 bound**——w4a8 NZ 权重组矩阵乘 mac 仅 ~50%、搬运引擎 170%+，Cube 没喂饱；专家流独立成流正是用访存并行度换吞吐。优化方向：权重布局/缓存友好、增大合并粒度。
2. **P 的主要 bound 是通信（去重后 ≈55%）**而非计算/访存——KV broadcast + a2a + send 且重叠不足，优化优先级高于算子本身。
3. 量化/反量化类在 P 侧合计 ~370ms/前向（DequantSituQuant 为 vec 计算主导）——融合进 GroupedMatmul（D 侧 SituQuant 做法）可同时省计算与访存。

## 7. 汇总：问题—优化优先级矩阵

| 优先级 | 问题 | 证据数据集 | 建议动作 | 预期收益 |
|---|---|---|---|---|
| P0 | 逐层细粒度 RS/AG 通信（380 次/步，占比 7→15.5% 随规模上升） | 全部 4 份 | 层间通信合并/大粒度化、TP→SP/序列并行重切 | D 端 -1~2ms/步；占比封顶 |
| P0 | P 阶段 KV broadcast 半重叠 | D4 | 分层流水外送 + KV 压缩 | TTFT ~-30% |
| P1 | P 阶段量化/反量化 25% | D4 | Situ 融合迁移到 prefill 路径 | P 主计算 -20%± |
| P1 | 通信等齐不对称（rank0/1/6/7 vs 2–5，1.1ms/步） | D1 | 查 HCCS 拓扑亲和/预取带宽争用；复采全 rank 验证 | -1ms/步（2.4%） |
| P2 | dense_mlp bubble 37µs/层；aten::index 瞬时 0.14GB×2/步 | D1 | buffer 复用；层内调度 | 微 |
| P2 | 8k 的 host 空闲 5.5ms | D1→已随新栈解决 | （已完成，作为回归基准） | — |
| P3 | 显存稳态 89GB 高占用 + multistream pool 碎片风险 | D1 | memory pool 监控；index 分配复用 | 稳定性 |

---

## 8. 数据局限与复采建议

1. **D2/D3/D4 仅 rank0 落盘** → 负载不均（EP32/EP64 的专家分布）无法跨卡验证；建议全 rank 采集
2. **D2/D3/D4 未开 memory 采集** → 显存仅 D1 有证据
3. **HCCL 带宽计数全部未采上**（communication.json Transit 0MB）→ 复采加 `aic_metrics=Memory/L2Cache`
4. D4 broadcast 对象（权重 vs KV）与目标节点数未确认——建议结合 serving 配置核实后再定优化方案
5. 同配置 A/B（同层数/同 batch）才能做绝对迭代时间归因

## 9. 产物索引

| 文件 | 内容 |
|---|---|
| `SUMMARY_四专项.md` | D1 通信/显存/负载不均/同步时延 |
| `analysis_PD_bound.txt` | P/D 三类占比 + Top10 bound + 组级 bound 过程数据（含 FlashMla 大小核分离） |
| `SUMMARY_D_baseline_globalbs32.md` / `analysis_D_new_globalbs32.txt` | 更正后 D 基线（globalbs32_dspark7）分析与过程数据 |
| `SUMMARY_ep32对比.md`（含 ep64 节） | 栈演进 + 规模扩展对比 |
| `SUMMARY_A3_p_prefill.md` | P 阶段画像 |
| `analysis_rank_compare.txt` / `analysis_ep32.txt` / `analysis_ep64.txt` / `analysis_A3_p.txt` | 全部过程数据 |
| `runs/rank0_dspark7_8k/index.html` + `metrics.json` | D1 逐层 cluster 抖动报告 |
| `splits/`（155 component 实例） | D1 逐层下钻切片 |
| `structure_spec.json` / `sample_ack.json` / `kimi_k3_spec.json` | D1 结构与规则（可跨 prof 复用） |
| `kernel_details_steps125.csv` | D1 合成 Step Id 的派生 csv |
| `HISTORY.md` | 运行日志（复用/变更/观察） |
