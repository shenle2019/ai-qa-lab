# 模块 02 笔记：自己写一个迷你 pytest，难在哪

## 问题

项目里已经有 pytest 8.3.4，为什么还要自己写一个？

因为面试里说“熟悉 pytest”，和能解释“pytest 怎么收集用例、怎么做 fixture 注入、怎么把参数化展开成多条 case、怎么在失败时给出 diff”，是两件事。模块 02 的目标是把这些机制拆开重写一遍，能跑、能测、能讲。

约束：

- 不能 fork pytest，也不能复制源码；
- 包名不能叫 `pytest`，不能影响现有 33 个测试；
- 必须形成完整闭环：输入 → 执行 → 结果 → 报告；
- 每个机制都要有真实 pytest 元测试，不能只写 demo。

## 方案

包放在 `libs/minipytest`，导入路径 `libs.minipytest`，核心只用标准库。

| 机制 | 实现 |
|---|---|
| 收集 | 扫描 `test_*.py`，按源码行号排序，展开参数化 |
| fixture | 按参数名注入，function/module/session 三级缓存，yield teardown |
| 参数化 | 堆叠 `@parametrize`，按签名顺序做笛卡尔积，生成 node ID |
| marker | `-m` 递归下降解析，支持 and/or/not/括号 |
| 断言 | `assert_that(...)` 链式 API，expected/actual + unified diff |
| 重试 | 全局 `--retry` + 单测 `@mark.retry(n)`，记录每次 attempt |
| 报告 | JSON + 单文件离线 HTML，无 CDN |

## 结果

- 真实 pytest：66 passed（33 现有 + 33 框架元测试）
- 迷你 pytest 验收演示：20 cases，17 passed、1 skipped、1 xfailed、1 xpassed，exit 0
- 故意失败演示：9 cases，7 failed、2 errors，exit 1
- 报告：`docs/portfolio/module-02-minipytest-report.html`
- 控制台入口：`/portfolio/module-02-minipytest-report.html`

## 踩坑

1. 类没有 `__code__`，最初用 `cls.__code__.co_firstlineno` 排序直接报错，改用 `inspect.getsourcelines`。
2. 失败位置一开始落在框架的 `assertions.py`，因为反向找 traceback 拿到了最后一个 frame。修复方式是跳过框架根目录下的直接文件。
3. Windows 控制台默认 GBK，中文原因容易乱码。报告统一 UTF-8，控制台状态标签用 ASCII。
4. 真实 pytest 会把迷你 pytest 的 demo 当普通测试收集，在 `demo/conftest.py` 加 `collect_ignore_glob` 隔离。
5. uvicorn 子进程必须在 `finally` 里 terminate/wait/kill，否则测试结束会留下端口和进程。

## 一句话

写一个能跑的迷你测试框架不难，难的是把“收集、依赖注入、参数化、失败定位、报告”这条链路做对，并且用真实 pytest 证明它对。
