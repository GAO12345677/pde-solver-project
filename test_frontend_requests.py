"""测试前端发送的请求"""
import requests
import json

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("测试前端发送的请求")
print("=" * 60)

# 测试 1：模拟前端发送的请求（可能包含空字符串）
print("\n测试 1：模拟前端发送的请求（可能包含空字符串）")
payload1 = {
    "model_name": "doubao",
    "api_key": "0dd4ec9c-9b5f-42d1-a705-a7e9bdea37ce",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model_id": "doubao-seed-1-8-251228"
}

try:
    resp = requests.post(f"{base_url}/llm/config/test", json=payload1, timeout=30)
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print(f"响应: {resp.text}")
    else:
        print("✅ 成功")
except Exception as e:
    print(f"❌ 错误: {e}")

# 测试 2：测试缺少 model_id 的情况
print("\n测试 2：测试缺少 model_id 的情况")
payload2 = {
    "model_name": "doubao",
    "api_key": "0dd4ec9c-9b5f-42d1-a705-a7e9bdea37ce",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3"
}

try:
    resp = requests.post(f"{base_url}/llm/config/test", json=payload2, timeout=30)
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print(f"响应: {resp.text}")
    else:
        print("✅ 成功")
except Exception as e:
    print(f"❌ 错误: {e}")

# 测试 3：测试 api_key 为空字符串的情况
print("\n测试 3：测试 api_key 为空字符串的情况")
payload3 = {
    "model_name": "doubao",
    "api_key": "",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model_id": "doubao-seed-1-8-251228"
}

try:
    resp = requests.post(f"{base_url}/llm/config/test", json=payload3, timeout=30)
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print(f"响应: {resp.text}")
    else:
        print("✅ 成功")
except Exception as e:
    print(f"❌ 错误: {e}")

# 测试 4：测试发送空 JSON 的情况
print("\n测试 4：测试发送空 JSON 的情况")
payload4 = {}

try:
    resp = requests.post(f"{base_url}/llm/config/test", json=payload4, timeout=30)
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print(f"响应: {resp.text}")
    else:
        print("✅ 成功")
except Exception as e:
    print(f"❌ 错误: {e}")
