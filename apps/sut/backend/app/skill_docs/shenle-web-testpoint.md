---
title: shenle-web-testpoint
---

# shenle-web-testpoint

> 分组：**测试点分析**　来源：`.claude/skills/shenle-web-testpoint`

## 它是什么

AI-WEB功能测试点分析生成技能（单批次版）。

## 核心功能

- `references/testpoint-template.md`：页面测试点与全局公共模块的最终 Markdown 模板
- `references/testpoint-spec.md`：批次读取、分析边界、输出规则、公共模块策略和自检规范
- 用户说"分析测试点" / "生成测试点" / "测试点分析" / "根据指定批次生成WEB测试点文档" + **明确提供批次号**
- 用户提供具体 JSON 文件路径

## 怎么用

```bash
{工作空间}/                          ← 项目根目录
├── AI-信息采集/{批次号}/{模块路径}/      ← 输入
│   ├── json/dom_001.json
│   └── img/screenshot_001.png
```

## 产物与判读

本技能有明确输出物：页面测试点分析 Markdown 与全局公共模块 Markdown。执行前必须按需读取：

- `references/testpoint-template.md`：页面测试点与全局公共模块的最终 Markdown 模板
- `references/testpoint-spec.md`：批次读取、分析边界、输出规则、公共模块策略和自检规范

硬性要求：最终产物结构以 template 为准，生成行为和质量要求以 spec 为准。

## 常见失败模式

输入缺字段、路径不存在时会直接报错；先按 SKILL.md 核对入参。

## 相关

- 全文与下载：[Skills 库](/skills/shenle-web-testpoint)
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

判定：✅ 达标，正文 240 行；明细见 docs/skill-scores.json。
