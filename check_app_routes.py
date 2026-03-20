"""检查 FastAPI 应用的所有路由"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

print("=" * 60)
print("FastAPI 应用的所有路由")
print("=" * 60)

for route in app.routes:
    if hasattr(route, 'path'):
        route_type = type(route).__name__
        print(f"  {route_type:20} {route.path}")
        if hasattr(route, 'methods'):
            print(f"    Methods: {route.methods}")

print(f"\n总路由数: {len(app.routes)}")
