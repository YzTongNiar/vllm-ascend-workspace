# ep32（A5）vs 8k（dspark7）优化对比

数据：`kimik3_A5_d_ep32`（BS32/EP32/DCP, rank0, 39 步, 2.09s）vs `kimik3_d_old/...8k_nostack_memory_26`（TP8/EP8, rank0, 28 步, 1.04s）

## ⚠️ 不可直接比绝对值：配置本身不同

| | 8k (dspark7) | ep32 (A5) |
|---|---|---|
| 模型 | 78 层 = 3 KDA-dense 头 + 18×[3 attn+1 KDA] + 3 attn 尾 | ~93 层 = 1 + 23×[3 KDA-MoE + 1 MLA-MoE]，无 dense 头 |
| attention | GQA 路径 SparseFlashAttention (57 层) | **MLA**: FlashMlaWithKvcache + MlaPrologV3 (24 层) |
| 投机解码 | DSpark 5 层 draft（eager，步间空隙跑） | 无（窗口内无 draft 算子） |
| batch/并行 | 8k ctx, TP8=EP8 | BS32, EP32 + DCP |
| 迭代 | 37.4ms busy + 8.5ms gap ≈ 46ms | 53.1ms busy + 5.0ms gap ≈ 58.1ms |

## ✅ 已解决的 8k 问题

| 8k 问题 | ep32 对策 | 证据 |
|---|---|---|
| **步间纯空闲 5.5ms（12%）** | 尾部工作（TP 通信 launch、下步预处理、采样）流水填充空隙 | gap 5.08ms 内 union busy 4.87ms，**空闲仅 4%**（8k 为 62%）；流 562/560/61/57/559 在 gap 内并行 |
| **KDA 拼装开销**（LightningIndexer 35µs + SFA 76µs + Transpose 胶水） | **RecurrentKda + CausalConv1dV2 专用融合核**，KDA 投影独立到流 506 | LightningIndexer/SFA/Transpose 消失；RecurrentKda 69/step + CausalConv1d 69/step；流506 276 ops/step 2.5ms |
| **激活/量化分立**（SwigluGroupQuant + GroupedMatmul） | **SituMxQuant + GroupedMatmulSituQuant 融合**，量化 matmul 升 V5/V4 | SwiGlu 类消失；QuantBatchMatmulV5(主流) + WeightNz V4(专家流)；专家单层 ~111µs（8k 104µs，BS32 下持平） |
| **attn-residual 碎算子**（LayerNormV4/MatMulV3/rope 拼装） | **AttnResFwdFused 融合核** | "0"号算子实为 AttnResFwdFused（AI_VECTOR_CORE, 187/step, 1.66ms/step） |
| **主流算子密度低**（3000 ops/83 层 ≈ 36/层） | 融合后 2163 ops/93 层 ≈ **23/层** | 主流 508 算子数下降 28%，层数反增 |
| **MoE 多流覆盖浅**（overlap 17.3%） | 专家流 505 busy 10.2ms ≈ 主流步内空闲 10ms，基本全遮蔽 | 505: 368 ops/step；主流 busy 43.1 vs wall 53.1 |

## ⚠️ 遗留/新问题

1. **通信仍是次大头且粒度未合并**：hcom allGather 194 次/step 4.22ms + reduceScatter 186 次 3.30ms + allReduce 12 次 0.52ms + alltoall 29 次 0.48ms ≈ **8.5ms/step（14.6%）**，细粒度逐层模式与 8k 相同（层数 92×每层 RS+AG）；EP32/DCP 规模放大了绝对值
2. **通信走 AICPU（HCCL）路径**，8k 是 aiv vector-core 自绘核——单次成本相当（~18-22µs），但 path 不同；hcom marker 挤在 N/A 流，难以做流级 bubble 归因
3. **负载不均/显存无法对比**：ep32 仅 rank0 落盘、未开 memory 采集（无 memory_record/operator_memory）
4. draft 移除后 8k 里 draft 的 1.4ms 步外开销消失，但吞吐损失投机收益——是配置取舍非纯优化

## 复采建议（如需补齐对比）

- ep32 补 memory 采集 + 全 rank 落盘（对比显存与 EP32 负载不均）
- 两次都开 `aic_metrics=Memory/L2Cache` 量化通信带宽
- 同配置 A/B（同层数/同 batch）才能把 58.1ms vs 46ms 归因到栈升级

---

# ep64 追加（2026-10-15）：EP64/BS128 vs EP32/BS32（同栈同模型 A/B）

数据：`kimik3_A5_d_ep64`（EP64_BS128_c8, rank0, 36-37 步, 2.09s）。模型与算子栈与 ep32 完全一致（92 MoE 层、RecurrentKda/FlashMla/SituQuant/AttnResFwdFused/hcom）。

| 指标 | ep32 (BS32/EP32) | ep64 (BS128/EP64) | 解读 |
|---|---|---|---|
| 迭代 | 53.1+5.0 ≈ **58.1ms** | 57.2+6.6 ≈ **63.8ms** | **BS×4 迭代仅 +9.8%** —— A5 decode 批量扩展性极好 |
| 主流 busy | 43.1ms | 43.6/44.7ms | 主流算子时间几乎不变（BS 增大被并行吃掉）|
| 专家流 | 10.2ms (505) | 9.5ms (401) | MoE 专家时间持平 |
| 主流步内空闲 | ~10ms | 12.5ms（专家流遮蔽大部分）| 多流 overlap 维持 |
| 通信/步 | 8.5ms (14.6%) | **9.87ms (15.5%)**：AG 194次4.47 + RS 186次3.98 + a2a 29次0.75 + AR 12次0.67 | 仍逐层细粒度，绝对值随 EP64 微涨；单次成本 ~18-24µs 不变 |
| gap 利用 | 空闲 4% | 空闲 2%（流449/61/575 填充）| 流水保持 ✓ |
| 显存 | 未采 | 未采 | 无法对比 ⚠️ |

**结论**：ep64 证实 A5 栈的批量扩展性（BS128 vs BS32 吞吐 ≈ 3.6×）；通信占比随规模继续走高（15.5%），仍是首要优化点（逐层 RS/AG 合并）。EP64 相比 EP32 通信单次成本未恶化，EP 切分本身没有引入额外开销。
