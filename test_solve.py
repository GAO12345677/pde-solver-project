"""测试 PDE 求解功能"""
import requests

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("测试 PDE 求解功能")
print("=" * 60)

# 测试 1D 热传导方程求解
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

print(f"Payload: {payload}")
print()

try:
    resp = requests.post(f"{base_url}/solve_equation", json=payload, timeout=30)
    print(f"状态码: {resp.status_code}")
    
    if resp.status_code == 200:
        result = resp.json()
        print(f"响应: {result}")
        print("\n✅ 1D 热传导方程求解成功！")
    else:
        print(f"响应: {resp.text}")
        print(f"\n❌ 1D 热传导方程求解失败，状态码: {resp.status_code}")
except Exception as e:
    print(f"\n❌ 错误: {e}")
