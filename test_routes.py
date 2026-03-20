"""测试后端路由"""
import requests

# 测试 OPTIONS 请求
url = "http://127.0.0.1:8001/llm/config/test"
headers = {
    "Content-Type": "application/json",
    "Origin": "http://127.0.0.1:8001"
}

print("=" * 60)
print("测试 OPTIONS 请求")
print("=" * 60)
print(f"URL: {url}")
print(f"Method: OPTIONS")
print()

try:
    resp = requests.options(url, headers=headers, timeout=30)
    print(f"状态码: {resp.status_code}")
    print(f"响应头: {dict(resp.headers)}")
    print(f"响应: {resp.text[:200]}...")
except Exception as e:
    print(f"\n❌ 错误: {e}")

print("\n" + "=" * 60)
print("测试 POST 请求")
print("=" * 60)

payload = {
    "model_name": "doubao",
    "api_key": "0dd4ec9c-9b5f-42d1-a705-a7e9bdea37ce",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model_id": "doubao-seed-1-8-251228"
}

try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.text[:200]}...")
except Exception as e:
    print(f"\n❌ 错误: {e}")
