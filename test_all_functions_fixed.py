"""测试系统所有功能（修复后）"""
import requests
import json

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("测试系统所有功能（修复后）")
print("=" * 60)

# 1. 测试健康检查
print("\n1. 测试健康检查")
try:
    resp = requests.get(f"{base_url}/health", timeout=5)
    print(f"✅ 健康检查 - 状态码: {resp.status_code}")
    print(f"   响应: {resp.json()}")
except Exception as e:
    print(f"❌ 健康检查失败: {e}")

# 2. 测试根路径
print("\n2. 测试根路径")
try:
    resp = requests.get(f"{base_url}/", timeout=5)
    print(f"✅ 根路径 - 状态码: {resp.status_code}")
    print(f"   响应: {resp.json()}")
except Exception as e:
    print(f"❌ 根路径失败: {e}")

# 3. 测试 LLM 管理页面
print("\n3. 测试 LLM 管理页面")
try:
    resp = requests.get(f"{base_url}/llm/admin", timeout=5)
    print(f"✅ LLM 管理页面 - 状态码: {resp.status_code}")
except Exception as e:
    print(f"❌ LLM 管理页面失败: {e}")

# 4. 测试获取配置
print("\n4. 测试获取配置")
try:
    resp = requests.get(f"{base_url}/llm/config/get", timeout=5)
    print(f"✅ 获取配置 - 状态码: {resp.status_code}")
    config = resp.json()
    print(f"   配置数量: {len(config.get('data', {}))}")
except Exception as e:
    print(f"❌ 获取配置失败: {e}")

# 5. 测试豆包连接
print("\n5. 测试豆包连接")
payload = {
    "model_name": "doubao",
    "api_key": "0dd4ec9c-9b5f-42d1-a705-a7e9bdea37ce",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model_id": "doubao-seed-1-8-251228"
}
try:
    resp = requests.post(f"{base_url}/llm/config/test", json=payload, timeout=30)
    print(f"✅ 豆包连接 - 状态码: {resp.status_code}")
    print(f"   响应: {resp.json()}")
except Exception as e:
    print(f"❌ 豆包连接失败: {e}")

# 6. 测试 1D 热传导方程求解
print("\n6. 测试 1D 热传导方程求解")
payload = {
    "equation_type": "heat1d",
    "algorithm_key": "fdm",
    "precision_requirement": "medium",
    "realtime_requirement": "medium",
    "resource_budget": 0.75,
    "boundary_condition": "dirichlet",
    "nx": 101,
    "k": 1.0
}
try:
    resp = requests.post(f"{base_url}/solve_equation", json=payload, timeout=30)
    print(f"✅ 1D 热传导方程求解 - 状态码: {resp.status_code}")
    result = resp.json()
    if result.get('success'):
        data = result.get('data', {})
        solve_info = data.get('solve_info', {})
        print(f"   算法: {solve_info.get('algorithm')}")
        print(f"   计算时间: {solve_info.get('elapsed_s')} 秒")
        print(f"   数据点数: {data.get('solution_preview', {}).get('count', 0)}")
    else:
        print(f"   错误: {result.get('error')}")
except Exception as e:
    print(f"❌ 1D 热传导方程求解失败: {e}")

# 7. 测试 2D 非线性 Poisson 方程求解
print("\n7. 测试 2D 非线性 Poisson 方程求解")
payload = {
    "equation_type": "poisson2d_nonlinear",
    "algorithm_key": "fdm",
    "precision_requirement": "medium",
    "realtime_requirement": "medium",
    "resource_budget": 0.75,
    "boundary_condition": "dirichlet",
    "nx": 51,
    "ny": 51
}
try:
    resp = requests.post(f"{base_url}/solve_equation", json=payload, timeout=30)
    print(f"✅ 2D 非线性 Poisson 方程求解 - 状态码: {resp.status_code}")
    result = resp.json()
    if result.get('success'):
        data = result.get('data', {})
        solve_info = data.get('solve_info', {})
        print(f"   算法: {solve_info.get('algorithm')}")
        print(f"   计算时间: {solve_info.get('elapsed_s')} 秒")
        print(f"   数据点数: {data.get('solution_preview', {}).get('count', 0)}")
    else:
        print(f"   错误: {result.get('error')}")
except Exception as e:
    print(f"❌ 2D 非线性 Poisson 方程求解失败: {e}")

# 8. 测试获取额度
print("\n8. 测试获取额度")
try:
    resp = requests.get(f"{base_url}/llm/quota/get", timeout=5)
    print(f"✅ 获取额度 - 状态码: {resp.status_code}")
    quota = resp.json()
    print(f"   响应: {quota}")
except Exception as e:
    print(f"❌ 获取额度失败: {e}")

# 9. 测试 API 文档
print("\n9. 测试 API 文档")
try:
    resp = requests.get(f"{base_url}/docs", timeout=5)
    print(f"✅ API 文档 - 状态码: {resp.status_code}")
except Exception as e:
    print(f"❌ API 文档失败: {e}")

# 10. 测试 React 前端
print("\n10. 测试 React 前端")
try:
    resp = requests.get(f"{base_url}/app", timeout=5)
    print(f"✅ React 前端 - 状态码: {resp.status_code}")
except Exception as e:
    print(f"❌ React 前端失败: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
