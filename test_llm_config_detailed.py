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
    # 这里需要用户输入正确的 API Key
    api_key = input("请输入火山方舟 API Key（按 Enter 跳过）: ").strip()
    if not api_key:
        print("   跳过此测试")
    else:
        payload = {
            "model_name": "doubao",
            "api_key": api_key,
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

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
