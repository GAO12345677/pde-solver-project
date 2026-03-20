"""测试 WebSocket 连接"""
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
