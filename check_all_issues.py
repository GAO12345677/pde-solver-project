"""系统检查所有可能的问题"""
import requests
import subprocess
import sys
import os

print("=" * 60)
print("系统检查所有可能的问题")
print("=" * 60)

# 1. 检查后端服务
print("\n1. 检查后端服务")
try:
    resp = requests.get("http://127.0.0.1:8001/health", timeout=5)
    if resp.status_code == 200:
        print("✅ 后端服务正常运行")
    else:
        print(f"❌ 后端服务异常，状态码: {resp.status_code}")
except Exception as e:
    print(f"❌ 后端服务不可用: {e}")

# 2. 检查前端服务
print("\n2. 检查前端服务")
try:
    resp = requests.get("http://127.0.0.1:3000/", timeout=5)
    if resp.status_code == 200:
        print("✅ 前端服务正常运行")
    else:
        print(f"❌ 前端服务异常，状态码: {resp.status_code}")
except Exception as e:
    print(f"❌ 前端服务不可用: {e}")

# 3. 检查后端路由
print("\n3. 检查后端路由")
routes_to_check = [
    ("GET", "http://127.0.0.1:8001/"),
    ("GET", "http://127.0.0.1:8001/llm/admin"),
    ("GET", "http://127.0.0.1:8001/llm/config/get"),
    ("POST", "http://127.0.0.1:8001/llm/config/test"),
    ("POST", "http://127.0.0.1:8001/solve_equation"),
]

for method, url in routes_to_check:
    try:
        if method == "GET":
            resp = requests.get(url, timeout=5)
        else:
            resp = requests.post(url, json={}, timeout=5)
        
        status_icon = "✅" if resp.status_code == 200 else "❌"
        print(f"{status_icon} {method:6} {url:50} - {resp.status_code}")
    except Exception as e:
        print(f"❌ {method:6} {url:50} - 错误: {e}")

# 4. 检查前端构建文件
print("\n4. 检查前端构建文件")
import os
from pathlib import Path

dist_path = Path("static/dist")
if dist_path.exists():
    index_html = dist_path / "index.html"
    if index_html.exists():
        print(f"✅ 前端构建文件存在: {index_html}")
        print(f"   文件大小: {index_html.stat().st_size} 字节")
    else:
        print(f"❌ 前端构建文件不存在: {index_html}")
else:
    print(f"❌ 前端构建目录不存在: {dist_path}")

# 5. 检查 Python 环境
print("\n5. 检查 Python 环境")
print(f"Python 可执行文件: {sys.executable}")
print(f"Python 版本: {sys.version}")

try:
    import websockets
    print(f"✅ websockets 已安装，版本: {websockets.__version__}")
except ImportError:
    print("❌ websockets 未安装")

# 6. 检查端口占用
print("\n6. 检查端口占用")
try:
    result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
    if "8001" in result.stdout:
        print("✅ 端口 8001 已被占用")
    else:
        print("❌ 端口 8001 未被占用")
    
    if "3000" in result.stdout:
        print("✅ 端口 3000 已被占用")
    else:
        print("❌ 端口 3000 未被占用")
except Exception as e:
    print(f"❌ 检查端口占用失败: {e}")

print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)
