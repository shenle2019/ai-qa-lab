# 模块复刻选型矩阵

> 选型日期：2026-11-02。star 数为当日 GitHub API 返回值，后续会变化。
> 原则：选择“同主题、star 最高、核心机制可复刻”的项目；只做 clean-room 复刻，不复制源码。许可证以仓库为准。

| 模块 | 最高星参考项目 | Stars | License | 为什么选它 | 复刻核心（不是 fork） |
|---|---|---:|---|---|---|
| 01 方法论 | [atinfo/awesome-test-automation](https://github.com/atinfo/awesome-test-automation) | 7,208 | 未声明 | 测试自动化领域最完整的索引型项目，适合抽成方法论与工具地图 | 知识图谱、分层选型决策树、检查表、AI 协作流程页面；不复制清单正文 |
| 02 Python 测试开发 | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) | 14,661 | MIT | Python 测试事实标准，核心机制清晰且可验证 | 迷你 pytest：用例收集、fixture 依赖注入（函数/模块/会话）、参数化、marker、断言内省、失败重试、JSON/HTML 报告 |
| 03 接口自动化 | [hoppscotch/hoppscotch](https://github.com/hoppscotch/hoppscotch) | 80,721 | MIT | 最高星的 API 开发与测试一体化平台，包含请求、集合、环境、脚本、批量运行 | API 工作台：请求构建、集合/环境、变量替换、前置/后置脚本沙箱、集合运行器、断言、历史、报告 |
| 04 Web 自动化 | [microsoft/playwright](https://github.com/microsoft/playwright) | 99,087 | Apache-2.0 | Web 测试自动化最高星，核心是 CDP/多浏览器协议与自动等待 | 迷你 Playwright：CDP 驱动、选择器、动作、自动等待、断言、重试、截图/轨迹、HTML 报告；不调用 Playwright 库 |
| 05 App UI 自动化 | [appium/appium](https://github.com/appium/appium) | 22,174 | Apache-2.0 | 移动端自动化事实标准，W3C WebDriver 协议清晰 | 迷你 Appium 客户端 + 会话管理 + 元素定位 + 手势；Android 侧通过 ADB/UIAutomator 驱动模拟器 |
| 06 性能测试 | [grafana/k6](https://github.com/grafana/k6) | 32,102 | AGPL-3.0 | 最高星现代压测工具，场景/阈值/指标模型值得复刻 | 压测引擎：常量 VU、阶梯加压、阈值判定、错误率/P95/P99、实时指标、HTML 报告；仅参考概念，不复制 AGPL 代码 |
| 07 测试平台 | [metersphere/metersphere](https://github.com/metersphere/metersphere) | 13,600 | NOASSERTION | 最贴近“持续测试平台”的高星项目（YApi 27,700 星但偏接口管理） | 测试管理闭环：项目、用例、计划、执行、缺陷、报表；平台前后端与权限 |
| 08 Agent/LLM 评测 | [confident-ai/deepeval](https://github.com/confident-ai/deepeval) | 19,242 | Apache-2.0 | 最高星 LLM 评测框架，指标与测试用例模型可直接映射 | 评测引擎：数据集、测试用例、DeepSeek 裁判、答案相关性/忠实度/上下文指标、批量运行、阈值、对比报告 |

## 备选与说明
- 04 Web：Cypress（约 48k）、Selenium（约 32k）可作为对照；选 Playwright 因为 star 最高且 CDP 路径适合复刻。
- 06 性能：Locust（28,257，MIT）比 k6 更容易用 Python 复刻；如果 AGPL 约束影响交付，切到 Locust 作为主参考，k6 仅作场景模型参考。
- 07 平台：YApi（27,700，Apache-2.0）星更高，但定位是接口管理；MeterSphere 更贴近“测试平台”。矩阵保留两者，最终以 MeterSphere 为主。
- 01 方法论：没有高星可运行项目，交付物是知识地图与方法论页面，不强行造应用。

## 统一验收标准
每个模块的验收页必须包含：
1. 参考项目卡片：名称、star、license、链接、选型理由。
2. 复刻范围与明确不做的部分。
3. 架构图与数据流。
4. 本地启动命令与使用步骤。
5. 真实运行截图/报告/指标。
6. 与参考项目的差异、取舍、踩坑。
7. 源码入口与关键文件说明。

## 执行顺序（按依赖与复用价值）
1. 02 迷你 pytest（测试基础设施，后续模块复用）
2. 03 API 工作台（直接服务 SUT 与验收页）
3. 07 测试平台（承载所有模块验收页）
4. 04 迷你 Playwright
5. 05 迷你 Appium
6. 06 压测引擎
7. 08 LLM 评测
8. 01 方法论页面（贯穿全程，最后汇总）
