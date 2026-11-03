# 模块 07 笔记：测试平台不是页面，是数据闭环

## 问题

很多“测试平台”最后做成了一堆表单：项目、用例、计划都有，但执行结果进不来，缺陷跟执行没关系，报表是假的。

真正要解决的是数据怎么流动：

```
项目 → 用例 → 计划 → 执行 → 结果 → 缺陷 → 报表
```

## 方案

在现有 SUT 控制台里加一层平台，不另起一套前后端。

| 能力 | 实现 |
|---|---|
| 项目 | `platform_projects` |
| 用例 | `platform_cases`，挂项目 |
| 计划 | `platform_plans`，挂项目 |
| 执行 | `platform_executions`，挂计划 |
| 结果 | `platform_results`，挂执行 |
| 缺陷 | `platform_defects`，挂项目 |
| 报表 | `/api/platform/summary` + 页面卡片 |
| 导入 | `POST /api/platform/import/minipytest` |
| 演示 | `POST /api/platform/seed` |

## 结果

- 13 个平台 API 端点
- 6 个后端测试通过
- 演示数据：1 项目、4 用例、1 计划、1 执行、1 缺陷
- 最近执行：2 passed、1 failed、1 skipped，通过率 66.7%
- 页面：`/ui/#/platform`
- 截图：`docs/portfolio/screenshots/module-07-platform.png`

## 踩坑

1. SQLite 外键默认不强制，演示阶段不做级联删除。
2. xfailed/xpassed 不能算失败，否则通过率失真。
3. seed 必须幂等，重复点击不能重复插入。
4. 前端要等 API 返回再断言/截图。
5. 通过率分母只算 passed + failed，跳过不算。

## 一句话

平台的价值不在页面多漂亮，而在“执行结果能进来，缺陷能跟上，报表能说清楚”。
