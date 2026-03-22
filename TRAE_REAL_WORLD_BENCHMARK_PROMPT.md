把下面这段直接发给 Trae：

```text
请不要改我现有项目主代码，只执行并维护新的真实案例 benchmark 工具链。

工作范围仅限：
- scripts/real_world_benchmark.py
- real_world_benchmark/

不要修改：
- solver/
- api/
- static/src/
- algorithm/

请按下面步骤做：

1. 在项目根目录运行：
   D:\cursorku\.venv\Scripts\python.exe scripts\real_world_benchmark.py all

2. 检查输出文件：
   - real_world_benchmark/literature_cases.json
   - real_world_benchmark/latest_local_results.json
   - real_world_benchmark/latest_report.md
   - real_world_benchmark/sota_results.template.json

3. 不要改现有 solver，只允许在 real_world_benchmark 目录里追加：
   - 更多公开来源
   - 更详细的 case metadata
   - sota_results.json

4. 如果要补 SOTA，请优先从公开学术来源中提取：
   - PDEBench
   - PDEArena
   - 文献中的公开 benchmark 表格

5. 填写 real_world_benchmark/sota_results.json 后，再运行：
   D:\cursorku\.venv\Scripts\python.exe scripts\real_world_benchmark.py compare

6. 任何情况下不要擅自重构我的主项目页面、后端接口或求解器实现。
```
