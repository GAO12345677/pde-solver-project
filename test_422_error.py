"""检查后端日志中的 422 错误"""
import requests
import json

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("检查后端日志中的 422 错误")
print("=" * 60)

# 测试 1：发送正确的请求
print("\n测试 1：发送正确的请求")
payload = {
    "model_name": "doubao",
    "api_key": "0dd4ec9c-9b5f-42d1-a705-a7e9bdea37ce",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model_id": "doubao-seed-1-8-251228"
}

try:
    resp = requests.post(f"{base_url}/llm/config/test", json=payload, timeout=30)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.text}")
except Exception as e:
    print(f"❌ 错误: {e}")

# 测试 2：发送缺少 api_key 的请求
print("\n测试 2：发送缺少 api_key 的请求")
payload = {
    "model_name": "doubao",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model_id": "doubao-seed-1-8-251228"
}

try:
    resp = requests.post(f"{base_url}/llm/config/test", json=payload, timeout=30)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.text}")
except Exception as e:
    print(f"❌ 错误: {e}")

# 测试 3：发送缺少 model_name 的请求
print("\n测试 3：发送缺少 model_name 的请求")
payload = {
    "api_key": "0dd4ec9c-9b5f-42d1-a705-a7e9bdea37ce",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model_id": "doubao-seed-1-8-251228"
}

try:
    resp = requests.post(f"{base_url}/llm/config/test", json=payload, timeout=30)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.text}")
except Exception as e:
    print(f"❌ 错误: {e}")

# 测试 4：发送 api_key 为空字符串的请求
print("\n测试 4：发送 api_key 为空字符串的请求")
payload = {
    "model_name": "doubao",
    "api_key": "",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model_id": "doubao-seed-1-8-251228"
}

try:
    resp = requests.post(f"{base_url}/llm/config/test", json=payload, timeout=30)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.text}")
except Exception as e:
    print(f"❌ 错误: {e}")
