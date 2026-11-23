---
title: shenle-test-flow-builder
---

# shenle-test-flow-builder

> 分组：**编排与计划**　来源：`.claude/skills/test-flow-builder`

## 它是什么

把录制产物整理成可执行的流程（步骤 + 数据 + 断言）。

技能自带的触发描述：

> 对话式引导构建完整的自动化测试流程。触发场景：用户要求编排测试流程、生成完整测试链路、创建自动化测试 flow。手工用例优先转换为自动化用例 YAML，动态函数委托已有 Skill 生成，最终串联为 case_flow 编排文件。支持接口、Web UI、性能等全部测试类型，智能复用已有资源。

## 核心功能

- 统一步骤结构，屏蔽 web / app / api 的差异
- 支持从快照推导候选步骤
- 输出带校验的流程描述，供执行器直接吃

## 怎么用

```bash
按 SKILL.md 提示，把快照目录交给它生成 flow
校验：`.venv/Scripts/python.exe -m pytest labs/ch46-toolchain -q`
```

## 产物与判读

`flows/*.json`（步骤、数据引用、断言）

## 常见失败模式

录制产物缺字段时，生成的步骤会缺断言

## 相关

- 单跑记录：[shenle-test-flow-builder 单跑记录](/labs/skills/test-flow-builder)
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
