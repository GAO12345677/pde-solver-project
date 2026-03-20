"""测试 FastAPI 路由"""
import requests

# 测试 FastAPI 根路径
url = "http://127.0.0.1:8001"

print("=" * 60)
print("测试 FastAPI 路由")
print("=" * 60)

# 测试根路径
try:
    resp = requests.get(f"{url}/", timeout=30)
    print(f"GET / - 状态码: {resp.status_code}")
except Exception as e:
    print(f"GET / - 错误: {e}")

# 测试健康检查
try:
    resp = requests.get(f"{url}/health", timeout=30)
    print(f"GET /health - 状态码: {resp.status_code}")
except Exception as e:
    print(f"GET /health - 错误: {e}")

# 测试 LLM 配置获取
try:
    resp = requests.get(f"{url}/llm/config/get", timeout=30)
    print(f"GET /llm/config/get - 状态码: {resp.status_code}")
except Exception as e:
    print(f"GET /llm/config/get - 错误: {e}")

# 测试 LLM 配置测试（POST）
try:
    payload = {
        "model_name": "doubao",
        "api_key": "test",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model_id": "doubao-seed-1-8-251228"
    }
    resp = requests.post(f"{url}/llm/config/test", json=payload, timeout=30)
    print(f"POST /llm/config/test - 状态码: {resp.status_code}")
    if resp.status_code != 200:
        print(f"响应: {resp.text}")
except Exception as e:
    print(f"POST /llm/config/test - 错误: {e}")

print("\n" + "=" * 60)
print("访问 API 文档查看所有路由")
print("=" * 60)
print(f"Swagger UI: {url}/docs")
print(f"ReDoc: {url}/redoc")
