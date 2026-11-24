---
title: shenle-api-doc-generator
---

# shenle-api-doc-generator

> 分组：**用例生成**　来源：`.claude/skills/shenle-api-doc-generator`

## 它是什么

接口文档生成器。

## 核心功能

- 一次处理**一个** `raw.json` 文件
- 该文件里通常含**多个**接口条目（数组或单个 dict），每个条目 = 一个 MD
- 跨文件 / 跨批次处理不在本技能范围
- `references/apidoc-template.md`：最终 MD 文件结构与字段

## 怎么用

```bash
AI-信息采集/{batch}/raw01.json  →  AI-接口管理/{batch}/001_GET_xxx.md
shenle-api-doc-generator/
├── SKILL.md                          ← 本文件
├── references/
```

## 产物与判读

执行前必须按需读取：

- `references/apidoc-template.md`：最终 MD 文件结构与字段
- `references/apidoc-spec.md`：事实性约束、去重规则

## 常见失败模式

输入缺字段、路径不存在时会直接报错；先按 SKILL.md 核对入参。

## 相关

- 全文与下载：[Skills 库](/skills/shenle-api-doc-generator)
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

判定：✅ 达标，正文 250 行；明细见 docs/skill-scores.json。
