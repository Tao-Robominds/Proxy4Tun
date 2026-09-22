# Proxy comparison

Training rows: 120

- PQ: pooled Spearman 0.615, MAE 0.166; permutation mean -0.113 (std 0.056) vs unpermuted 0.615
  - complex: Spearman 0.466, MAE 0.210
  - continuous: Spearman 0.551, MAE 0.159
  - staggered: Spearman 0.595, MAE 0.130
- SC: pooled Spearman 0.758, MAE 0.147; permutation mean -0.123 (std 0.073) vs unpermuted 0.758
  - complex: Spearman 0.930, MAE 0.110
  - continuous: Spearman 0.472, MAE 0.174
  - staggered: Spearman 0.870, MAE 0.158
- ten: pooled Spearman 0.686, MAE 0.165; permutation mean -0.109 (std 0.086) vs unpermuted 0.686
  - complex: Spearman 0.952, MAE 0.156
  - continuous: Spearman 0.320, MAE 0.200
  - staggered: Spearman 0.892, MAE 0.139
- four: pooled Spearman 0.809, MAE 0.129; permutation mean -0.121 (std 0.082) vs unpermuted 0.809
  - complex: Spearman 0.914, MAE 0.097
  - continuous: Spearman 0.488, MAE 0.152
  - staggered: Spearman 0.892, MAE 0.140

Frozen four-feature model: alpha=10.0, intercept=0.358867, n=120
