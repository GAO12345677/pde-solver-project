# PDE 求解器项目使用教程

## 1. 项目简介

本项目是一个面向偏微分方程问题的实验型求解平台，包含：

- PDE 参数化求解
- 特征提取与算法选择
- 自然语言题目解析
- 基于大模型的 PDE 题目自动求解
- Web 页面演示与 Swagger API 调试

当前项目适合演示和课程汇报，不适合作为通用物理题求解器。

## 2. 运行环境

建议环境：

- Windows 10/11
- Python 3.10+
- Node.js 18+

本项目当前默认后端地址：

- 后端：`http://127.0.0.1:8001`
- 前端挂载页：`http://127.0.0.1:8001/app/`
- Swagger：`http://127.0.0.1:8001/docs`

## 3. 第一次运行

### 3.1 安装 Python 依赖

在项目根目录运行：

```powershell
pip install -r requirements.txt
```

如果你使用虚拟环境，也可以先激活虚拟环境后再安装。

### 3.2 安装前端依赖

在项目根目录运行：

```powershell
cd static
npm install
cd ..
```

### 3.3 构建前端

在项目根目录运行：

```powershell
cd static
npm run build
cd ..
```

这一步会生成 `static/dist`，后端启动后会自动挂载到 `/app/`。

## 4. 启动项目

在项目根目录运行：

```powershell
python main.py
```

如果你使用项目自带虚拟环境：

```powershell
.\.venv\Scripts\python main.py
```

启动成功后可访问：

- 主界面：[http://127.0.0.1:8001/app/](http://127.0.0.1:8001/app/)
- API 文档：[http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- 健康检查：[http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)

## 5. 页面功能说明

### 5.1 首页

用于进入不同功能页面。

### 5.2 题目解析

路径：

- [http://127.0.0.1:8001/app/#question](http://127.0.0.1:8001/app/#question)

功能：

- 输入自然语言 PDE 题目
- 调用大模型将题目解析成结构化 JSON
- 支持“解析题目”和“自动求解”

注意：

- 这里只适合 PDE 题目
- 普通力学题、运动学题、牛顿定律题不属于本系统支持范围

推荐测试题目：

```text
求解一维热传导方程 u_t = k * u_xx，在区间 [0,1] 上，边界条件 u(0,t)=u(1,t)=0，初始条件 u(x,0)=sin(pi x)
```

### 5.3 求解

路径：

- [http://127.0.0.1:8001/app/#solve](http://127.0.0.1:8001/app/#solve)

功能：

- 手动设置 PDE 参数
- 选择算法
- 执行数值求解
- 查看求解统计结果

这是参数化 PDE 求解页面，不依赖大模型题目理解。

### 5.4 LLM 配置

路径：

- [http://127.0.0.1:8001/app/#llm](http://127.0.0.1:8001/app/#llm)

功能：

- 配置豆包、OpenAI、Qwen、Gemini 等模型
- 测试连接
- 保存配置

如果老师只看演示，建议优先配置豆包。

## 6. 豆包配置说明

进入“LLM 配置”页面后：

1. 选择 `豆包 (Doubao)`
2. 填写 `API Key`
3. 填写 `模型名称 / model_id`
4. 点击“测试连接”
5. 点击“保存配置”

推荐模型名称示例：

```text
doubao-seed-1-8-251228
```

说明：

- “解析题目”成功不代表所有题都能自动求解
- 当前自动求解器只支持 PDE 题目

## 7. 推荐演示流程

如果你给老师现场展示，建议按这个顺序：

### 方案 A：最稳妥

1. 启动项目
2. 打开 [http://127.0.0.1:8001/app/](http://127.0.0.1:8001/app/)
3. 进入“LLM 配置”，展示豆包已连接
4. 进入“题目解析”，输入一维热传导方程测试题
5. 先点“解析题目”
6. 再点“自动求解”
7. 最后进入“求解”页演示手动参数求解

### 方案 B：只做 API 演示

1. 打开 [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
2. 演示 `/api/parse_question`
3. 演示 `/api/auto_solve`
4. 演示 `/solve_equation`

这种方式最适合老师重点看接口设计和系统流程。

## 8. 重要限制说明

当前系统主要支持：

- 一维热传导方程
- 二维非线性 Poisson 方程

当前不建议输入：

- 普通受力分析题
- 高中物理运动学题
- 非 PDE 类自然语言题

如果输入非 PDE 题，系统可能返回“当前自动求解器不支持”之类提示，这是预期行为。

## 9. 常用接口

### 9.1 解析题目

```bash
curl -X POST http://127.0.0.1:8001/api/parse_question ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"求解一维热传导方程 u_t = k * u_xx，在区间 [0,1] 上，边界条件 u(0,t)=u(1,t)=0，初始条件 u(x,0)=sin(pi x)\",\"model_name\":\"doubao\"}"
```

### 9.2 自动求解

```bash
curl -X POST http://127.0.0.1:8001/api/auto_solve ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"求解一维热传导方程 u_t = k * u_xx，在区间 [0,1] 上，边界条件 u(0,t)=u(1,t)=0，初始条件 u(x,0)=sin(pi x)\",\"parser_model\":\"doubao\",\"return_full_solution\":false}"
```

### 9.3 参数化求解

```bash
curl -X POST http://127.0.0.1:8001/solve_equation ^
  -H "Content-Type: application/json" ^
  -d "{\"equation_type\":\"heat1d\",\"algorithm_key\":\"fdm\",\"k\":1.0,\"L\":1.0,\"nx\":101,\"t0\":0.0,\"t1\":0.1,\"bc_type\":\"dirichlet\",\"left_bc\":0.0,\"right_bc\":0.0}"
```

## 10. 常见问题

### 10.1 页面白屏

先确认已经执行过：

```powershell
cd static
npm run build
cd ..
```

然后重启后端。

### 10.2 自动求解失败

先检查：

- 输入是否为 PDE 题
- 豆包配置是否测试通过
- 后端是否已重启到最新代码

### 10.3 LLM 返回规则解析

这通常说明：

- 当前大模型连接失败或超时
- 题目不适合当前 PDE 求解器
- 输入不是 PDE 类型题目

## 11. 建议老师查看的内容

如果老师时间有限，建议重点查看：

- Web 演示页面
- Swagger 文档
- `api/routes.py`
- `algorithm/selector.py`
- `feature/extractor.py`
- `solver/numerical_solver.py`

## 12. 结语

本项目适合作为“PDE 自动求解与算法选择框架”的课程/毕业设计演示版本。  
如果用于正式答辩，建议重点突出：

- 系统流程完整
- 具备前后端界面
- 支持 LLM 接入
- 支持结构化解析、算法选择和数值求解闭环
