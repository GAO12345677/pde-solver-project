## 百度文心一言（千帆 Qianfan）接入指南（ERNIE-Speed-8K）

本项目已支持 **“自然语言题目 → 结构化 JSON → 特征提取 → 算法推荐 → 求解 → 评估”** 的一键流程：
- 解析接口：`/api/parse_question`
- 一键解题：`/api/auto_solve`

---

### 1) 申请 API Key / Secret Key（千帆平台）

在“百度智能云 · 文心千帆平台”创建应用并获取：
- **API Key**
- **Secret Key**

---

### 2) 配置环境变量（推荐方式，最安全）

在 PowerShell 中（临时生效）：

```powershell
$env:BAIDU_QIANFAN_API_KEY="你的APIKey"
$env:BAIDU_QIANFAN_SECRET_KEY="你的SecretKey"
```

可选环境变量：
- `BAIDU_QIANFAN_MODEL`：默认 `ERNIE-Speed-8K`
- `BAIDU_QIANFAN_TIMEOUT_S`：默认 `10`（解析超时 10 秒，超时自动降级）

---

### 3) 安装依赖与启动服务

```bash
pip install -r requirements.txt
python main.py
```

启动后打开：
- Swagger：`http://127.0.0.1:8001/docs`
- Redoc：`http://127.0.0.1:8001/redoc`

---

### 4) 在线调试（小白用法）

#### 仅解析题目（不求解）

在 Swagger 中调用 `POST /api/parse_question`：

```json
{ "question": "我要算一个一维的线性定常热传导方程，精度要求90%，别太耗资源" }
```

#### 一键解题（全流程）

在 Swagger 中调用 `POST /api/auto_solve`：

```json
{ "question": "求解2维非线性非定常泊松方程，要算得快一点，精度不用太高" }
```

返回会包含每一步的结果：`parsed / extracted / selected / solved / evaluated`。

---

### 5) 常见异常与排查

- **提示“百度API未配置，已降级为规则解析”**
  - 说明你没有设置环境变量 Key/Secret；系统会自动降级，不会崩溃。
- **Key 错误/权限不足**
  - 请检查 `BAIDU_QIANFAN_API_KEY` 与 `BAIDU_QIANFAN_SECRET_KEY` 是否正确、是否对应同一应用。
- **JSON 解析失败**
  - 服务端已做 “去除 ```json/解释文字/多余字符” 的清洗，并会自动降级为规则解析。
  - 若仍失败，请将返回的 `error.details` 发我，我可以继续增强清洗策略。
- **硬件检测失败**
  - GPU 检测失败会回落 CPU，不影响主流程；检查 torch/NVIDIA 驱动/NVML。

---

### 6) 免费额度说明

平台通常提供一定的免费额度（如个人每月约 **500 万 Tokens**，以平台实际说明为准）。

