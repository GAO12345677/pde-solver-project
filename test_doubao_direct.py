"""测试豆包 API 连接（直接调用豆包）"""
import requests

# 直接测试豆包 API
url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
headers = {
    "Authorization": "Bearer 0dd4ec9c-9b5f-42d1-a705-a7e9bdea37ce",
    "Content-Type": "application/json"
}
payload = {
    "model": "doubao-seed-1-8-251228",
    "messages": [
        {
            "role": "user",
            "content": "test"
        }
    ],
    "max_tokens": 10
}

print("=" * 60)
print("直接测试豆包 API")
print("=" * 60)
print(f"URL: {url}")
print(f"Headers: {headers}")
print(f"Payload: {payload}")
print()

try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.text[:200]}...")
    
    if resp.status_code == 200:
        print("\n✅ 豆包 API 连接成功！")
    else:
        print(f"\n❌ 豆包 API 连接失败，状态码: {resp.status_code}")
except Exception as e:
    print(f"\n❌ 错误: {e}")
