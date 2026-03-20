"""测试豆包 API 连接（使用正确的参数）"""
import requests

# 你的配置
API_KEY = "0dd4ec9c-9b5f-42d1-a705-a7e9bdea37ce"
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
MODEL_NAME = "doubao-seed-1-8-251228"

# 使用正确的端点和格式
url = f"{BASE_URL}/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "model": MODEL_NAME,
    "messages": [
        {
            "role": "user",
            "content": "test"
        }
    ],
    "max_tokens": 10
}

print("=" * 60)
print("测试豆包 API 连接")
print("=" * 60)
print(f"URL: {url}")
print(f"Headers: {headers}")
print(f"Payload: {payload}")
print()

try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.text}")
    
    if resp.status_code == 200:
        print("\n✅ API 连接成功！")
    else:
        print(f"\n❌ API 连接失败，状态码: {resp.status_code}")
except Exception as e:
    print(f"\n❌ 错误: {e}")
