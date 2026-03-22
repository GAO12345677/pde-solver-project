# Real World Benchmark

这个目录是给“真实案例 benchmark”单独预留的，不改你当前 solver 主代码。

## 目标

- 收集公开、学术来源的 PDE benchmark / dataset / literature case
- 建立一个 `real_world_benchmark` 库
- 先跑你项目当前能直接对齐的案例
- 再把外部 SOTA 结果并进来做对照

## 为什么要独立目录

因为这样最安全：

- 不会乱改 `solver/`
- 不会乱改 `api/`
- 不会乱改 `static/`
- Trae 只需要执行脚本，不需要到处改你的主工程

## 已准备好的文件

- [literature_cases.json](/D:/cursorku/real_world_benchmark/literature_cases.json)
- [latest_local_results.json](/D:/cursorku/real_world_benchmark/latest_local_results.json)
- [latest_report.md](/D:/cursorku/real_world_benchmark/latest_report.md)
- [sota_results.template.json](/D:/cursorku/real_world_benchmark/sota_results.template.json)

## 直接运行

在项目根目录执行：

```powershell
D:\cursorku\.venv\Scripts\python.exe scripts\real_world_benchmark.py all
```

它会做四件事：

1. 生成公开来源清单
2. 跑当前项目可直接对齐的本地 benchmark
3. 生成 SOTA 结果模板
4. 输出一份 markdown 报告

## 给 Trae 的安全要求

只允许 Trae 做这些事：

- 运行 `scripts/real_world_benchmark.py`
- 往 `real_world_benchmark/` 目录写文件
- 往 `sota_results.json` 填外部基线数据

不要让 Trae 直接改这些：

- `solver/numerical_solver.py`
- `api/routes.py`
- `static/src/*`
- `algorithm/selector.py`

## SOTA 怎么补

先把模板复制一份：

```powershell
Copy-Item D:\cursorku\real_world_benchmark\sota_results.template.json D:\cursorku\real_world_benchmark\sota_results.json
```

然后把文献或外部复现实验结果填进去，再执行：

```powershell
D:\cursorku\.venv\Scripts\python.exe scripts\real_world_benchmark.py compare
```

## 当前脚本的边界

它已经能做：

- 公开来源收集
- 本地对齐案例 benchmark
- 外部 baseline 合并
- markdown 报告输出

它暂时还不自动做：

- 自动下载超大公开数据集
- 自动训练外部 SOTA 模型
- 自动适配所有 PDEBench / PDEArena 数据格式

这些后续可以逐步接，但最好保持增量式，不要一次性把主工程改乱。
