"""测试导入 websocket_router"""
try:
    from api.websocket_routes import router as websocket_router
    print("✅ websocket_router 导入成功")
    print(f"路由类型: {type(websocket_router)}")
    print(f"路由对象: {websocket_router}")
    if hasattr(websocket_router, 'routes'):
        print(f"路由数量: {len(websocket_router.routes)}")
        for route in websocket_router.routes:
            print(f"  - {type(route).__name__} {route.path}")
    else:
        print("⚠️ 路由对象没有 'routes' 属性")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
