"""重新测试 LLM 路由"""
import requests

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("测试 LLM 路由")
print("=" * 60)

# 测试 GET /llm/config/get
print("\n1. GET /llm/config/get")
try:
    resp = requests.get(f"{base_url}/llm/config/get", timeout=30)
    print(f"   状态码: {resp.status_code}")
    if resp.status_code == 200:
        print(f"   响应: {resp.text[:200]}...")
    else:
        print(f"   响应: {resp.text}")
except Exception as e:
    print(f"   错误: {e}")

# 测试 POST /llm/config/test
print("\n2. POST /llm/config/test")
payload = {
    "model_name": "doubao",
    "api_key": "0dd4ec9c-9b5f-42d1-a705-a7e9bdea37ce",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model_id": "doubao-seed-1-8-251228"
}
try:
    resp = requests.post(f"{base_url}/llm/config/test", json=payload, timeout=30)
    print(f"   状态码: {resp.status_code}")
    if resp.status_code == 200:
        print(f"   响应: {resp.text[:200]}...")
    else:
        print(f"   响应: {resp.text}")
except Exception as e:
    print(f"   错误: {e}")

# 测试 GET /llm/quota/get
print("\n3. GET /llm/quota/get")
try:
    resp = requests.get(f"{base_url}/llm/quota/get", timeout=30)
    print(f"   状态码: {resp.status_code}")
    if resp.status_code == 200:
        print(f"   响应: {resp.text[:200]}...")
    else:
        print(f"   响应: {resp.text}")
except Exception as e:
    print(f"   错误: {e}")
