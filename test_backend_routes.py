"""测试后端路由"""
import requests

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("测试后端路由")
print("=" * 60)

routes_to_test = [
    ("/", "GET"),
    ("/llm/admin", "GET"),
    ("/llm/config/get", "GET"),
    ("/llm/config/test", "POST"),
    ("/solve_equation", "POST"),
]

for route, method in routes_to_test:
    try:
        if method == "GET":
            resp = requests.get(f"{base_url}{route}", timeout=30)
        else:
            resp = requests.post(f"{base_url}{route}", json={}, timeout=30)
        
        status_icon = "✅" if resp.status_code == 200 else "❌"
        print(f"{status_icon} {method:6} {route:30} - {resp.status_code}")
        if resp.status_code != 200:
            print(f"   响应: {resp.text[:200]}")
    except Exception as e:
        print(f"❌ {method:6} {route:30} - 错误: {e}")
