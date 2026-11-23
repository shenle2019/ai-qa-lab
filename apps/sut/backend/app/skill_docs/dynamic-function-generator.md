---
title: shenle-dynamic-function-generator
---

# shenle-dynamic-function-generator

> 分组：**报告与扩展**　来源：`.claude/skills/dynamic-function-generator`

## 它是什么

工具不够用时，按需求临时生成一个小函数补位。

技能自带的触发描述：

> AI 自动化流程中动态生成符合 AIQE 规范的动态函数文件。当 AI 需要在流程中创建可被节点调用的函数时，当用户要求 AI 创建动态函数、自动化函数、workflow 函数时，或流程执行时需要动态生成工具函数时，都应使用此 Skill。AI 会直接在指定工作区目录下编辑文件，无需通过界面操作。

## 核心功能

- 输入是「要做什么 + 输入输出约束」
- 生成后立刻在受控环境里试跑
- 产物要能被人读懂、能进版本库

## 怎么用

```bash
按 SKILL.md 描述需求，生成后自行校验并落盘
生成的函数放进项目 `labs/` 下，随测试一起跑
```

## 产物与判读

一个 Python 函数文件 + 使用示例

## 常见失败模式

约束写得含糊时会生成无法测试的函数

## 相关

- 单跑记录：[shenle-dynamic-function-generator 单跑记录](/labs/skills/dynamic-function-generator)
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
