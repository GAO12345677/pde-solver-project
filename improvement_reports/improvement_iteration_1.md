# 持续优化报告 #1

- 时间戳：2026-03-21 11:13:55
- 基准报告：`benchmark\benchmark_1774062822.json`
- 回归测试状态：`PASS`

## 模型重训练

- `static_rf`: {'strategy': 'static_rf', 'num_samples': 240, 'labels': ['fdm', 'fem', 'spectral']}
- `mlp_nn`: {'strategy': 'mlp_nn', 'num_samples': 240, 'labels': ['fdm', 'fem', 'spectral']}
- `dynamic_rl`: {'episodes': 300, 'avg_reward': 0.7018992132837999, 'min': 0.6107703494106984, 'max': 0.8058043497974574}

## 选择器准确率

- `static_rf`: `accuracy=1.000` on `60` samples
- `mlp_nn`: `accuracy=1.000` on `60` samples
- `dynamic_rl`: `accuracy=0.267` on `60` samples

## 求解器误差

- `heat1d / fdm`: `L2=1.743408e-05`, `Linf=2.492453e-05`, `elapsed=0.0832s`
- `heat1d / fem`: `L2=1.743429e-05`, `Linf=2.484311e-05`, `elapsed=0.3193s`
- `heat1d / spectral`: `L2=9.427012e-12`, `Linf=1.339862e-11`, `elapsed=0.4818s`
- `wave1d / fdm`: `L2=4.260903e-05`, `Linf=6.055881e-05`, `elapsed=0.0022s`

## 回归测试输出

```text
................                                                         [100%]
============================== warnings summary ===============================
main.py:155
  D:\cursorku\main.py:155: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    @app.on_event("startup")

.venv\lib\site-packages\fastapi\applications.py:4599
  D:\cursorku\.venv\lib\site-packages\fastapi\applications.py:4599: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    return self.router.on_event(event_type)

tests/test_wave1d_api.py::test_extract_feature_wave1d
  D:\cursorku\.venv\lib\site-packages\torch\cuda\__init__.py:65: FutureWarning: The pynvml package is deprecated. Please install nvidia-ml-py instead. If you did not install pynvml directly, please report this to the maintainers of the package that installed pynvml for you.
    import pynvml  # type: ignore[import]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
16 passed, 3 warnings in 9.17s
```

## 下一步建议

- `dynamic_rl` 准确率偏低，建议优先扩展状态表示、奖励设计和训练轮数。
- 当前回归测试通过，可以继续做能力扩展。