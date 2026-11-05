# 2026-11-05 · tester-skills 应用存档

用 [SeaZhusp/tester-skills](https://github.com/SeaZhusp/tester-skills) 对 ai-qa-lab 做的接口自动化测试实践快照。

## 一句话结果

39 个接口自动产出 35 条用例；修正生成器骨架后，**29 条修正版用例对线上环境 100% 通过**。

## 应用了哪些 skill

| Skill | 应用情况 |
|---|---|
| api-testcase-generator | 解析 SUT OpenAPI（31 paths / 39 operations）→ 35 条用例（Excel + Pytest） |
| defect-report-generator | 执行结果 CSV → 自包含 HTML 报告 |
| docx | 生成 Word 版最终测试报告 |
| api-index-sync-apifoxmcp | 未适用（依赖 Apifox MCP + 内部 knowledge-base） |
| api-script-gen-with-apifoxmcp | 未适用（依赖 Apifox MCP + api-auto-test 框架） |
| fireworks-tech-graph | 不可用（仓库该目录仅含 LICENSE，缺 SKILL.md） |

## 三轮执行

| 轮次 | 用例 | 通过 | 失败 | 说明 |
|---|---:|---:|---:|---|
| 1 | 35 | 7 | 28 | 未带认证，401 为主 |
| 2 | 35 | 7 | 28 | 补 APP_API_KEY 后 401 消失，422 仍在 |
| 3 | 29 | 29 | 0 | 修正版：真实 ID + 合法请求体 + 认证头 |

## 文件

- `report.md` —— 文字版小结
- `metrics.json` —— 指标
- `artifacts/defect-report.html` —— 完整 HTML 报告
- `artifacts/final-test-report.docx` —— Word 报告
- `artifacts/testcases.xlsx` —— 生成的用例表
- `artifacts/junit-results.xml` / `artifacts/qa-results.csv` —— 结构化执行结果
- `artifacts/openapi.json` —— 由 SUT 源码导出的接口定义
- `artifacts/test_aiqa_api.py` —— 修正版可复跑脚本

## 生成器缺陷（修正前不可直接执行）

1. 函数名含连字符（`test_platform_model-calls_get`）→ 语法错误；
2. 路径参数是 `<id>` 占位符；
3. 请求体为空 `{}`，缺 `title` / `name` / `project_id` 等必填字段。

修正版脚本见 `artifacts/test_aiqa_api.py`。
