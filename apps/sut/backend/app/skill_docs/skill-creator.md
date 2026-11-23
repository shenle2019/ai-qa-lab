---
title: skill-creator
---

# skill-creator

> 分组：**通用能力**　来源：`.claude/skills/skill-creator`

## 它是什么

写新技能时的脚手架：结构、校验、评测一条龙。

技能自带的触发描述：

> Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an e

## 核心功能

- 生成标准 SKILL.md 骨架（frontmatter + 触发描述）
- `quick_validate.py` 校验格式
- `run_eval.py` 跑评测，`package_skill.py` 打包

## 怎么用

```bash
python .claude/skills/skill-creator/scripts/quick_validate.py --help
```

## 产物与判读

可发布的技能目录（SKILL.md + scripts/ + references/）

## 常见失败模式

description 写得太宽会让技能乱触发

## 相关

- 单跑记录：[skill-creator 单跑记录](/labs/skills/skill-creator)
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
