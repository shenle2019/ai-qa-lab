---
title: zentao-cli
---

# zentao-cli

> 分组：**执行与定位**　来源：`.claude/skills/zentao-cli`

## 它是什么

通过 zentao 命令行工具查询和操作禅道（ZenTao）数据，覆盖项目集、产品、项目、执行、需求、Bug、任务、测试用例、测试单、产品计划、版本、发布、反馈、工单、应用、用户、附件等模块的增删改查及状态流转。

## 核心功能

- 用户尚未登录时，不要在对话里收集账号密码。让用户直接在终端执行 `zentao login`，或执行任意 `zentao` 命令触发首次自动登录提示，由用户自行输入凭证。
- 展示给用户：不加 `--format` 参数，默认输出 Markdown 表格（列表）或列表（单个对象）
- 需要程序化处理：加 `--format=json`，返回结构化 JSON
- 不确定模块参数时，先执行 `zentao <module> help` 查看帮助，不确定操作参数时，先执行 `zentao <module> <action> help` 查看帮助

## 怎么用

```bash
npm install -g zentao-cli
zentao login -s https://zentao.example.com -u admin -p 123456
zentao story --product=1                # 产品 #1 的需求
zentao bug --product=1                  # 产品 #1 的 Bug
```

## 产物与判读

按 SKILL.md 约定落盘到工作目录，失败时保留原始输入。

## 常见失败模式

输入缺字段、路径不存在时会直接报错；先按 SKILL.md 核对入参。

## 相关

- 全文与下载：[Skills 库](/skills/zentao-cli)
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
