---
title: shenle-report-generate-html
---

# shenle-report-generate-html

> 分组：**报告与扩展**　来源：`.claude/skills/report-generate-html`

## 它是什么

把执行结果渲染成一份可发给别人的 HTML 报告。

技能自带的触发描述：

> 把 shenle-ai-test-runner 跑出的 allure-results/ JSON 数据渲染成单文件静态 HTML 报告（无需 Allure CLI / Java 环境）。接受 plan-id 和 timestamp，输出 report.html 到对应 run 目录。

## 核心功能

- 单文件 HTML，不依赖外部资源
- 按用例聚合通过/失败、耗时与失败原因
- 带时间戳，便于横向比较

## 怎么用

```bash
python .claude/skills/shenle-report-generate-html/scripts/generate_html.py --help
```

## 产物与判读

`report.html`

## 常见失败模式

结果缺 `case_id` 时无法聚合，只能逐条平铺

## 相关

- 单跑记录：[shenle-report-generate-html 单跑记录](/labs/skills/report-generate-html)
- 返回：[Skills 手册](/kb/skills/)

## 评分（skill-judge）

总分 **111 / 120**（≥108 为 A 级），按 skill-judge 八维逐项打分：

| 维度 | 得分 | 满分 |
| --- | --- | --- |
| D1 知识增量 | 17 | 20 |
| D2 心智与流程 | 15 | 15 |
| D3 反模式 | 13 | 15 |
| D4 规格 | 15 | 15 |
| D5 渐进披露 | 14 | 15 |
| D6 自由度 | 12 | 15 |
| D7 模式识别 | 10 | 10 |
| D8 实用可用性 | 15 | 15 |

判定：✅ 达标，规范条数见 `docs/skill-scores.json`。
