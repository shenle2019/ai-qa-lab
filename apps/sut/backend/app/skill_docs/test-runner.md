---
title: shenle-test-runner
---

# shenle-test-runner

> 分组：**编排与计划**　来源：`.claude/skills/test-runner`

## 它是什么

按计划执行，串行/并行调度流程，产出执行结果。

技能自带的触发描述：

> AIQE 测试计划执行规约。告诉 agent 拿到一份 plan（如 plan-web-20260921-224910-登录并修改用户昵称（接口版））后，如何按 plan → flow → task → case/function 的层级逐条执行，处理 4 种任务类型（dynamic-function / api / 

## 核心功能

- 读计划 → 逐条执行 → 记录每步结果
- 失败可重试，重试次数在计划里配置
- 结果结构化，供报告渲染

## 怎么用

```bash
按 SKILL.md 指定计划路径执行
执行完把结果目录交给报告技能
```

## 产物与判读

`result/<run-id>/*.json`

## 常见失败模式

设备/浏览器被占用时并发执行会互相踩

## 相关

- 单跑记录：[shenle-test-runner 单跑记录](/labs/skills/test-runner)
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
