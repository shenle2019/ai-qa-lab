---
title: shenle-api-case-generator
---

# shenle-api-case-generator

> 分组：**用例生成**　来源：`.claude/skills/shenle-api-case-generator`

## 它是什么

基于接口 MD 文档生成 API 测试用例，每个接口一个独立的新文件（文件名带 YYYYMMDDHHMMSS 时间戳）。

## 核心功能

- **输入**：单个接口 MD 路径（可由用户直接指定；未指定时扫描后询问）
- **输出**：一个测试用例 MD 文件，文件名 = `<interface_name>_测试用例_<YYYYMMDDHHMMSS>.md`
- **每次独立**：每次生成都是全新的文件，**不读、不改、不合并**任何已有用例文件
- **本技能无 subagent**——main flow（AI 本身）直接读 MD、读 references/、渲染 case MD、写入文件

## 怎么用

```bash
{工作空间}/
├── AI-信息采集/{batch}/raw*.json          ← 录制数据（不读）
├── AI-接口管理/**/*.md                    ← 接口文档（输入）
│   ├── {module_a}/001_POST_user_login.md
```

## 产物与判读

按 SKILL.md 约定落盘到工作目录，失败时保留原始输入。

## 常见失败模式

输入缺字段、路径不存在时会直接报错；先按 SKILL.md 核对入参。

## 相关

- 全文与下载：[Skills 库](/skills/shenle-api-case-generator)
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
