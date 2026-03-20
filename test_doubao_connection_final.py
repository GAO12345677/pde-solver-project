"""测试豆包 API 连接"""
import requests

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("测试豆包 API 连接")
print("=" * 60)

payload = {
    "model_name": "doubao",
    "api_key": "0dd4ec9c-9b5f-42d1-a705-a7e9bdea37ce",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model_id": "doubao-seed-1-8-251228"
}

print(f"Payload: {payload}")
print()

try:
    resp = requests.post(f"{base_url}/llm/config/test", json=payload, timeout=30)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.text}")
    
    if resp.status_code == 200:
        print("\n✅ 豆包 API 连接测试成功！")
    else:
        print(f"\n❌ 豆包 API 连接测试失败，状态码: {resp.status_code}")
except Exception as e:
    print(f"\n❌ 错误: {e}")
