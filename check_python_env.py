"""检查 Python 环境和 websockets 安装"""
import sys
import os

print("=" * 60)
print("检查 Python 环境")
print("=" * 60)
print(f"Python 可执行文件: {sys.executable}")
print(f"Python 版本: {sys.version}")
print(f"虚拟环境: {hasattr(sys, 'real_prefix') and sys.real_prefix != sys.prefix}")
print()

try:
    import websockets
    print(f"✅ websockets 已安装")
    print(f"   版本: {websockets.__version__}")
except ImportError:
    print(f"❌ websockets 未安装")

print()
print(f"site-packages 路径:")
for path in sys.path:
    if 'site-packages' in path:
        print(f"  - {path}")
