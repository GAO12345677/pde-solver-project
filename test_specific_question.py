"""测试具体题目解析"""
import requests
import json

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("测试具体题目解析")
print("=" * 60)

# 测试题目
test_question = "求解一维线性定常热传导方程，边界条件为两端固定温度0和100，区域长度为1，精度要求90%"

print(f"\n测试题目：\n{test_question}\n")

# 测试 1：解析题目
print("1. 测试题目解析")
try:
    payload = {
        "question": test_question,
        "model_name": "doubao"
    }
    resp = requests.post(f"{base_url}/api/parse_question", json=payload, timeout=30)
    print(f"✅ 题目解析 - 状态码: {resp.status_code}")
    result = resp.json()
    print(f"   完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    if result.get('code') == 0:
        data = result.get('data', {})
        parsed = data.get('parsed', {})
        print(f"   解析模式: {parsed.get('parser_mode')}")
        print(f"   物理参数: {json.dumps(parsed.get('physics_params', {}), indent=2, ensure_ascii=False)}")
        print(f"   领域需求: {json.dumps(parsed.get('domain_demand', {}), indent=2, ensure_ascii=False)}")
    else:
        print(f"   错误: {result.get('message')}")
except Exception as e:
    print(f"❌ 题目解析失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 2：自动求解
print("\n2. 测试自动求解")
try:
    payload = {
        "question": test_question,
        "parser_model": "doubao",
        "return_full_solution": False
    }
    resp = requests.post(f"{base_url}/api/auto_solve", json=payload, timeout=60)
    print(f"✅ 自动求解 - 状态码: {resp.status_code}")
    result = resp.json()
    print(f"   完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    if result.get('code') == 0:
        data = result.get('data', {})
        solve_info = data.get('solve_info', {})
        print(f"   算法: {solve_info.get('algorithm')}")
        print(f"   计算时间: {solve_info.get('elapsed_s')} 秒")
        print(f"   状态: {solve_info.get('status')}")
    else:
        print(f"   错误: {result.get('message')}")
except Exception as e:
    print(f"❌ 自动求解失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
