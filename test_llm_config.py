"""测试 LLM 配置"""
import requests
import json

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("测试 LLM 配置")
print("=" * 60)

# 测试 1：获取配置
print("\n1. 测试获取配置")
try:
    resp = requests.get(f"{base_url}/llm/config/get")
    print(f"✅ 获取配置 - 状态码: {resp.status_code}")
    result = resp.json()
    print(f"   完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"❌ 获取配置失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 2：测试连接
print("\n2. 测试豆包连接")
try:
    payload = {
        "model_name": "doubao",
        "api_key": "test_key",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model_id": "doubao-seed-1-8-251228"
    }
    print(f"   发送请求: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    resp = requests.post(f"{base_url}/llm/config/test", json=payload, timeout=30)
    print(f"✅ 测试连接 - 状态码: {resp.status_code}")
    result = resp.json()
    print(f"   完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"❌ 测试连接失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
