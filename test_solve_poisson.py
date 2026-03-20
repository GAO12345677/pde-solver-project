"""测试 2D Poisson 方程求解"""
import requests

# 测试 2D Poisson 方程求解
url = "http://127.0.0.1:8001/solve_equation"
headers = {
    "Content-Type": "application/json"
}
payload = {
    "equation_type": "poisson2d_nonlinear",
    "algorithm_key": "fem",
    "precision_requirement": "high",
    "realtime_requirement": "low",
    "resource_budget": 0.9,
    "boundary_condition": "dirichlet",
    "nx": 50,
    "ny": 50,
    "source_function": "sin(x*pi)*sin(y*pi)"
}

print("=" * 60)
print("测试 2D Poisson 方程求解")
print("=" * 60)
print(f"URL: {url}")
print(f"Payload: {payload}")
print()

try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.text[:500]}...")
    
    if resp.status_code == 200:
        print("\n✅ 2D Poisson 方程求解成功！")
    else:
        print(f"\n❌ 求解失败，状态码: {resp.status_code}")
except Exception as e:
    print(f"\n❌ 错误: {e}")
