# API 使用指南

## 📋 概述

本文档详细说明了 PDE 求解器框架的所有 API 端点，包括请求格式、响应格式和错误处理。

## 🔗 基础信息

- **基础URL**: `http://127.0.0.1:8001`
- **数据格式**: JSON
- **字符编码**: UTF-8
- **认证**: 暂无（未来版本将添加）

## 📚 交互式文档

启动服务后，可以访问以下地址查看交互式 API 文档：

- **Swagger UI**: http://127.0.0.1:8001/docs
- **ReDoc**: http://127.0.0.1:8001/redoc

---

## 🎯 核心API端点

### 1. 特征提取

提取 PDE 问题的物理特征、硬件特征和领域需求特征。

#### 端点
```
POST /extract_feature
GET /extract_feature
```

#### 请求参数

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|--------|------|
| equation_type | string | 是 | 方程类型：`heat1d` 或 `poisson2d_nonlinear` |
| accuracy | string | 否 | 精度要求：`high`、`medium`、`low`，默认 `medium` |
| realtime | string | 否 | 实时性要求：`high`、`medium`、`low`，默认 `medium` |
| resource_budget | float | 否 | 资源预算：0.1-1.0，默认 0.75 |
| boundary_condition | string | 否 | 边界条件：`dirichlet`、`neumann`、`mixed`，默认 `dirichlet` |
| nx | int | 否 | X方向网格点数，默认 101 |
| ny | int | 否 | Y方向网格点数（仅2D），默认 41 |

#### 请求示例

```bash
curl -X POST http://127.0.0.1:8001/extract_feature \
  -H "Content-Type: application/json" \
  -d '{
    "equation_type": "heat1d",
    "accuracy": "medium",
    "realtime": "medium",
    "resource_budget": 0.75,
    "boundary_condition": "dirichlet",
    "nx": 101
  }'
```

#### 响应示例

```json
{
  "status": "ok",
  "success": true,
  "error": null,
  "data": {
    "equation_type": "heat1d",
    "physics": [0.0, 0.0, 1.0, 0.0, 0.5],
    "hardware": [0.0, 0.5, 0.5, 0.0, 1.0],
    "domain": [0.5, 0.5, 0.75],
    "x13": [0.0, 0.0, 1.0, 0.0, 0.5, 0.0, 0.5, 0.5, 0.0, 1.0, 0.5, 0.5, 0.75],
    "hardware_extra": {
      "gpu_name": "NVIDIA GeForce RTX 3080"
    }
  }
}
```

---

### 2. 算法选择

基于提取的特征，使用机器学习模型选择最优算法。

#### 端点
```
POST /select_algorithm
GET /select_algorithm
```

#### 请求参数

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|--------|------|
| strategy | string | 是 | 选择策略：`static_rf`、`static_xgb`、`dynamic_rl` |
| physics | array | 是 | 物理特征向量（5维） |
| hardware | array | 是 | 硬件特征向量（5维） |
| domain | array | 是 | 领域需求特征向量（3维） |

#### 请求示例

```bash
curl -X POST http://127.0.0.1:8001/select_algorithm \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "static_rf",
    "physics": [0.0, 0.0, 1.0, 0.0, 0.5],
    "hardware": [0.0, 0.5, 0.5, 0.0, 1.0],
    "domain": [0.5, 0.5, 0.75]
  }'
```

#### 响应示例

```json
{
  "status": "ok",
  "success": true,
  "error": null,
  "data": {
    "selected_algorithm": "fdm",
    "algorithm_scores": {
      "fdm": 0.85,
      "fem": 0.72,
      "spectral": 0.68
    },
    "rationale": "评分依据(代理)：精度权重=0.50、收敛/效率权重=0.30、资源权重=0.20；精度=0.75、收敛/效率=0.80、资源利用=0.85。"
  }
}
```

---

### 3. 方程求解

使用指定算法求解偏微分方程。

#### 端点
```
POST /solve_equation
GET /solve_equation
```

#### 请求参数

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|--------|------|
| equation_type | string | 是 | 方程类型：`heat1d` 或 `poisson2d_nonlinear` |
| algorithm_key | string | 是 | 算法：`fdm`、`fem`、`spectral` |
| k | float | 否 | 扩散系数，默认 1.0 |
| L | float | 否 | 区间长度，默认 1.0 |
| nx | int | 否 | X方向网格点数，默认 101 |
| ny | int | 否 | Y方向网格点数（仅2D），默认 41 |
| t0 | float | 否 | 起始时间，默认 0.0 |
| t1 | float | 否 | 结束时间，默认 0.1 |
| bc_type | string | 否 | 边界条件类型，默认 `dirichlet` |
| left_bc | float | 否 | 左边界值，默认 0.0 |
| right_bc | float | 否 | 右边界值，默认 0.0 |
| return_full_solution | bool | 否 | 是否返回完整解，默认 false |

#### 请求示例

```bash
curl -X POST http://127.0.0.1:8001/solve_equation \
  -H "Content-Type: application/json" \
  -d '{
    "equation_type": "heat1d",
    "algorithm_key": "fdm",
    "k": 1.0,
    "L": 1.0,
    "nx": 101,
    "t0": 0.0,
    "t1": 0.1,
    "bc_type": "dirichlet",
    "left_bc": 0.0,
    "right_bc": 0.0
  }'
```

#### 响应示例

```json
{
  "status": "ok",
  "success": true,
  "error": null,
  "data": {
    "solve_info": {
      "algorithm": "fdm",
      "elapsed_s": 0.0234,
      "nfev": 100,
      "status": "success",
      "estimated_error": 0.001234,
      "resource_proxy": 0.85
    },
    "validation": {
      "non_negative": true,
      "bounded": true,
      "smooth": true
    },
    "solution_preview": {
      "count": 101,
      "head": [0.0, 0.0012, 0.0023, ...],
      "tail": [0.0089, 0.0067, 0.0045, ...],
      "stats": {
        "min": 0.0,
        "max": 0.1234,
        "mean": 0.0567,
        "std": 0.0345
      }
    },
    "solution": [0.0, 0.0012, 0.0023, ...]
  }
}
```

---

### 4. 结果评估

评估求解结果并提供反馈优化。

#### 端点
```
POST /evaluate_result
GET /evaluate_result
```

#### 请求参数

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|--------|------|
| solution | array | 是 | 解向量 |
| solve_info | object | 是 | 求解信息 |
| accuracy | string | 是 | 精度要求：`high`、`medium`、`low` |
| realtime | string | 是 | 实时性要求：`high`、`medium`、`low` |
| resource_budget | float | 是 | 资源预算：0.1-1.0 |
| validation | object | 否 | 验证信息 |
| x13 | array | 否 | 特征向量（用于反馈优化） |
| selected_algorithm | string | 否 | 选择的算法（用于反馈优化） |
| retrain_strategy | string | 否 | 重训练策略，默认 `static_rf` |

#### 请求示例

```bash
curl -X POST http://127.0.0.1:8001/evaluate_result \
  -H "Content-Type: application/json" \
  -d '{
    "solution": [0.0, 0.0012, 0.0023, ...],
    "solve_info": {
      "algorithm": "fdm",
      "elapsed_s": 0.0234,
      "nfev": 100,
      "status": "success"
    },
    "accuracy": "medium",
    "realtime": "medium",
    "resource_budget": 0.75
  }'
```

#### 响应示例

```json
{
  "status": "ok",
  "success": true,
  "error": null,
  "data": {
    "report": {
      "timestamp": 1234567890.123,
      "selected_algorithm": "fdm",
      "metrics": {
        "accuracy_score": 0.85,
        "speed_score": 0.90,
        "resource_score": 0.80,
        "robustness_score": 0.75
      },
      "pass_fail": {
        "accuracy": true,
        "speed": true,
        "resource": true,
        "robustness": true
      },
      "notes": [
        "精度要求满足",
        "速度表现良好",
        "资源使用合理"
      ],
      "context": {
        "equation_type": "heat1d",
        "problem_size": 101
      }
    },
    "saved_to": "result/report_1234567890.json",
    "optimizer": {
      "skipped": false,
      "feedback_saved_to": "result/feedback_samples.npz",
      "retrained": {
        "strategy": "static_rf",
        "num_samples": 241,
        "accuracy": 0.87
      }
    }
  }
}
```

---

### 5. 自然语言解析

将自然语言描述的 PDE 问题解析为结构化参数。

#### 端点
```
POST /api/parse_question
GET /api/parse_question
```

#### 请求参数

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|--------|------|
| question | string | 是 | 自然语言问题描述 |

#### 请求示例

```bash
curl -X POST http://127.0.0.1:8001/api/parse_question \
  -H "Content-Type: application/json" \
  -d '{
    "question": "求解1D热传导方程，扩散系数k=1.0，区间长度L=1.0，使用Dirichlet边界条件，左右边界温度为0，初始温度分布为sin(pi*x/L)"
  }'
```

#### 响应示例

```json
{
  "status": "ok",
  "success": true,
  "error": null,
  "data": {
    "message": "当前使用大模型智能解析（全局配置Key）。",
    "parsed": {
      "parser_mode": "baidu_llm",
      "physics_params": {
        "equation_type": "heat1d",
        "dimension": 1,
        "linear": true,
        "stationary": false,
        "boundary_condition": "dirichlet",
        "problem_size": 101
      },
      "domain_demand": {
        "accuracy": 0.9,
        "realtime": 0.8,
        "resource_budget": 0.7
      },
      "hardware_info": {
        "gpu_available": true,
        "cpu_cores": 8
      }
    },
    "key_configured": true
  }
}
```

---

### 6. 自动求解

完整的自然语言到求解的自动化流程。

#### 端点
```
POST /api/auto_solve
```

#### 请求参数

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|--------|------|
| question | string | 是 | 自然语言问题描述 |
| return_full_solution | bool | 否 | 是否返回完整解，默认 false |

#### 请求示例

```bash
curl -X POST http://127.0.0.1:8001/api/auto_solve \
  -H "Content-Type: application/json" \
  -d '{
    "question": "求解1D热传导方程，扩散系数k=1.0，区间长度L=1.0，使用Dirichlet边界条件",
    "return_full_solution": false
  }'
```

#### 响应示例

```json
{
  "status": "ok",
  "success": true,
  "error": null,
  "data": {
    "parsed": {
      "parser_mode": "baidu_llm",
      "physics_params": {
        "equation_type": "heat1d",
        "dimension": 1,
        "linear": true,
        "stationary": false,
        "boundary_condition": "dirichlet",
        "problem_size": 101
      },
      "domain_demand": {
        "accuracy": 0.9,
        "realtime": 0.8,
        "resource_budget": 0.7
      }
    },
    "features": {
      "equation_type": "heat1d",
      "physics": [0.0, 0.0, 1.0, 0.0, 0.5],
      "hardware": [0.0, 0.5, 0.5, 0.0, 1.0],
      "domain": [0.5, 0.5, 0.75],
      "x13": [0.0, 0.0, 1.0, 0.0, 0.5, 0.0, 0.5, 0.5, 0.0, 1.0, 0.5, 0.5, 0.75]
    },
    "algorithm_selection": {
      "selected_algorithm": "fdm",
      "algorithm_scores": {
        "fdm": 0.85,
        "fem": 0.72,
        "spectral": 0.68
      },
      "rationale": "评分依据(代理)：精度权重=0.50、收敛/效率权重=0.30、资源权重=0.20"
    },
    "solution": {
      "solve_info": {
        "algorithm": "fdm",
        "elapsed_s": 0.0234,
        "nfev": 100,
        "status": "success"
      },
      "solution_preview": {
        "count": 101,
        "head": [0.0, 0.0012, 0.0023, ...],
        "tail": [0.0089, 0.0067, 0.0045, ...],
        "stats": {
          "min": 0.0,
          "max": 0.1234,
          "mean": 0.0567,
          "std": 0.0345
        }
      }
    }
  }
}
```

---

### 7. LLM 配置管理

管理大语言模型的配置。

#### 7.1 获取配置

```
GET /llm/config/get
```

#### 响应示例

```json
{
  "code": 200,
  "data": {
    "openai": {
      "api_key": "",
      "base_url": "https://api.openai.com/v1"
    },
    "gemini": {
      "api_key": "sk-xxxxx",
      "base_url": "https://generativelanguage.googleapis.com/v1beta"
    }
  }
}
```

#### 7.2 保存配置

```
POST /llm/config/save
```

#### 请求参数

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|--------|------|
| model_name | string | 是 | 模型名称：`openai`、`gemini`、`qwen`、`deepseek`、`doubao`、`qianfan` |
| api_key | string | 是 | API 密钥 |
| base_url | string | 否 | 自定义 Base URL |

#### 7.3 测试连接

```
POST /llm/config/test
```

#### 请求参数

与保存配置相同。

#### 响应示例

成功：
```json
{
  "code": 200,
  "message": "测试成功"
}
```

失败：
```json
{
  "code": 500,
  "message": "连接超时"
}
```

#### 7.4 获取额度

```
GET /llm/quota/get
```

#### 响应示例

```json
{
  "code": 200,
  "data": [
    {
      "model_name": "gemini",
      "provider": "Google",
      "total_quota": 10000.0,
      "remaining_quota": 9900.0,
      "status": "normal",
      "update_time": "2026-03-19 10:30",
      "message": "额度充足"
    }
  ]
}
```

---

### 8. WebSocket 实时求解

通过 WebSocket 获取实时求解进度。

#### 端点
```
WS /ws/solve/{task_id}
```

#### 消息格式

##### 客户端发送

```json
{
  "action": "solve",
  "params": {
    "equation_type": "heat1d",
    "algorithm_key": "fdm",
    ...
  }
}
```

或

```json
{
  "action": "cancel"
}
```

##### 服务端推送

**进度消息**:
```json
{
  "type": "progress",
  "task_id": "task_1234567890",
  "progress": 0.5,
  "message": "正在求解...",
  "status": "running",
  "timestamp": 1234567890.123
}
```

**完成消息**:
```json
{
  "type": "complete",
  "task_id": "task_1234567890",
  "result": {
    "solve_info": {...},
    "solution_preview": {...}
  },
  "timestamp": 1234567890.456
}
```

**错误消息**:
```json
{
  "type": "error",
  "task_id": "task_1234567890",
  "error": "求解失败：参数错误",
  "timestamp": 1234567890.789
}
```

---

### 9. 健康检查

检查服务状态。

#### 端点
```
GET /health
```

#### 响应示例

```json
{
  "status": "ok"
}
```

---

## ⚠️ 错误处理

### 标准错误响应格式

```json
{
  "status": "error",
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {}
  },
  "data": null
}
```

### 常见错误码

| 错误码 | 说明 | HTTP状态码 |
|--------|------|------------|
| VALIDATION_ERROR | 参数验证失败 | 400 |
| FEATURE_EXTRACTION_ERROR | 特征提取失败 | 500 |
| ALGORITHM_SELECTION_ERROR | 算法选择失败 | 500 |
| SOLVER_ERROR | 求解器错误 | 500 |
| LLM_CONFIG_ERROR | LLM配置错误 | 500 |
| LLM_CONNECTION_ERROR | LLM连接失败 | 503 |
| RESOURCE_NOT_FOUND | 资源未找到 | 404 |
| CONFIGURATION_ERROR | 配置错误 | 500 |

---

## 📝 使用建议

1. **优先使用 WebSocket**: 对于耗时较长的求解任务，建议使用 WebSocket 获取实时进度
2. **合理设置参数**: 根据问题复杂度调整网格点数和时间步长
3. **利用自动求解**: 对于自然语言描述的问题，使用 `/api/auto_solve` 端点
4. **监控资源使用**: 关注 `resource_budget` 参数，避免资源耗尽
5. **错误重试**: 对于网络相关的错误，建议实现指数退避重试机制

---

## 🔗 相关文档

- [快速开始指南](./QUICKSTART.md)
- [改进方案](./IMPROVEMENT_PLAN.md)
- [Swagger UI](http://127.0.0.1:8001/docs)
- [ReDoc](http://127.0.0.1:8001/redoc)
