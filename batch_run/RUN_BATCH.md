## 无人值守批处理运行说明（Windows 10/11, Python 3.10）

本模块用于从 `input/` 目录读取 JSON 配置文件，批量执行：
**特征提取 → 算法选择 → 方程求解 → 结果评估**，
并把结果保存到 `output/`（含解/评估报告/图片），日志写到 `log/`。

---

### 1) 安装依赖

在项目根目录（`d:\cursorku`）执行：

```bash
pip install -r requirements.txt
```

---

### 2) 准备输入配置（`input/*.json`）

#### 示例 A：1D 线性热传导（heat1d）

保存为 `input/heat1d_case.json`：

```json
{
  "equation_type": "heat1d",
  "strategy": "static_rf",
  "k": 1.0,
  "L": 1.0,
  "nx": 101,
  "t0": 0.0,
  "t1": 0.05,
  "bc_type": "dirichlet",
  "left_bc": 0.0,
  "right_bc": 0.0,
  "initial": "sine_nonnegative",
  "enforce_nonnegativity": true,
  "domain": {
    "accuracy": "medium",
    "realtime": "high",
    "resource_budget": 0.5
  }
}
```

#### 示例 B：2D 非线性泊松（poisson2d_nonlinear）

保存为 `input/poisson2d_case.json`：

```json
{
  "equation_type": "poisson2d_nonlinear",
  "strategy": "dynamic_rl",
  "nx": 41,
  "ny": 41,
  "Lx": 1.0,
  "Ly": 1.0,
  "tol": 1e-6,
  "max_iter": 200,
  "domain": {
    "accuracy": "medium",
    "realtime": "medium",
    "resource_budget": 0.7
  }
}
```

---

### 3) 手动运行一次（推荐先跑通）

```bash
python -m batch_run.batch_processor --once
```

运行后会生成：
- `output/*_solution.json`：求解结果
- `output/*_plot.png`：可视化图片
- `result/report_*.json`：评估报告
- `output/batch_summary_*.json`：本次批处理汇总
- `log/YYYY-MM-DD.log`：日志

---

### 4) 定时任务（每天凌晨 2 点）

```bash
python -m batch_run.batch_processor --schedule --at 02:00
```

自定义时间（例如 01:30）：

```bash
python -m batch_run.batch_processor --schedule --at 01:30
```

---

### 5) 文件夹监控（input/ 新增 JSON 自动触发）

```bash
python -m batch_run.batch_processor --watch
```

同时启用“监控 + 定时”：

```bash
python -m batch_run.batch_processor --watch --schedule --at 02:00
```

---

### 6) 后台运行

#### 方式 A：pythonw（无控制台窗口）

在项目根目录运行：

```bash
pythonw -m batch_run.batch_processor --watch --schedule --at 02:00
```

日志查看：
- 打开 `log/` 下当天的 `YYYY-MM-DD.log`

#### 方式 B：PowerShell 后台启动

```powershell
Start-Process python -ArgumentList "-m batch_run.batch_processor --watch --schedule --at 02:00" -WindowStyle Hidden
```

---

### 7) Windows 开机自启（推荐：任务计划程序）

1. 打开“任务计划程序” → “创建基本任务”
2. 触发器选择：“当计算机启动时”
3. 操作选择：“启动程序”
4. 程序/脚本：填写你的 `pythonw.exe` 路径
5. 参数：`-m batch_run.batch_processor --watch --schedule --at 02:00`
6. 起始于：`d:\cursorku`

提示：
- 若权限/路径问题，先在命令行确认 `pythonw -V` 可用。

---

### 8) 异常排查方案

- **依赖缺失**：看日志里是否提示缺包，执行 `pip install -r requirements.txt`
- **GPU 检测失败**：日志可能出现 NVML/torch 提示；框架会自动回落到 CPU，不影响批处理主流程
- **求解失败**：检查 JSON 参数（如 k/L/nx/t_span/bc_type），以及边界条件是否冲突
- **数值溢出/不稳定**：降低问题规模（nx/ny）、缩短 t1-t0 或改用更稳定算法（FEM）

