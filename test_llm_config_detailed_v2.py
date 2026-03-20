"""测试 LLM 配置 - 详细版本"""
import requests
import json

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("测试 LLM 配置 - 详细版本")
print("=" * 60)

# 测试 1：测试豆包连接（使用正确的 API Key）
print("\n1. 测试豆包连接（使用正确的 API Key）")
try:
    payload = {
        "model_name": "doubao",
        "api_key": "0dd4ec9c-9b5f-42d1-a705-a7e9bdea37ce",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model_id": "doubao-seed-1-8-251228"
    }
    print(f"   发送请求: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    resp = requests.post(f"{base_url}/llm/config/test", json=payload, timeout=30)
    print(f"✅ 测试连接 - 状态码: {resp.status_code}")
    result = resp.json()
    print(f"   完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    if result.get('code') == 200:
        print("   ✅ 连接测试成功！")
    else:
        print(f"   ❌ 连接测试失败: {result.get('message')}")
except Exception as e:
    print(f"❌ 测试连接失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 2：测试豆包连接（缺少 model_id）
print("\n2. 测试豆包连接（缺少 model_id）")
try:
    payload = {
        "model_name": "doubao",
        "api_key": "0dd4ec9c-9b5f-42d1-a705-a7e9bdea37ce",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3"
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

# 测试 3：测试豆包连接（空对象）
print("\n3. 测试豆包连接（空对象）")
try:
    payload = {}
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
