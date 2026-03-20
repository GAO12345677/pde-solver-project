"""测试火山方舟 API 连接"""
import requests

# 你的配置
API_KEY = "0dd4ec9c-9b5f-42d1-a705-a7e9bdea37ce"
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
MODEL_NAME = "doubao-seed-1-8-251228"

# 测试 1: 直接访问 responses 端点（官方示例）
print("=" * 60)
print("测试 1: 使用官方示例格式")
print("=" * 60)
url1 = f"{BASE_URL}/responses"
headers1 = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
payload1 = {
    "model": MODEL_NAME,
    "input": [
        {
            "role": "user",
            "content": [
                {
                        "type": "input_text",
                        "text": "test"
                    }
            ]
        }
    ]
}

print(f"URL: {url1}")
print(f"Headers: {headers1}")
print(f"Payload: {payload1}")

try:
    resp1 = requests.post(url1, headers=headers1, json=payload1, timeout=30)
    print(f"\n状态码: {resp1.status_code}")
    print(f"响应: {resp1.text}")
except Exception as e:
    print(f"\n错误: {e}")

# 测试 2: 访问 models 端点（获取模型列表）
print("\n" + "=" * 60)
print("测试 2: 获取模型列表")
print("=" * 60)
url2 = f"{BASE_URL}/models"
headers2 = {
    "Authorization": f"Bearer {API_KEY}"
}

print(f"URL: {url2}")

try:
    resp2 = requests.get(url2, headers=headers2, timeout=30)
    print(f"\n状态码: {resp2.status_code}")
    print(f"响应: {resp2.text}")
except Exception as e:
    print(f"\n错误: {e}")

# 测试 3: 不带 Bearer 前缀
print("\n" + "=" * 60)
print("测试 3: 不带 Bearer 前缀")
print("=" * 60)
url3 = f"{BASE_URL}/responses"
headers3 = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}

print(f"URL: {url3}")
print(f"Headers: {headers3}")

try:
    resp3 = requests.post(url3, headers=headers3, json=payload1, timeout=30)
    print(f"\n状态码: {resp3.status_code}")
    print(f"响应: {resp3.text}")
except Exception as e:
    print(f"\n错误: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
