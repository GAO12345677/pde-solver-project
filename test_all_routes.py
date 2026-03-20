"""测试所有路由"""
import requests

base_url = "http://127.0.0.1:8001"

routes_to_test = [
    ("/", "GET"),
    ("/health", "GET"),
    ("/llm/config/get", "GET"),
    ("/llm/config/test", "POST"),
    ("/llm/config/save", "POST"),
    ("/llm/quota/get", "GET"),
    ("/solve_equation", "POST"),
    ("/extract_feature", "POST"),
    ("/select_algorithm", "POST"),
]

print("=" * 60)
print("测试所有路由")
print("=" * 60)

for route, method in routes_to_test:
    try:
        if method == "GET":
            resp = requests.get(f"{base_url}{route}", timeout=30)
        else:
            resp = requests.post(f"{base_url}{route}", json={}, timeout=30)
        
        status_icon = "✅" if resp.status_code == 200 else "❌"
        print(f"{status_icon} {method:6} {route:30} - {resp.status_code}")
        if resp.status_code != 200:
            print(f"   响应: {resp.text[:100]}")
    except Exception as e:
        print(f"❌ {method:6} {route:30} - 错误: {e}")

print("\n" + "=" * 60)
print("访问 API 文档")
print("=" * 60)
print(f"Swagger: {base_url}/docs")
print(f"ReDoc: {base_url}/redoc")
