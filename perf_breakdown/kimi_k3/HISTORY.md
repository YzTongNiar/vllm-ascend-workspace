# HISTORY

## 2026-10-14 — rank0_dspark7_8k（首次 run）

- **label**: rank0_dspark7_8k | **prof**: kimik3_d_old/glm52_dspark7_fullgraph_multistream_8k_nostack_memory_26（命名含 glm52 但实跑 Kimi K3）
- **模型结构**: KimiLinear 78 层 = 3×KDA-dense 头 + [3×attn-moe + 1×kda-moe]×18 + 3×attn-moe 尾 + DSpark 5 层 GQA eager draft（每步 1 draft + 1 verify）；锚点计数验证 KV=78/LI=21/MoE=75
- **sample 锁定**: 锚点推导（dense index：gqa 101-118@346+345aux、kda 384-402、attn layer3、dense_mlp layer0、moe layer3+347aux）；csv 无 Step Id 列，用主流 349 gap>3ms 合成 28 步（首尾剔除→26 稳定步，派生 kernel_details_steps125.csv）
- **cluster 规则**: kimi_k3_spec.json（attn/kda/moe/dense_mlp/gqa 五类，名字正则分桶）
- **已知缺口**: moe 尾部 6 层因 csv 行序错位未匹配（--accept-warnings）；unmatched 20.9% 为 348 逐层 TP 通信 + 尾 6 层 + draft 碎片 + 步首 embedding（--accept-unmatched）
- **渲染产物**: runs/rank0_dspark7_8k/{index.html, metrics.json}；splits/ 155 component 实例
- **关键观察**: 迭代 46ms = 37.4 图执行 + 8.5 步间空隙（纯空闲 5.5ms=12%）；步间空隙含 draft eager 尾巴/采样/残余 AR；单层 attn 165µs(SFA 50%)、kda 197µs、moe 171µs(experts 104µs, 347 流 overlap 17.3%)、dense_mlp 107µs(bubble 37µs)、gqa 265µs；通信 3.9ms/步(RS 1.9+AG 1.15+AR 0.86)；rank0/1/6/7 比 2-5 多等 1.1ms 集合通信；显存 8 卡一致稳态 89GB 无泄漏
