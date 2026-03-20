"""检查 FastAPI 应用的路由"""
import requests

base_url = "http://127.0.0.1:8001"

# 获取 OpenAPI 规范
try:
    resp = requests.get(f"{base_url}/openapi.json", timeout=30)
    if resp.status_code == 200:
        openapi = resp.json()
        print("=" * 60)
        print("FastAPI 应用路由")
        print("=" * 60)
        print(f"标题: {openapi.get('info', {}).get('title')}")
        print(f"版本: {openapi.get('info', {}).get('version')}")
        print(f"路由数量: {len(openapi.get('paths', {}))}")
        print()
        
        for path, methods in openapi.get('paths', {}).items():
            for method, details in methods.items():
                print(f"  {method.upper():6} {path}")
    else:
        print(f"❌ 获取 OpenAPI 规范失败: {resp.status_code}")
except Exception as e:
    print(f"❌ 错误: {e}")
