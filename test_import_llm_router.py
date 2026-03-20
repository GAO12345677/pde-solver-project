"""测试导入 llm_router"""
try:
    from api.llm.llm_routes import router as llm_router
    print("✅ llm_router 导入成功")
    print(f"路由类型: {type(llm_router)}")
    print(f"路由对象: {llm_router}")
    if hasattr(llm_router, 'routes'):
        print(f"路由数量: {len(llm_router.routes)}")
        for route in llm_router.routes:
            print(f"  - {route.methods} {route.path}")
    else:
        print("⚠️ 路由对象没有 'routes' 属性")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
