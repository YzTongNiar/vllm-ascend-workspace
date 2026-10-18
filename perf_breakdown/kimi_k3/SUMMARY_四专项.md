# Kimi K3 fullgraph multistream 8k — 四专项分析（通信/显存/负载不均/同步时延）

- 数据：`/home/t00886357/kimik3/kimik3_d_old/glm52_dspark7_fullgraph_multistream_8k_nostack_memory_26`（8×Ascend 910, TP=8/EP=TP, vllm fullgraph + DSpark 投机解码, w4a8 MX 量化）
- 迭代结构：每引擎步 = 1×5层 DSpark draft（eager, 流346）+ 1×78层主干 verify（fullgraph, 流349）
- 节奏：图执行 37.4ms + 步间空隙 8.5ms ≈ **46ms/迭代**（28 步实测）

## ① 通信（每卡每步，28 步均值）
| 算子 | 次数/步 | 时长/步 | 流 |
|---|---|---|---|
| aiv_reduce_scatter_bf16 | 82 | 1.90ms | 348 |
| aiv_all_gather_bf16 | 95 | 1.15ms | 348(29.1)+345(3.1) |
| aiv_allreduce_bf16 | 18 | 0.86ms | 345 |
| 合计 | 195 | 3.9ms(r0/1/6/7) / 3.0ms(r2-5) | 占迭代 7~8.5% |

- communication.json/HCCL 细粒度计数未采上（Transit 0MB、全 Idle），带宽无法评估，需 aic_metrics=Memory 级别复采才能定量
- 特征：次数多、单次小（RS 单次 ~23µs）→ 有合并/大粒度化空间

## ② 显存（memory_record.csv，8 卡完全一致）
- 稳态 Reserved 89.1GB（峰 92.0），Active 峰 83.4GB（计数器口径可能含池/跨设备，相对结论有效）
- 采集窗口 1.04s 内无增长 → 无泄漏
- 每步 2× `aten::index` 0.141GB 瞬时大分配（life≈0）+ `aten::fill_`/`copy_` 高频churn；multistream 每流独立 pool 放大碎片风险

## ③ 负载不均
- 算子层：Σdur 差 3.5%（34.5~35.8ms/步）、MoE GroupedMatmul 差 2.8%、GroupedMatmul 次数 150/步 8 卡相同；扣除通信后计算本体均 ≈31.7ms → **EP 不均衡本身温和**
- 真正不均暴露在通信等齐：rank0/1/6/7 的 RS(+0.73ms)/AR(+0.39ms)/Combine(+0.09ms) 比 rank2-5 同算子更长 → **半数卡在集合通信里等另外半数**，每步 ~1.1ms（2.4%）
- 8 卡每步 wall 37.1~38.2ms，同步由 TP+EP 集合通信驱动

## ④ 同步时延（最大项）
- 步间 8.9ms 空隙剖析（rank0 实测）：
  - 流346 draft 头 eager 前向 1.38ms（MatMulV3+FusedInferAttentionScore）
  - 流345 残余通信 1.08ms（allreduce 0.97）
  - 流61 采样/索引/Slice 0.83ms
  - 流51/N/A 碎片 0.24ms
  - **纯空闲 ≈5.5ms（占迭代 12%）= host 侧 vllm scheduler + dspark accept/reject + 下一步图启动**
- 图内主流 349 连续 3000 算子无大空洞，与通信流 348/预取流 347 并发

## 优化方向（按收益排序）
1. 压 5.5ms host 空隙：采样/accept-reject 下沉图内、CPU 流水化（预计 -8~10% 迭代）
2. 通信等待不对称（0/1/6/7 vs 2/3/4/5）：查 HCCS 拓扑亲和与 multistream 预取是否与主流争带宽（预计 -1ms/步）
3. RS/AG 细粒度合并（82+95 次/步 → 更少更大）（预计 -0.5~1ms/步）
4. 显存：index 瞬时 0.14GB×2/步复用 buffer；multistream pool 碎片监控
