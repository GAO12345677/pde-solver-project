"""测试前端开发服务器"""
import requests

base_url = "http://127.0.0.1:3000"

print("=" * 60)
print("测试前端开发服务器")
print("=" * 60)

# 测试根路径
try:
    resp = requests.get(f"{base_url}/", timeout=30)
    print(f"GET / - 状态码: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('Content-Type')}")
    print(f"Content-Length: {resp.headers.get('Content-Length')}")
    if resp.status_code == 200:
        print(f"响应前 200 字符: {resp.text[:200]}")
except Exception as e:
    print(f"GET / - 错误: {e}")

print()

# 测试 API 代理
try:
    resp = requests.get(f"{base_url}/health", timeout=30)
    print(f"GET /health (通过代理) - 状态码: {resp.status_code}")
    if resp.status_code == 200:
        print(f"响应: {resp.text}")
except Exception as e:
    print(f"GET /health (通过代理) - 错误: {e}")
