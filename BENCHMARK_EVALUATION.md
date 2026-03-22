# Benchmark Evaluation

生成时间：2026-03-22  
最新基线报告：[benchmark_1774185805.json](/D:/cursorku/benchmark/benchmark_1774185805.json)

## 1. 本轮已完成内容

- 已运行现有 benchmark：
  - `D:\cursorku\.venv\Scripts\python.exe -m test_case.benchmark_algorithms`
- 已完成三类评估：
  - 算法选择器精度
  - 不同 PDE / 不同算法的误差与耗时对比
  - 分辨率 sweep 下的平均误差与平均耗时对比

## 2. 当前 benchmark 已覆盖的案例

- `heat1d`: `fdm / fvm / fem / spectral / pinn`
- `poisson1d`: `fdm / fem / spectral / bem`
- `wave1d`: `fdm / fem / spectral`
- `heat2d`: `fdm / fvm / fem`
- `wave2d`: `fdm / fem / spectral`
- `heat3d`: `fdm / fvm / fem`
- `poisson3d`: `fdm / fem / bem`
- `wave3d`: `fdm / fem / spectral`

现在三维主线已经都进入 benchmark 体系了。

## 3. 选择器结果

### 3.1 精度

- `static_rf`: `1.000`
- `mlp_nn`: `1.000`
- `gnn_selector`: `1.000`
- `dynamic_rl`: `0.267`

### 3.2 解释

- 当前静态选择器在项目合成代表性数据集上表现非常稳定。
- `gnn_selector` 已经可以作为论文里“新增算法选择策略”的正向结果展示。
- `dynamic_rl` 当前明显弱于静态策略，更适合作为对照组或后续改进方向。

## 4. 各 PDE 的求解表现

这里把“最准”“最快”“综合较优”分开看，避免只看单一指标。

### 4.1 heat1d

- 最准：`spectral`
- 最快：`pinn`  
  但这个耗时几乎为 0，更像缓存/极简基线，不建议单独拿来强调。
- 更稳的工程结论：
  - `fdm`：速度快、误差低
  - `spectral`：精度最强，但更慢

### 4.2 poisson1d

- 最准：`spectral`
- 最快：`bem`
- 综合较优：`spectral`

### 4.3 wave1d

- 最准：`spectral`
- 最快：`spectral`
- 综合较优：`spectral`

这是当前最容易在论文里讲清楚的一类：  
`wave1d` 下 `spectral` 在精度和速度上同时占优。

### 4.4 heat2d

- 最准：`fdm`
- 最快：`fdm`
- 综合较优：`fdm`

`fvm` 与 `fdm` 接近，但 `fem` 当前基线更慢且误差略高。

### 4.5 wave2d

- 最准：`spectral`
- 最快：`fdm`
- 综合较优：`spectral`

这类结果适合说明：
- 如果追求高精度，`spectral` 更好
- 如果只看运行时间，`fdm` 更快

### 4.6 heat3d

- 最准：`fvm`
- 最快：`fvm`
- 综合较优：`fvm`

当前 `heat3d` 下 `fdm` 和 `fvm` 很接近，但本轮报告里 `fvm` 在精度和时间上都略占优。

### 4.7 poisson3d

- 最准：`fdm`
- 最快：`fdm`
- 综合较优：`fdm`
- `bem` 当前误差远大于 `fdm / fem`

所以 `poisson3d / bem` 现在更适合表述成：
- 已接入并可运行
- 可作为方法扩展展示
- 但当前数值精度不宜宣传为最优

### 4.8 wave3d

- 最准：`spectral`
- 最快：`fem`
- 综合较优：`fdm`

解释：
- `spectral` 精度几乎达到机器精度，但耗时略高
- `fem` 最快，但误差明显高于 `fdm / spectral`
- `fdm` 在精度和时间之间取得了更均衡的折中

这部分现在已经可以作为论文里“三维波动方程多方法对比”的正式实验结果。

## 5. “推荐是否最优或接近最优”目前能怎么说

### 5.1 可以比较稳地说的

- 在当前项目的合成代表性数据集上：
  - `static_rf / mlp_nn / gnn_selector` 精度都达到 `1.000`
- 对一些典型场景：
  - `wave1d_balanced` 中，`mlp_nn` 和 `gnn_selector` 推荐 `spectral`
  - 这与 benchmark 中 `wave1d` 的最优算法一致

### 5.2 新增的“推荐 vs benchmark”对照结果

本轮已经把 selector 推荐结果和 benchmark 最优算法对齐到同一份报告里。

当前命中情况如下：

- `heat1d_accuracy_oriented`
  - `static_rf / mlp_nn / gnn_selector`：命中
  - `dynamic_rl`：未命中
- `wave1d_balanced`
  - `mlp_nn / gnn_selector`：命中
  - `static_rf / dynamic_rl`：未命中
- `heat2d_standard`
  - `static_rf / mlp_nn / dynamic_rl`：命中
  - `gnn_selector`：未命中
- `wave2d_accuracy_oriented`
  - `static_rf / mlp_nn / gnn_selector`：命中
  - `dynamic_rl`：未命中
- `heat3d_balanced`
  - `mlp_nn / dynamic_rl`：命中
  - `static_rf / gnn_selector`：未命中
- `wave3d_accuracy_oriented`
  - `dynamic_rl`：命中
  - `static_rf / mlp_nn / gnn_selector`：未命中

因此目前更稳的判断是：

- `mlp_nn`：整体最稳，命中率较高
- `gnn_selector`：在 1D/2D 精度导向场景上表现好，但在部分 2D/3D 热传导和 wave3d 场景上还不够稳
- `static_rf`：在部分规则型案例中有效，但不如 `mlp_nn` 稳定
- `dynamic_rl`：整体精度仍低，但在个别 3D 平衡场景里会命中

### 5.3 还不能直接硬说“全局最优”的

当前推荐案例和 solver benchmark 不是一一完全对齐的同一批问题。  
因此更稳的说法是：

- `mlp_nn` 在当前代表性案例上，已经能较稳定给出与 benchmark 最优算法一致的推荐；
- `gnn_selector` 在部分代表性案例上也能命中 benchmark 最优算法，但还不稳定；
- 但要严格论证“推荐总是最优/接近最优”，还需要把推荐案例和 solver 基准案例做一一对齐实验。

## 6. 论文里建议采用的表述

可以这样写：

- 本文首先构建了多类 PDE 的数值 benchmark，包括 `heat / wave / poisson` 的一维、二维和三维问题。
- 在此基础上，对多种算法选择策略进行了评估。
- 实验表明，静态策略中的 `RF / MLP / GNN` 在当前代表性数据集上均取得较高选择准确率，其中 `MLP selector` 在本轮对齐 benchmark 的案例中表现最稳定，`GNN selector` 也能在部分典型场景下给出与 benchmark 最优解法一致的推荐。
- 对三维问题，`heat3d`、`poisson3d` 和 `wave3d` 已形成可比较的多方法矩阵。

## 7. 当前难点与限制

### 7.1 数据集限制

- 当前选择器精度主要基于项目内的合成代表性数据集，而不是真实工程案例库。
- 因此可以证明“在本项目定义的典型问题上推荐有效”，但还不能直接外推到所有真实问题。

### 7.2 benchmark 仍偏标准算例

- 当前解析解或 manufactured solution 较多。
- 这对论文实验是合理的，但如果要进一步证明工程价值，后面还需要补更真实的案例场景。

### 7.3 指标还不够全

- 当前已经有：
  - `L2 error`
  - `Linf error`
  - `elapsed time`
  - 部分三维 `boundary_residual`
- 但还没统一纳入：
  - 内存占用
  - 更系统的稳定性失败率
  - 推荐算法与最优算法的“距离”统计

## 8. 下一步最值得做的事情

### 第一优先级

- 新增“推荐对齐 benchmark”的案例集：
  - 同一组案例先让 selector 推荐
  - 再把所有算法都跑一遍
  - 判断推荐结果是否等于最优，或是否落在前二名

### 第二优先级

- 在 benchmark 里统一记录：
  - `best_by_error`
  - `best_by_time`
  - `best_balanced`
  - `selector_pick`
  - `selector_gap_to_best`

### 第三优先级

- 补更接近实际问题的案例：
  - 更密网格
  - 更复杂边界
  - 更长时间区间
  - 参数更极端的场景

## 9. 本轮结论

当前项目已经可以支持这样一个比较稳的结论：

- **项目不只是“能解 PDE”，而且已经可以通过 benchmark 比较不同算法的误差和效率，并初步验证算法选择模块是否合理。**

其中最强的结论点是：

- `RF / MLP / GNN selector` 在当前典型数据集上表现稳定，其中 `MLP` 在“推荐 vs benchmark”对齐实验里表现最好；
- `wave1d`、`heat2d`、`heat3d`、`poisson3d`、`wave3d` 等问题已经能形成“算法优劣比较”的实验支撑；
- 但若要更有说服力地证明“推荐接近最优”，还需要把推荐案例与求解基准进一步严格对齐。
