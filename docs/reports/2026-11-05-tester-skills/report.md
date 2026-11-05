# ai-qa-lab 接口自动化测试快照（2026-11-05）

## 目标

用 SeaZhusp/tester-skills 的 skill 对线上 ai-qa-lab 做接口自动化测试，验证「从接口文档生成用例 → 执行 → 出报告」这条链路是否可复刻。

## 过程

1. 从 SUT 源码（FastAPI）导出 OpenAPI：31 paths / 39 operations。
2. 用 api-testcase-generator 解析并生成 35 条用例（Pytest + Excel）。
3. 对线上环境执行：
   - 首轮未带认证：35 条中 7 通过、28 失败（401 为主）。
   - 补 `Authorization: Bearer <APP_API_KEY>` 后：401 消失，但 422 参数校验失败仍在。
   - 修正生成器骨架（真实 ID、合法请求体、认证头）后：29 条全通过。
4. 用 defect-report-generator 把结果转成 HTML 报告，用 docx 产出 Word 报告。

## 覆盖

健康检查、`/ready`、平台 summary/projects/cases/plans/executions/defects/models/model-calls、工单 CRUD（建→改→删→查 404）、认证校验、知识库问答、计划执行。

生产特殊规则单独断言：`/plans/{id}/run` 返回 410（生产禁用客户端上报），真实执行走 `/execute`（202）。

## 结论

- tester-skills 的用例生成与报告能力可用。
- 生成器产出是骨架，需修正三类缺陷（函数名合法化、路径占位符替换、必填字段填充）才能直接执行。
- 两个 Apifox skill 需先接入 Apifox MCP 与 api-auto-test 框架。
- fireworks-tech-graph 目录不完整。

## 产物

见 `artifacts/`：defect-report.html、final-test-report.docx、testcases.xlsx、junit-results.xml、qa-results.csv、openapi.json、test_aiqa_api.py。
