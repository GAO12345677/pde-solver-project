"""测试 WebSocket 路由"""
import requests

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("测试 WebSocket 路由")
print("=" * 60)

# 测试 WebSocket 路由（使用 HTTP GET 请求）
ws_paths = [
    "/ws/solve/test_task_id",
    "/ws/solve/",
    "/ws/solve/task_12345",
]

for path in ws_paths:
    try:
        resp = requests.get(f"{base_url}{path}", timeout=30)
        print(f"GET {path:30} - {resp.status_code}")
        if resp.status_code != 404:
            print(f"   响应: {resp.text[:100]}")
    except Exception as e:
        print(f"GET {path:30} - 错误: {e}")

print("\n" + "=" * 60)
print("检查所有路由")
print("=" * 60)

# 获取 OpenAPI 规范
try:
    resp = requests.get(f"{base_url}/openapi.json", timeout=30)
    if resp.status_code == 200:
        openapi = resp.json()
        paths = openapi.get('paths', {})
        print(f"总路由数: {len(paths)}")
        print()
        
        # 按路径排序
        sorted_paths = sorted(paths.keys())
        for path in sorted_paths:
            print(f"  {path}")
    else:
        print(f"❌ 获取 OpenAPI 规范失败: {resp.status_code}")
except Exception as e:
    print(f"❌ 错误: {e}")
