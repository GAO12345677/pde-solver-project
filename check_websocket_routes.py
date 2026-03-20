"""检查 WebSocket 路由注册"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

print("=" * 60)
print("检查 WebSocket 路由注册")
print("=" * 60)

ws_routes = []
for route in app.routes:
    if hasattr(route, 'path') and '/ws/' in route.path:
        ws_routes.append(route)
        print(f"✅ 找到 WebSocket 路由: {route.path}")
        print(f"   类型: {type(route).__name__}")

if not ws_routes:
    print("❌ 没有找到 WebSocket 路由！")
else:
    print(f"\n总共找到 {len(ws_routes)} 个 WebSocket 路由")
