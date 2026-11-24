---
title: shenle-android-case-generator
---

# shenle-android-case-generator

> 分组：**用例生成**　来源：`.claude/skills/shenle-android-case-generator`

## 它是什么

基于单个安卓测试点分析文档（MD）生成安卓功能测试用例，每次一个独立新文件（文件名带 YYYYMMDDHHMMSS 时间戳）。

## 核心功能

- 解析测试点分析文档中的功能测试点、状态测试点、边界条件、安卓补充测试点
- 拆解测试点为具体可执行的测试用例（含具体测试数据）
- 生成带测试步骤、预期结果、前置条件的标准化 Markdown 用例
- 自动使用占位符表示测试数据

## 怎么用

```bash
{工作空间}/
├── AI-测试点分析/<module>/<功能名>.md     ← 测试点分析（输入）
└── AI-测试用例/<module>/                 ← 用例（输出）
└── <功能名>_测试用例_<YYYYMMDDHHMMSS>.md
```

## 产物与判读

本技能有明确输出物：安卓功能测试用例 Markdown 文件。执行前必须读取：

- `references/testcase-template.md`：最终测试用例 Markdown 模板
- `references/testcase-spec.md`：测试点拆解、测试设计、步骤写法、优先级和编号规则

## 常见失败模式

输入缺字段、路径不存在时会直接报错；先按 SKILL.md 核对入参。

## 相关

- 全文与下载：[Skills 库](/skills/shenle-android-case-generator)
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
