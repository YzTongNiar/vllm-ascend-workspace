# kimik3_A3_p — P（prefill）阶段分析（PD 分离部署）

数据：`kimik3_A3_p`（kimi-k3-1006-pd-prof_random_40k_p, rank0, span 10.75s）；zip 名表明 PD 分离 + random 40k 负载。仅 rank0、无 memory 采集。

## 拓扑画像

- **模型**：~96 层变体（72 KDA + 24 MLA 全注意力 + 92 MoE 层，4 dense 头），与 A5 decode 同族但层数略异
- **prefill 走 Chunk 路径**：`ChunkKdaFwd`（非 decode 的 RecurrentKda）+ `FusedInferAttentionScore`（MLA prefill）
- **6 次 chunked 前向**，各 ~1.8s（40k tokens ÷ 6 chunks），起点 0.04/1.75/3.57/5.37/7.17/8.97s
- **全局利用率 97.4%**——设备不闲，但构成是"计算 + 大量通信重叠"

## 关键发现：KV 广播半重叠，后半前向通信 bound

| 项 | 量化 |
|---|---|
| KV broadcast | **4 次 × 1.36–1.39s**（@2.14/4.39/6.65/8.91s，各横跨一个前向的后 ~76%）|
| broadcast 期间主流计算占比 | 仅 **~51%**（695ms 计算 / 1360ms 广播窗口）→ 前向后半段被 KV 传输拖住 |
| send（KV 分块外送） | 96 次 × ~10.5ms = 1.01s |
| EP alltoallv（MoE dispatch） | 1656 次 / 1.63s |
| TP RS / AG | 1152 次 0.92s / 1800 次 0.80s（细粒度逐层，与 decode 同病）|
| 主计算（流47） | 5.65s：GroupedMatmul 1.40s + ChunkKdaFwd 1.33s + QuantMatmul 0.94s + FusedInferAttn 0.49s + 其他 |
| 量化/反量化开销 | DynamicQuantV2 0.67s + DequantSituQuant 0.78s + WeightNz 0.94s ≈ **主计算的 25%+** |
| AivKernel（流40） | 2208 次 1.64s（通信辅助核）|

## P 阶段问题清单（按影响排序）

1. **KV 广播未全重叠**：每前向 ~1.36s 广播期间主流半闲——若把 KV 分层细粒度流水（算完一层发一层）或压缩 KV（w4a8 已有量化通道），可把前向 1.8s 压向 ~1.2s（-30% TTFT）
2. **量化/反量化占主计算 25%**：DequantSituQuant 0.78s 全窗（all2all 后专家输入反量化？），WeightNz+DynamicQuantV2 1.6s——prefill 有融合空间
3. TP RS/AG 细粒度逐层（1152+1800 次）与 decode 相同问题
4. 前 2 个前向无 KV 广播（warmup/本地？），冷启动 chunk 调度可优化

## 与 D（decode）画像对照

| | D (A5 ep32/ep64) | P (A3 pd) |
|---|---|---|
| KDA | RecurrentKda 递归核 | ChunkKdaFwd 分块核 |
| attention | FlashMlaWithKvcache | FusedInferAttentionScore |
| 主要矛盾 | 逐层 RS/AG 细粒度（15%）| **KV 广播半重叠 + 量化开销** |
| gap/步间 | 空闲 2-4%（已流水化）| 97.4% 利用率但通信占比高 |
| MoE | SituMxQuant 融合 | DequantSituQuant 仍分立（P 未上融合？）|

## 复采建议

- 全 rank + memory 采集；开 aic_metrics 量化通信带宽
- 确认 broadcast 对象（权重 vs KV）与目标节点数，评估压缩/流水方案
