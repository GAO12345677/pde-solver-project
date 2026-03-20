"""检查求解 API 的返回格式"""
import requests
import json

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("检查求解 API 的返回格式")
print("=" * 60)

# 测试 1D 热传导方程求解
print("\n1. 测试 1D 热传导方程求解")
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
    print(f"状态码: {resp.status_code}")
    result = resp.json()
    print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"❌ 错误: {e}")

# 测试 2D Poisson 方程求解
print("\n2. 测试 2D Poisson 方程求解")
payload = {
    "equation_type": "poisson2d",
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
    print(f"状态码: {resp.status_code}")
    result = resp.json()
    print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"❌ 错误: {e}")
