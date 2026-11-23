---
title: Skills 手册
---

# Skills 手册

按「在流水线里的位置」分组。每组先看功能，再点单跑记录看真实输出。

## 录制采集

| 技能 | 做什么 | 手册 | 单跑记录 |
| --- | --- | --- | --- |
| `shenle-web-record` | 打开网页，人工点 SNAP 抓当前视口与元素结构，按批次落盘。 | [手册](/kb/skills/web-record) | [记录](/labs/skills/web-record) |
| `shenle-device-record` | 连安卓设备，抓当前屏幕与界面层级，落盘成结构化快照。 | [手册](/kb/skills/device-record) | [记录](/labs/skills/device-record) |
| `shenle-api-record` | 本地代理抓接口请求，装 CA 后可解 HTTPS，产出接口清单。 | [手册](/kb/skills/api-record) | [记录](/labs/skills/api-record) |

## 执行与定位

| 技能 | 做什么 | 手册 | 单跑记录 |
| --- | --- | --- | --- |
| `shenle-web-cli` | 给网页截图，让视觉模型找元素，直接点击、输入、读回页面内容。 | [手册](/kb/skills/web-cli) | [记录](/labs/skills/web-cli) |
| `shenle-android-cli` | 连安卓设备，截图后视觉定位并执行点击、输入、滑动、按键。 | [手册](/kb/skills/android-cli) | [记录](/labs/skills/android-cli) |
| `shenle-api-cli` | 命令行发接口请求、抽字段、断言，替代 curl 给 AI 用。 | [手册](/kb/skills/api-cli) | [记录](/labs/skills/api-cli) |

## 编排与计划

| 技能 | 做什么 | 手册 | 单跑记录 |
| --- | --- | --- | --- |
| `shenle-test-flow-builder` | 把录制产物整理成可执行的流程（步骤 + 数据 + 断言）。 | [手册](/kb/skills/test-flow-builder) | [记录](/labs/skills/test-flow-builder) |
| `shenle-test-plan-generator` | 按流程与用例生成测试计划，含环境选择与编排扫描。 | [手册](/kb/skills/test-plan-generator) | [记录](/labs/skills/test-plan-generator) |
| `shenle-test-runner` | 按计划执行，串行/并行调度流程，产出执行结果。 | [手册](/kb/skills/test-runner) | [记录](/labs/skills/test-runner) |

## 报告与扩展

| 技能 | 做什么 | 手册 | 单跑记录 |
| --- | --- | --- | --- |
| `shenle-report-generate-html` | 把执行结果渲染成一份可发给别人的 HTML 报告。 | [手册](/kb/skills/report-generate-html) | [记录](/labs/skills/report-generate-html) |
| `shenle-dynamic-function-generator` | 工具不够用时，按需求临时生成一个小函数补位。 | [手册](/kb/skills/dynamic-function-generator) | [记录](/labs/skills/dynamic-function-generator) |

## 通用能力

| 技能 | 做什么 | 手册 | 单跑记录 |
| --- | --- | --- | --- |
| `playwright-cli` | 直接用 Playwright 操作浏览器：导航、取属性、跑脚本、存会话。 | [手册](/kb/skills/playwright-cli) | [记录](/labs/skills/playwright-cli) |
| `skill-creator` | 写新技能时的脚手架：结构、校验、评测一条龙。 | [手册](/kb/skills/skill-creator) | [记录](/labs/skills/skill-creator) |

## 一条命令自检

```bash
.venv/Scripts/python.exe -m pytest labs/ch46-toolchain -q
```

## 审核结果（skill-judge 120 分制）

| 技能 | 总分 | 等级 |
| --- | --- | --- |
| shenle-api-record | 111 | A |
| shenle-test-plan-generator | 111 | A |
| playwright-cli | 109 | A |
| shenle-android-cli | 109 | A |
| shenle-dynamic-function-generator | 109 | A |
| shenle-test-flow-builder | 109 | A |
| shenle-test-runner | 109 | A |
| shenle-web-cli | 109 | A |
| shenle-web-record | 109 | A |
| skill-creator | 109 | A |

全部技能 ≥108 分；打分口径与逐维明细在 `docs/skill-scores.json`，评分脚本 `scripts/_score_skills.py`。
