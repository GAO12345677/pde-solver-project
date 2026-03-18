# LLM 模型配置与额度监控前端集成说明

本目录 (`llm_admin_frontend`) 包含了纯 HTML/CSS/JS 编写的 LLM 模型配置与额度监控前端界面。

## 文件结构
- `index.html`: 页面主结构
- `style.css`: 样式文件，采用响应式卡片布局，统一的视觉风格
- `app.js`: 核心交互逻辑，包含接口调用、表单校验、本地缓存、DOM 渲染等

## 接入现有 FastAPI 项目的方法

由于前端是纯静态文件，您可以通过 FastAPI 的静态文件挂载功能或直接返回 HTML 字符串的方式将其集成到现有项目中。

### 方法一：使用 `StaticFiles` 挂载（推荐）

1. 将 `llm_admin_frontend` 文件夹移动到您的 FastAPI 项目根目录下（例如重命名为 `static/llm_admin`）。
2. 在 `api/routes.py` 或 `main.py` 中挂载静态目录：

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# 挂载静态文件目录
app.mount("/llm_admin_static", StaticFiles(directory="static/llm_admin"), name="llm_admin_static")

# 添加路由返回 index.html
@app.get("/llm/admin", response_class=HTMLResponse)
async def llm_admin_page():
    return FileResponse("static/llm_admin/index.html")
```

### 方法二：直接通过 HTMLResponse 返回

如果您不想挂载静态目录，可以将 `style.css` 和 `app.js` 的内容直接内联到 `index.html` 中，然后在路由中读取并返回：

```python
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import os

router = APIRouter()

@router.get("/llm/admin", response_class=HTMLResponse)
async def llm_admin_page():
    # 假设 index.html 包含了内联的 css 和 js
    html_path = os.path.join(os.path.dirname(__file__), "llm_admin_frontend", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)
```
*(注意：若采用此方法，请先将 `style.css` 放入 `<style>` 标签，将 `app.js` 放入 `<script>` 标签内)*

## 测试步骤

1. **启动后端服务**：确保 FastAPI 服务正常运行，并且 `/llm/config/save`、`/llm/config/test`、`/llm/config/get`、`/llm/quota/get` 接口可用。
2. **访问页面**：在浏览器中打开挂载的路由地址（如 `http://localhost:8000/llm/admin`）。
3. **测试表单校验**：在 OpenAI 的 API Key 输入框中输入 `123`，输入框应变红并提示 "通常以 sk- 开头"。
4. **测试本地缓存**：输入一个 API Key，刷新页面，该 Key 应该依然保留在输入框中。
5. **测试连接**：输入正确的 API Key 和 Base URL，点击「测试连接」，按钮应显示转圈动画，随后右上角弹出成功或失败的 Toast 提示。
6. **保存配置**：点击「保存配置」，成功后页面下方的额度监控区域应自动刷新。
7. **额度监控**：点击「刷新额度」，观察各个模型的额度卡片是否正确渲染，进度条颜色是否符合规则（>80%绿，50-80%黄，<50%橙，0%红）。
