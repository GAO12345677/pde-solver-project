"""检查 LLM 配置"""
import requests

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("检查 LLM 配置")
print("=" * 60)

# 检查 LLM 配置
print("\n1. 检查 LLM 配置")
try:
    resp = requests.get(f"{base_url}/llm/config/get")
    print(f"✅ 获取配置 - 状态码: {resp.status_code}")
    result = resp.json()
    if result.get('code') == 0:
        data = result.get('data', {})
        print(f"   配置数量: {len(data)}")
        for model_name, config in data.items():
            print(f"   模型: {model_name}")
            print(f"     API Key: {config.get('api_key', 'N/A')[:20]}...")
            print(f"     Base URL: {config.get('base_url', 'N/A')}")
            print(f"     Model ID: {config.get('model_id', 'N/A')}")
    else:
        print(f"   错误: {result.get('message')}")
except Exception as e:
    print(f"❌ 获取配置失败: {e}")

print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)
