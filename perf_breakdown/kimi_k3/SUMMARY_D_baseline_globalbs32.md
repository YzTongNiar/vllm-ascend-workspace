# D 基线重分析 — globalbs32_dspark7（2026-10-15，替换已作废的 glm52_dspark7_8k 数据）

数据：`kimik3_d_old/globalbs32_dspark7`（rank0, 24 步, span 3.22s, global BS32, dspark7 投机解码）。
⚠ 之前基于 `glm52_dspark7_fullgraph_multistream_8k_nostack_memory_26` 的全部 D 基线结论（46ms 迭代/四专项/逐层拆解/步间空隙解剖）**随数据作废**。

## 模型与栈（锚点计数实测）
- ~93 层家族：69 KDA（RecurrentKda+CausalConv1dV2）+ 24 MLA + 92 MoE 层 + **DSpark draft 5 层**（FusedInferAttentionScore 696 = 24×24 主干 + 5×24 draft ✓）
- **MLA 用 `FusedInferAttentionScore`（FIA），不是 ep32/ep64 的 FlashMlaWithKvcache**——同家族不同 attention 后端
- 量化：QuantMatmulV5/WeightNz-V4 + SituMxQuant（与 ep32 同代）

## 迭代结构
- 24 步，**wall 133.9ms + 步间 gap 36.9ms ≈ 170.8ms/迭代**
- 步间空隙 37.5ms 中 union busy 33.05ms → **空闲仅 12%**（N/A allReduce 25.5ms + 采样 5.4ms 填充）——draft eager 尾巴问题在此配置下不显著，代之以通信填充

## 三类占比（按 busy 归属，busy Σ178ms/步，多流重叠）
| 类 | ms/步 | 占比 |
|---|---|---|
| **通信** | 78.9 | **44.3%**（HcclLaunchAicpuKernel 54.4 + hcom_allReduce 汇总 24.5；二者窗口互不嵌套、非双计） |
| 计算 bound | 59.3 | 33.3% |
| 访存 bound | 39.8 | 22.3% |

**通信主导**（对比 ep32 的 14.5%）——dspark7 配置下 TP 通信以 allReduce 为主（hcom_allReduce 单次最大 9ms）。

## Top12 × bound
| # | 算子 | ms/步 | n/步 | bound |
|---|---|---|---|---|
| 1 | HcclLaunchAicpuKernel | 54.42 | 205 | 通信 |
| 2 | FusedInferAttentionScore（主干 24 + draft 5） | 29.18 | 29 | 计算 |
| 3 | GroupedMatmulWeightNz | 13.86 | 184 | 访存 |
| 4 | SituMxQuant | 12.07 | 184 | 计算 |
| 5 | MatMulV3Common | 7.82 | 515 | 计算 |
| 6 | MoeDistributeCombineV3 | 5.45 | 92 | 访存 |
| 7 | QuantMatmulV5 | 5.30 | 255 | 访存 |
| 8 | MoeDistributeDispatchV3 | 3.59 | 92 | 计算 |
| 9 | RecurrentKda | 3.34 | 69 | 计算 |
| 10 | _apply_attn_res_kernel | 2.70 | 186 | 计算 |
| 11 | QuantMatmulWeightNz V4 | 2.30 | 184 | 访存 |
| 12 | DynamicMxQuant | 1.57 | 278 | 计算 |

## Attention / MoE bound
- **attn 组** 35.0ms/步：计算 54% vs 访存 46%（FIA 计算主导）→ **计算 bound**
- **MoE 组** 40.0ms/步：计算 51% vs 访存 49% + **组内通信 9.05ms（23%）**（Dispatch/Combine）→ 均衡偏计算但通信显著

## 数据局限
- 仅 rank0；**无 memory 采集**（无 memory_record/operator_memory）；HCCL 带宽计数未采上

## FlashMlaWithKvcache 大小核分离（ep32/ep64，本基线不适用——用的是 FIA）
| 数据集 | 变体 | n/步 | 单次均值 | ms/步 | bound |
|---|---|---|---|---|---|
| ep32 | **big_quant**（主干 MLA 量化段，q[32,96,512+64]） | 24 | 214.7µs | 5.153 | 计算（59/41） |
| ep32 | small_bf16·主干近端段（q[32,12,576]@流508） | 24 | 14.8µs | 0.355 | 计算 |
| ep32 | small_bf16·**DSpark draft**（q[24,64,576]@流562，扫全量 KV） | 5 | 175.5µs | 0.878 | 计算 |
| ep64 | big_quant | 24 | 422.5µs | 10.140 | 计算（59/41） |
| ep64 | small_bf16·主干近端段（q[64,12,576]@流404） | 24 | 15.3µs | 0.366 | 计算 |
| ep64 | small_bf16·DSpark draft（q[48,64,576]@流449） | 5 | 339.5µs | 1.698 | 计算 |

- 大小核都是**计算 bound**（~57-59%），特征差异在单次时长（5-6×）与覆盖 KV（量化全量 vs bf16 小段）
- ep64 vs ep32：大核单次 214.7→422.5µs（BS128 线性放大）、小核 42.5→71.2µs（亚线性）
- 小核 29/步 = **24 主干近端段 + 5 draft 层**：ep32/64 均有 DSpark draft（推 5 步），draft attention 走 FlashMla small_bf16 后端（流562/449），与主干近端段是同核不同形态（shape/时长/KV 范围完全不同）
