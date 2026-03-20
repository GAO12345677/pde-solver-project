"""测试火山方舟 API 各种端点"""
import requests
import json

# 你的配置
API_KEY = "0dd4ec9c-9b5f-42d1-a705-a7e9bdea37ce"
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
MODEL_NAME = "doubao-seed-1-8-251228"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 测试各种可能的端点
endpoints = [
    "/responses",
    "/models",
    "/chat/completions",
    "/chat",
    "/completions",
    "/v1/chat/completions",
]

for endpoint in endpoints:
    print("=" * 60)
    print(f"测试端点: {endpoint}")
    print("=" * 60)
    
    url = f"{BASE_URL}{endpoint}"
    print(f"完整 URL: {url}")
    
    # 尝试不同的 payload
    payloads = [
        # Payload 1: 官方 responses 格式
        {
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
        },
        # Payload 2: OpenAI chat/completions 格式
        {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": "test"
                }
            ],
            "max_tokens": 10
        },
        # Payload 3: 简化格式
        {
            "model": MODEL_NAME,
            "prompt": "test"
        }
    ]
    
    for i, payload in enumerate(payloads, 1):
        print(f"\n尝试 Payload {i}:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"状态码: {resp.status_code}")
            if resp.status_code == 200:
                print(f"✅ 成功！响应: {resp.text[:200]}")
                break
            elif resp.status_code == 404:
                print(f"❌ 404 - 端点不存在")
            else:
                print(f"响应: {resp.text[:200]}")
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    print()
