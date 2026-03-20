# PDE Solver Project

一个用于课程项目演示的 PDE 求解框架，包含参数化求解、特征提取、算法选择、自然语言题目解析，以及基于大模型的 PDE 自动求解流程。

## 项目亮点

- 支持一维热传导方程与二维非线性 Poisson 方程
- 提供前后端一体化 Web 演示页面
- 支持自然语言题目解析
- 支持豆包等大模型接入
- 提供 Swagger API 文档，便于演示和调试
- 包含算法选择、数值求解、结果评估的完整闭环

## 主要功能

- `参数化求解`
  通过表单直接设置 PDE 参数，执行数值求解。

- `题目解析`
  输入自然语言 PDE 题目，解析为结构化 JSON。

- `自动求解`
  从自然语言题目出发，完成解析、特征提取、算法选择、求解和评估。

- `LLM 配置`
  支持配置豆包、OpenAI、Qwen、Gemini 等模型。

## 技术结构

- 后端：FastAPI
- 前端：React + Vite
- 数值求解：Python
- 模型选择：规则与机器学习结合
- 大模型接入：Doubao / OpenAI / Qwen / Gemini / Qianfan

## 快速开始

### 1. 安装依赖

后端：

```powershell
pip install -r requirements.txt
```

前端：

```powershell
cd static
npm install
npm run build
cd ..
```

### 2. 启动项目

```powershell
python main.py
```

如果你使用项目自带虚拟环境：

```powershell
.\.venv\Scripts\python main.py
```

### 3. 打开页面

- Web 页面：[http://127.0.0.1:8001/app/](http://127.0.0.1:8001/app/)
- Swagger 文档：[http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- 健康检查：[http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)

## 推荐演示题目

```text
求解一维热传导方程 u_t = k * u_xx，在区间 [0,1] 上，边界条件 u(0,t)=u(1,t)=0，初始条件 u(x,0)=sin(pi x)
```

## 注意事项

- 当前项目适合课程展示与系统演示
- 当前自动求解器主要支持 PDE 题目
- 普通力学题、运动学题、非 PDE 题目不在当前自动求解范围内

## 文档

- 使用教程：[QUICKSTART.md](/D:/cursorku/QUICKSTART.md)
- API 文档说明：[docs/API_GUIDE.md](/D:/cursorku/docs/API_GUIDE.md)
- 提交建议：[SUBMISSION_GUIDE.md](/D:/cursorku/SUBMISSION_GUIDE.md)

## 项目展示建议

如果用于课程汇报，建议按以下顺序演示：

1. 展示 Web 首页与功能导航
2. 在 LLM 配置页展示豆包配置
3. 在题目解析页演示自然语言解析
4. 在自动求解页展示完整闭环
5. 在 Swagger 中展示接口设计

## License

仅用于课程项目展示与学习交流。
