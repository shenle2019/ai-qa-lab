---
title: playwright-cli
---

# playwright-cli

> 分组：**通用能力**　来源：`.claude/skills/playwright-cli`

## 它是什么

直接用 Playwright 操作浏览器：导航、取属性、跑脚本、存会话。

技能自带的触发描述：

> Automate browser interactions, test web pages and work with Playwright tests.

## 核心功能

- 覆盖导航、点击、输入、断言、截图、trace
- 支持存/复用 `storage_state` 跳过登录
- 可跑任意 JS、可 mock 请求

## 怎么用

```bash
按 SKILL.md 里的参考文档选择动作
复杂场景参考 `references/spec-driven-testing.md`
```

## 产物与判读

截图、trace、执行日志

## 常见失败模式

选择器写死时页面一改就断，优先用 role / label

## 相关

- 单跑记录：[playwright-cli 单跑记录](/labs/skills/playwright-cli)
- 返回：[Skills 手册](/kb/skills/)

## 评分（skill-judge）

总分 **109 / 120**（≥108 为 A 级），按 skill-judge 八维逐项打分：

| 维度 | 得分 | 满分 |
| --- | --- | --- |
| D1 知识增量 | 17 | 20 |
| D2 心智与流程 | 15 | 15 |
| D3 反模式 | 13 | 15 |
| D4 规格 | 15 | 15 |
| D5 渐进披露 | 12 | 15 |
| D6 自由度 | 12 | 15 |
| D7 模式识别 | 10 | 10 |
| D8 实用可用性 | 15 | 15 |

判定：✅ 达标，规范条数见 `docs/skill-scores.json`。
