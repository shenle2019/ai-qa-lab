# 项目学习手册：AI全栈测试开发平台-shenle 是怎么一步步做出来的

> 版本：v0.2.0（2026-11-02）
> 读者：刚接触测试开发、需要把项目写进简历并能在面试中讲清楚的人
> 目标：看完这份手册，你能回答“这个项目是什么、每一步做了什么、为什么这么做、涉及哪些名词、原理是什么、效果是什么”。

---

## 0. 先搞清楚：你在做一个什么项目

### 0.1 它不是“一个 demo”

你做的不是“随便写个页面 + 跑两个测试”的 Demo，而是一个**可展示、可运行、可复刻的测试开发作品集**：

- 有一套**被测系统**（SUT），有真实接口和数据；
- 有**分层自动化测试**（后端冒烟 + 接口黑盒 + 工具契约测试）；
- 有一个**测试控制台/平台**（Vue 前端）；
- 有一个**对标行业工具的复刻**（模块 03：Hoppscotch 风格 API 工作台）；
- 有**项目报告、验收截图、版本归档、CI**。

一句话：它证明的不是“我会写代码”，而是“我能搭系统、能设计测试、能做工具、能留下证据”。

### 0.2 “复刻”是什么意思

本项目要求每个模块先找 GitHub 上同主题 **star 最高**的项目，然后**理解它的核心机制，自己重写一个可运行的子集**。

这叫 **clean-room 复刻**：看文档、看行为、看公开接口，然后自己实现；不直接复制源码。这样做的好处：

1. 能真正理解原理，面试能讲；
2. 避开了“fork 一个仓库就说是自己做的”的简历风险；
3. 许可证上更安全（我们仍然会记录 license）。

### 0.3 8 个模块和参考项目

| 模块 | 参考项目（2026-11-02 star） | 本次状态 |
|---|---|---|
| 01 方法论 | atinfo/awesome-test-automation（7,208） | 规则与知识地图已记录 |
| 02 Python 测试开发 | pytest-dev/pytest（14,661） | 下一步 |
| 03 接口自动化 | hoppscotch/hoppscotch（80,721） | **v0.1 已复刻** |
| 04 Web 自动化 | microsoft/playwright（99,087） | 待开始 |
| 05 App 自动化 | appium/appium（22,174） | 待开始 |
| 06 性能测试 | grafana/k6（32,102） | 待开始 |
| 07 测试平台 | metersphere/metersphere（13,600） | 控制台雏形 |
| 08 LLM 评测 | confident-ai/deepeval（19,242） | 待开始 |

### 0.4 本次（v0.2.0）到底做了什么

| 序号 | 内容 | 结果 |
|---|---|---|
| 1 | 定目标、规则、验收标准 | CLAUDE.md、模块矩阵 |
| 2 | 建 monorepo、Python 环境、依赖 | `E:\ailearning\ai-qa-lab` |
| 3 | 自建 SUT（FastAPI + SQLite） | 8 个接口（6 业务 + 2 工作台），`/docs` 可看 |
| 4 | 后端冒烟测试 | 6 个用例 |
| 5 | 接口自动化套件 | 22 个黑盒用例 |
| 6 | Vue 控制台 | 6 个页面 |
| 7 | 模块 03 复刻：API 工作台 | 5 类断言 + 集合 + 批量报告 |
| 8 | 工具契约测试 | 5 个用例，全量 33 passed |
| 9 | 证据与 CI | 截图、GitHub Actions |
| 10 | 报告与归档 | 报告站 + v0.2.0 快照 |
| 11 | 部署准备 | Docker/Render/HF 配置（暂缓上云） |

---

## 1. 第一步：定目标和验收标准

### 做了什么

先明确：目标是杭州 30K+ 的测试开发（AI 质量方向）岗位；项目要覆盖 8 个模块；每个模块必须有“可运行代码 + 验收网页 + 原理说明 + 使用步骤 + 效果”。然后写进 `CLAUDE.md` 和 `docs/requirements/`。

### 为什么

如果不先定义“什么算完成”，后面很容易变成堆功能：今天写个页面，明天加个按钮，最后没有一条完整证据链。面试官看的是“你能不能交付”，不是“你写了多少行”。

### 涉及的名词

- **作品集**：用真实项目证明能力，而不只是简历上写“熟悉 pytest”。
- **验收标准**：可检查的完成条件，比如“33 个测试通过、页面能打开、报告有截图”。
- **MVP**：最小可用版本，先做核心闭环，再加功能。
- **clean-room 复刻**：理解后重写，不复制源码。

### 原理

**以终为始**：先定义最终要展示什么，再反推每一步要产出什么。每个产物都能追溯到目标，避免“为了写代码而写代码”。

### 效果

你得到了一张路线图：8 个模块、参考项目、复刻范围、验收标准。后面每一步都在填这张图，而不是盲目开发。

---

## 2. 第二步：搭仓库和环境

### 做了什么

建立 `E:\ailearning\ai-qa-lab`，划分 `apps/sut`、`apps/platform`、`suites/*`、`docs/*`、`scripts`；用 Python 3.11 建 `.venv`；写 `requirements.txt`、`.gitignore`、`README.md`、`CLAUDE.md`；初始化 Git。

### 为什么

1. **可复现**：换一台机器，按命令能跑起来；
2. **隔离**：项目依赖装在 `.venv`，不污染系统 Python；
3. **可回滚**：Git 记录每次改动，出错能退回；
4. **可协作/可展示**：别人能看懂目录结构。

### 涉及的名词

- **monorepo**：一个仓库放多个应用/包（这里是 SUT、平台、测试套件、文档）。
- **虚拟环境（venv）**：项目专用的 Python 环境，依赖互不干扰。
- **依赖（dependency）**：项目用到的第三方库，如 FastAPI、pytest。
- **lockfile**：锁定依赖版本的文件（前端是 `package-lock.json`），保证每次安装一致。
- **Git commit**：一次代码快照；**remote**：远程仓库；**tag**：给某个提交打版本标签。
- **.gitignore**：告诉 Git 哪些文件不提交（`.venv`、`node_modules`、`.env`、数据库文件）。
- **环境变量**：不写死在代码里的配置，如数据库地址、API key。

### 原理

**隔离 + 单一信源 + 版本控制**：

- 依赖隔离，避免“你机器能跑、我机器不能跑”；
- 代码、文档、测试都在一个仓库，避免多份真相；
- 每次改动有提交记录，出问题能定位。

### 效果

一条命令可以建环境、装依赖、启动项目；密钥和虚拟环境不会进 Git；后面所有模块都复用它。

```bash
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 3. 第三步：造一个被测系统（SUT）

### 做了什么

用 FastAPI + SQLAlchemy + SQLite 写了一个“AI 知识库工单系统”：

- `GET /health`：健康检查
- `GET /api/tickets`：工单列表
- `POST /api/tickets`：创建工单
- `GET /api/tickets/{id}`：查询单条
- `PATCH /api/tickets/{id}`：更新状态/优先级
- `POST /api/kb/query`：知识库问答（当前 mock）

### 为什么

**测试必须有被测对象。** 如果只写测试脚本，没有系统，测试就是空中楼阁。自建 SUT 的好处：

1. 数据可控，能主动造正常/异常场景；
2. 后续 API、Web、App、性能、Agent 测试都能围绕它展开；
3. 能展示“我不仅能测，还能造一个可测的系统”。

### 涉及的名词

- **SUT（System Under Test）**：被测系统，测试动作作用的对象。
- **API（Application Programming Interface）**：系统对外提供的调用接口；这里是 HTTP + JSON 接口。
- **REST**：一种接口设计风格，用 URL 表示资源，用 HTTP 方法表示动作。我们的接口是 REST 风格，不追求严格 REST。
- **Endpoint（端点）**：一个“方法 + URL”，比如 `POST /api/tickets`。
- **HTTP 方法**：`GET` 查、`POST` 建、`PATCH` 改、`DELETE` 删。
- **HTTP 状态码**：`200` 成功、`201` 已创建、`400` 请求错误、`404` 找不到、`422` 参数校验失败、`500` 服务器错误。
- **JSON**：一种文本数据格式，如 `{"title": "登录失败"}`。
- **CRUD**：Create/Read/Update/Delete，增删改查；本项目实现了 C/R/U，没做 D。
- **ORM**：对象关系映射，用 Python 类操作数据库表，而不是手写 SQL。
- **Schema（模式）**：数据的结构和约束；这里用 Pydantic 定义请求/响应格式。
- **SQLite**：一个文件型轻量数据库，适合本地演示，不需要单独装数据库服务。
- **OpenAPI**：描述 API 的机器可读文档；FastAPI 自动生成 `/openapi.json` 和 `/docs` 页面。

### 原理

一次请求的路径：

```
浏览器/测试脚本
  → HTTP 请求（方法 + URL + Headers + Body）
  → FastAPI 路由匹配
  → Pydantic 校验参数
  → SQLAlchemy 读写 SQLite
  → 组装 JSON 响应
  → 返回状态码 + Body
```

`/health` 为什么先做？因为它是“系统活着”的最小契约：CI、负载均衡、监控都靠它判断服务是否可用。

### 效果

打开 `http://127.0.0.1:8000/docs` 能看到可交互的 API 文档；6 个后端测试通过；后续所有测试和页面都围绕这套接口。

---

## 4. 第四步：写后端冒烟测试

### 做了什么

用 pytest + FastAPI `TestClient` 写了 6 个用例：健康检查、创建工单、列表、查询、404、参数校验。

### 为什么

先确认“系统基本能用”，再往上叠接口自动化、UI 和工具。冒烟测试跑得最快，能在几秒内告诉你核心链路有没有断。

### 涉及的名词

- **冒烟测试（Smoke Test）**：只测最关键路径，确认系统“没冒烟”。
- **单元测试**：测一个函数/模块，依赖尽量隔离。
- **集成测试**：测多个组件一起工作，比如 API + 数据库。
- **Fixture**：测试前的准备/测试后的清理，pytest 用 `@pytest.fixture` 复用。
- **断言（Assertion）**：把“实际结果”和“预期结果”比较，比如 `assert response.status_code == 200`。
- **测试隔离**：每个测试不依赖别的测试，也不污染共享数据。
- **内存数据库**：测试用 `sqlite:///:memory:`，跑完即销毁，不污染开发库。

### 原理

**Arrange-Act-Assert（准备-执行-断言）**：

1. 准备数据和客户端；
2. 调用接口；
3. 断言状态码和响应内容。

测试配置通过 `conftest.py` 把数据库指向内存，保证每次测试从干净状态开始。

### 效果

`pytest` 一条命令跑完，6 passed。你有了第一层“质量守门员”。

---

## 5. 第五步：接口自动化（黑盒测试）

### 做了什么

新建 `suites/api`，用 pytest + requests 写黑盒接口测试，自动拉起/停止 SUT，覆盖：

- 健康检查、OpenAPI 契约；
- 工单创建、列表、查询、更新；
- 异常：404、422、空标题、超长字段、非法优先级、非法状态；
- 知识库 mock 接口。

共 22 个用例。

### 为什么

接口测试是投入产出比最高的一层：比 UI 快、比单元测试更接近真实业务。企业里大量回归靠接口自动化。

### 涉及的名词

- **黑盒测试**：不关心内部实现，只通过接口输入/输出验证行为。
- **契约测试**：确认接口的字段、状态码、结构符合约定。
- **正向测试**：输入合法，期望成功。
- **负向测试**：输入非法，期望被拒绝（4xx）。
- **边界值**：长度/范围的两端，比如标题 200 和 201 个字符。
- **测试数据**：用例的输入；这里用随机后缀避免多次运行冲突。
- **测试隔离**：每个用例独立，顺序不影响结果。
- **Session Fixture**：整个测试会话只启动一次 SUT，提高速度。
- **Test Runner**：执行测试并汇总结果的工具，这里用 pytest。

### 原理

接口测试的本质是**对协议的断言**：

```
构造请求 → 发送 HTTP → 拿到响应 → 断言 status / headers / body / schema
```

自动启动 SUT 是为了让测试“一条命令可复现”，不依赖你手动先开服务。

### 效果

22 个用例约 1.5 秒跑完；正常和异常路径都有覆盖；这部分可以直接写进简历。

---

## 6. 第六步：做 Vue 控制台

### 做了什么

用 Vue 3 + Vite + Pinia + Vue Router + ECharts 做了 6 个页面：

- 仪表盘：统计卡片 + 状态环形图 + 最近工单；
- 工单管理：搜索、筛选、新建、改状态/优先级；
- 知识库问答：提问、耗时、历史；
- API 工作台：后面模块 03 的复刻；
- 项目报告：你现在看的这份内容；
- 模块验收：8 个模块的参考项目与状态。

### 为什么

1. 作品集需要“看得见”的成果；
2. 测试开发/平台开发岗位需要前端能力；
3. 你测 UI 之前，得先理解 UI 是怎么被构建出来的。

### 涉及的名词

- **SPA（单页应用）**：页面不整页刷新，由前端路由切换视图。
- **组件（Component）**：可复用的 UI 单元，如按钮、表格、卡片。
- **路由（Router）**：URL 和页面的映射；这里用 hash 路由（`#/tickets`），静态托管不需要服务端 fallback。
- **状态管理（Pinia）**：把工单列表、加载状态等集中管理，多个页面共享。
- **Vite**：前端构建工具，开发时热更新，生产时打包。
- **构建（Build）**：把 Vue 源码编译成浏览器能直接运行的 HTML/CSS/JS。
- **同源（Same-origin）**：协议、域名、端口都相同；同源请求不受 CORS 限制。
- **静态托管**：只发 HTML/CSS/JS，不需要应用服务器。

### 原理

```
组件渲染 → 读取 Pinia 状态 → 调用 /api → 更新状态 → 重新渲染
```

生产构建后，FastAPI 把 `dist/` 挂到 `/ui`，所以一个服务同时提供 API 和页面，验收只需要一个地址。

### 效果

本地打开 `http://127.0.0.1:8000/ui/` 能看到完整控制台，截图已归档。

---

## 7. 第七步：模块 03 复刻——API 工作台

### 做了什么

以 Hoppscotch（80,721★，MIT）为参考，复刻了一个 API 工作台：

- 请求构建：方法、URL、Headers、Body；
- 环境变量：`{{baseUrl}}` 替换；
- 后端代理发送：FastAPI + httpx；
- 5 类断言：状态码、最大耗时、文本包含、JSON 路径存在/等于；
- 集合保存、加载、删除（localStorage）；
- 批量运行与 PASS/FAIL 报告；
- 历史记录。

### 为什么选 Hoppscotch

它是 API 开发/测试一体化平台里 star 最高的开源项目，核心模型（请求、集合、环境、断言、运行器）和模块 03 完全对口。复刻它的核心闭环，比“自己随便写个请求页面”更有说服力。

### 涉及的名词

- **API 客户端**：Postman/Hoppscotch 这类工具，用来发请求、看响应、做断言。
- **集合（Collection）**：一组请求的集合，可以批量运行。
- **环境变量**：不同环境（本地/测试/生产）用不同的 baseUrl，不在代码里写死。
- **CORS**：浏览器的同源策略限制；前端直接请求不同域名的 API 会被拦截。
- **反向代理**：由后端代替前端发请求，绕过浏览器 CORS，统一超时和鉴权。
- **断言**：对响应做检查，例如“状态码必须是 200”“JSON 的 `$.status` 必须等于 ok”。
- **JSONPath**：从 JSON 里取值的路径表达式，如 `$.data[0].id`。
- **测试运行器（Runner）**：按顺序执行一组请求，汇总每条的结果。
- **SSRF**：服务端请求伪造，攻击者诱导服务器访问内网地址；我们的代理只限制协议和云元数据地址，属于本地工具级别，不是完整防护。
- **localStorage**：浏览器本地键值存储，关掉浏览器数据还在。

### 原理

```
Vue 请求编辑器
  → POST /api/workbench/send（后端代理）
  → httpx 发真实请求到目标服务
  → 后端执行断言
  → 返回 status / elapsed_ms / failures / body
  → 前端展示 PASS/FAIL
```

为什么断言放在后端？因为批量运行时需要统一、可重复的判定逻辑，不能依赖浏览器。

### 效果

单请求实测 PASS；批量运行 2/2 PASS；新增 5 个工作台契约测试；全量 33 passed。截图和验收说明已归档。

---

## 7.5 模块 02 复刻：迷你 pytest

### 做了什么

- 在 `libs/minipytest` 里自己写了一个 pytest-like 测试执行器；
- 支持用例收集、fixture、参数化、marker、断言内省、失败重试、JSON/HTML 报告；
- 用真实 pytest 写了 33 个元测试，证明引擎行为正确；
- 用迷你 pytest 跑了 20 个验收演示和 9 个故意失败演示；
- 生成了一份断网也能打开的 HTML 报告，并挂到 SUT 控制台的 `/portfolio` 下。

### 为什么

面试官问“你熟悉 pytest 吗”，如果你只能回答“会写 `@pytest.mark.parametrize`”，那只是会用工具。能解释“用例怎么被发现、fixture 怎么注入、参数化怎么展开、失败位置怎么定位、报告怎么生成”，才说明你理解测试框架。

这个模块还有一个实际作用：后续 Web、App、性能、LLM 评测模块都要复用同一套测试基础设施。先把 runner 做出来，后面不用重复造轮子。

### 涉及的名词

- **收集（collection）**：框架扫描目录，找出哪些函数是测试用例。
- **fixture**：测试前准备数据、测试后清理资源的函数。
- **作用域（scope）**：fixture 多久重建一次，function 每条用例、module 每个文件、session 整轮。
- **参数化（parametrize）**：一份测试代码，喂多组输入，生成多条用例。
- **marker**：给用例打标签，比如 `smoke`、`skip`、`xfail`、`retry`。
- **断言内省**：断言失败时，框架能告诉你期望值、实际值和差异。
- **retry**：失败后自动重跑，用来识别不稳定用例（flaky）。
- **node ID**：每条用例的唯一名字，例如 `test_api.py::test_login[admin]`。

### 原理

#### 1. 收集

框架从你给的路径开始，找 `test_*.py`。打开文件后：

- 模块里名字以 `test_` 开头的函数，收；
- 名字以 `Test` 开头的类，类里 `test_` 开头的方法，收；
- 其他函数（helper、fixture）不收。

收集时按源码行号排序，保证执行顺序和文件里写的一致。

#### 2. fixture

测试函数的参数名就是 fixture 名：

```python
@fixture(scope="session")
def api():
    client = make_client()
    yield client
    client.close()

def test_health(api):
    assert api.get("/health").status_code == 200
```

执行器看到 `test_health` 需要 `api`，就去 fixture 表里找 `api`，调用它。`yield` 前是准备，`yield` 后是清理。

作用域决定复用：

- `function`：每条用例都新建，最干净，也最慢；
- `module`：同一个文件内共用；
- `session`：整轮测试共用，适合启动一次服务。

#### 3. 参数化

```python
@parametrize("role", ["admin", "viewer"])
@parametrize("status", ["open", "closed"])
def test_permission(role, status):
    ...
```

收集器把两组值做笛卡尔积，生成 4 条 case：

```
test_permission[admin-open]
test_permission[admin-closed]
test_permission[viewer-open]
test_permission[viewer-closed]
```

每条 case 单独执行、单独记结果。

#### 4. marker

`@mark.skip` 直接跳过，不跑 fixture；`@mark.xfail` 表示“我知道它会失败”，失败记 xfailed，意外通过记 xpassed；`@mark.retry(2)` 表示最多跑两次。

`-m "smoke and not slow"` 是一个小型表达式，执行器只跑符合条件的 case。

#### 5. 断言内省

普通 `assert 1 == 2` 失败时只告诉你“断言失败”。迷你 pytest 用链式断言：

```python
assert_that({"status": "closed"}).is_equal_to({"status": "open"})
```

失败时输出：

```
expected: {'status': 'open'}
actual:   {'status': 'closed'}
--- expected
+++ actual
-{'status': 'open'}
+{'status': 'closed'}
```

还会定位到测试文件的具体行号，而不是框架内部。

#### 6. 重试

执行器记录每次尝试：

- 第 1 次失败，记 attempt 1；
- 第 2 次通过，最终状态 passed，但标记 retried / flaky。

这样你不会因为一次网络抖动就误判，也能在报告里看到“这条用例曾经失败过”。

#### 7. 报告

JSON 适合机器读，HTML 适合人看。HTML 是单文件，CSS/JS 都内嵌，不依赖 CDN，断网也能打开。报告里有 summary、失败详情、断言 diff、每次 attempt、fixture 耗时。

### 效果

- 真实 pytest：66 passed（33 现有 + 33 框架元测试）；
- 迷你 pytest：20 cases，17 passed、1 skipped、1 xfailed、1 xpassed，exit 0；
- 故意失败演示：9 cases，7 failed、2 errors，exit 1；
- 报告：`docs/portfolio/module-02-minipytest-report.html`；
- 控制台入口：`/portfolio/module-02-minipytest-report.html`。

### 关键文件

```
libs/minipytest/collect.py     收集、参数化展开
libs/minipytest/fixtures.py    fixture 依赖注入
libs/minipytest/runner.py      执行、重试、退出码
libs/minipytest/assertions.py  断言与 diff
libs/minipytest/reporting.py   JSON / HTML
libs/minipytest/cli.py         命令行入口
```

---

## 7.6 模块 04 复刻：迷你 Playwright

### 做了什么

- 在 `libs/miniplaywright` 里自己写了一个浏览器自动化库；
- 用 Chrome DevTools Protocol 驱动本机 Edge/Chrome；
- 支持启动、导航、CSS 选择器、点击、填值、自动等待、断言、截图；
- 用真实 pytest 写了 6 个元测试；
- 用迷你 pytest 跑了 5 个 SUT UI 用例，真实创建了一条工单。

### 为什么

面试里说“会 Playwright”，如果只会 `page.click()`，说不出浏览器和测试脚本之间怎么通信，底层还是空的。自己用 CDP 驱动一遍，就能解释“浏览器怎么被控制、元素怎么定位、自动等待在等什么”。

### 涉及的名词

- **CDP**：Chrome DevTools Protocol，浏览器暴露的调试协议。
- **remote debugging port**：启动浏览器时开的调试端口。
- **WebSocket**：CDP 的命令通道，发 JSON，收 JSON。
- **选择器**：用 CSS 语法定位页面元素。
- **自动等待**：元素没出现就反复查，直到超时。
- **headless**：无界面浏览器，适合 CI。

### 原理

#### 1. 启动浏览器

给 Edge/Chrome 加参数：

```
--remote-debugging-port=<端口>
--remote-allow-origins=*
--headless=new
```

浏览器启动后，本地会多一个 HTTP 服务。

#### 2. 找到页面

请求 `GET http://127.0.0.1:<端口>/json/list`，返回当前可调试的页面，里面有 `webSocketDebuggerUrl`。

#### 3. 连接 CDP

用 WebSocket 连上去，发送：

```json
{"id": 1, "method": "Page.navigate", "params": {"url": "http://..."}}
```

浏览器返回：

```json
{"id": 1, "result": {"frameId": "..."}}
```

#### 4. 定位和操作

`Runtime.evaluate` 可以在页面里执行 JavaScript：

```js
document.querySelector("#btn").click()
```

填值不能只改 `value`，还要派发 `input` 和 `change` 事件，Vue 的 `v-model` 才会更新。

#### 5. 自动等待

页面是异步渲染的。`expect(locator).to_have_text("工单管理")` 会在超时时间内反复查，直到文本出现或超时。这样不会因为页面慢半拍就假失败。

#### 6. 截图和报告

`Page.captureScreenshot` 返回 base64 PNG，写到文件。测试结果交给迷你 pytest 生成 JSON/HTML 报告。

### 效果

- 6 个框架元测试通过；
- 5 个 SUT UI 用例通过；
- 真实创建工单，截图在 `docs/portfolio/screenshots/module-04-tickets.png`；
- 报告：`docs/portfolio/module-04-playwright-report.html`。

### 关键文件

```
libs/miniplaywright/browser.py    启动浏览器、找 page target
libs/miniplaywright/cdp.py        CDP WebSocket 客户端
libs/miniplaywright/page.py       Page / Locator / 截图
libs/miniplaywright/assertions.py expect 断言
libs/miniplaywright/demo/         SUT UI 用例
```

---

## 7.7 模块 05 复刻：迷你 Appium

### 做了什么

- 在 `libs/miniappium` 里自己写了一个 Android UI 自动化客户端；
- 用 ADB + UIAutomator 驱动 Android 模拟器；
- 支持设备发现、启动 App、元素定位、点击、滑动、输入、返回、截图；
- 用真实 pytest 写了 5 个元测试；
- 用迷你 pytest 跑了 3 个 Settings 演示用例。

### 为什么

面试里说“会 Appium”，如果只会 `driver.find_element()`，说不出 Appium 底层怎么和手机通信，还是只会用工具。自己用 ADB/UIAutomator 驱动一遍，就能解释“设备怎么连、控件树怎么来、点击坐标怎么算、等待在等什么”。

### 涉及的名词

- **ADB**：Android Debug Bridge，电脑和 Android 设备之间的命令通道。
- **UIAutomator**：Android 自带的 UI 控件树导出工具。
- **resource-id**：控件 ID，最稳的定位方式。
- **content-desc**：无障碍描述，图标按钮常用。
- **bounds**：控件在屏幕上的坐标范围。
- **headless 模拟器**：没有窗口的模拟器，适合自动化。

### 原理

#### 1. 连接设备

`adb devices` 列出已连接设备。模拟器启动后通常叫 `emulator-5554`。

#### 2. 启动 App

```bash
adb shell am force-stop com.android.settings
adb shell am start -a android.settings.SETTINGS
```

先强制停止，避免 Settings 恢复到上次打开的页面。

#### 3. 导出控件树

```bash
adb shell uiautomator dump /sdcard/window.xml
adb exec-out cat /sdcard/window.xml
```

XML 里每个节点有 `text`、`resource-id`、`content-desc`、`bounds`。

#### 4. 定位和点击

按 text 或 resource-id 找到节点，取 `bounds` 中心，`adb shell input tap x y`。

#### 5. 自动等待

页面跳转有动画。`wait_for(text="Internet")` 会反复 dump + 查找，直到出现或超时。

#### 6. 截图

`adb exec-out screencap -p` 返回 PNG 二进制，写到文件。

### 效果

- 5 个框架元测试通过；
- 3 个 Settings 演示通过；
- 真实打开 Settings、点击 Network & internet、返回首页；
- 截图：`docs/portfolio/screenshots/module-05-settings.png`；
- 报告：`docs/portfolio/module-05-appium-report.html`。

### 关键文件

```
libs/miniappium/device.py     ADB、UIAutomator dump、定位、点击、截图
libs/miniappium/assertions.py expect 断言
libs/miniappium/demo/         Settings 演示用例
```

---

## 7.8 模块 06 复刻：迷你压测引擎

### 做了什么

- 在 `libs/miniload` 里自己写了一个压测引擎；
- 支持常量 VU、ramp-up、P50/P95/P99、RPS、错误率；
- 支持阈值判定：P95、错误率、最小 RPS；
- 生成 JSON 和离线 HTML 报告；
- 用真实 pytest 写了 5 个元测试；
- 对 SUT 的 `/health` 做了一次 20 VU、5 秒的压测。

### 为什么

面试里说“会压测”，如果只会说“我跑了 100 并发”，没有 P95、错误率、阈值判断，等于没有结论。压测的价值是拿数据回答“能不能上线”。

### 涉及的名词

- **VU**：虚拟用户，压测里的并发单位。
- **RPS**：每秒请求数，吞吐量。
- **P50/P95/P99**：50%/95%/99% 的请求比这个值快。
- **ramp-up**：并发用户逐步启动的时间。
- **阈值**：P95、错误率、最小 RPS 的通过线。
- **错误率**：失败请求 / 总请求。

### 原理

#### 1. 并发

每个 VU 一个线程，线程里循环发请求，直到结束时间。

#### 2. 阶梯启动

VU 不是同一瞬间启动，而是按序号错开。这样更接近真实用户逐步进入。

#### 3. 采集

每次请求记录：

- 开始时间；
- 结束时间；
- 耗时；
- 状态码；
- 异常信息。

#### 4. 计算

- RPS = 总请求 / 实际耗时；
- 错误率 = 失败数 / 总数；
- 百分位：把所有耗时排序，取对应位置。

#### 5. 阈值

任何一条不满足就 FAIL：

- P95 是否超过 500ms；
- 错误率是否超过 1%；
- RPS 是否低于 10。

#### 6. 报告

HTML 里放 summary、百分位、延迟分布、状态码、错误 Top N。单文件，断网可看。

### 效果

- 5 个框架元测试通过；
- SUT `/health`：8239 次请求，1371.2 RPS，P95 21.11ms，错误率 0.00%，PASS；
- 报告：`docs/portfolio/module-06-load-report.html`；
- 截图：`docs/portfolio/screenshots/module-06-load-report.png`。

### 关键文件

```
libs/miniload/engine.py     VU 线程、ramp-up、百分位、阈值
libs/miniload/reporting.py  JSON + 离线 HTML
libs/miniload/cli.py        命令行入口
libs/miniload/demo/         启动 SUT、压测、生成报告
```

---

## 8. 第八步：把测试跑成“证据”

### 做了什么

- 用 pytest 跑全量 33 个测试；
- 用无头 Chrome 截图验收页面；
- 配置 GitHub Actions，每次 push 跑 pytest；
- 把截图、报告、验收说明写进仓库。

### 为什么

简历和面试需要**证据**，不是口头说“我做了”。CI 还能防止你改坏已有功能。

### 涉及的名词

- **CI（持续集成）**：每次提交自动构建/跑测试，尽早发现问题。
- **GitHub Actions**：GitHub 的 CI 服务；`workflow` 是配置文件。
- **Workflow**：定义“什么时候、在什么环境、跑什么命令”的 YAML。
- **无头浏览器（Headless Chrome）**：没有界面的 Chrome，用于自动截图/自动化测试。
- **Artifact**：CI 产出的文件，如测试报告、截图。
- **回归测试**：改代码后重跑旧测试，确认没把旧功能改坏。

### 原理

```
push 代码 → GitHub Actions 启动 Ubuntu → 安装依赖 → 跑 pytest → 记录成功/失败
```

### 效果

GitHub 上能看到 CI 记录；本地 33 passed；验收截图可追溯。

> 注意：当前 CI 只跑后端测试，还没有把 `suites/api` 和前端构建加进去；这是下一步可以补的。

---

## 9. 第九步：报告与归档

### 做了什么

- 最新报告：`docs/index.html` 和 Vue `/ui/#/report`；
- 日报：`docs/progress/YYYY-MM-DD.md`；
- 里程碑快照：`docs/reports/YYYY-MM-DD-vX.Y.Z/`；
- 归档索引：`docs/reports/index.html`；
- 归档脚本：`scripts/archive_report.py`；
- Git tag：`v0.2.0`、`v0.2.0-archive`。

### 为什么

代码每天变，如果报告也每天覆盖，历史就丢了；如果每天生成一个新报告，又会变成噪声。所以：

- 日报记录“过程”；
- 里程碑快照记录“阶段性成果”；
- 根报告永远是最新状态；
- 快照不可变，面试时能回看“我当时做到了什么”。

### 涉及的名词

- **快照（Snapshot）**：某一时刻的完整副本。
- **不可变（Immutable）**：归档后不再修改，保证可信。
- **语义化版本（SemVer）**：`主.次.补`，模块完成升次版本，修复升补丁。
- **Git tag**：给某个提交起一个版本名，如 `v0.2.0`。
- **里程碑（Milestone）**：一个阶段目标，如“完成模块 03”。
- **Changelog**：变更记录，说明每个版本改了什么。

### 原理

**单一信源 + 自动生成 + 不可变归档**：报告从当前仓库生成快照，脚本复制截图、改写路径、写 `metrics.json`，再生成索引；历史快照只读。

### 效果

公网可访问：

- 最新报告：https://shenle2019.github.io/ai-qa-lab/
- 归档索引：https://shenle2019.github.io/ai-qa-lab/reports/
- v0.2.0 快照：https://shenle2019.github.io/ai-qa-lab/reports/2026-11-02-v0.2.0/

---

## 10. 第十步：本地与远端部署

### 做了什么

- 本地：FastAPI 同时提供 `/api` 和 `/ui`，一条命令启动；
- 容器：写 `Dockerfile`，Node 构建前端，Python 跑后端；
- Render：`render.yaml`；
- Hugging Face Spaces：`deploy/huggingface/`；
- 决策：**先本地开发，8 个模块全部完成后再上云**。

### 为什么

GitHub Pages 只能托管静态文件，不能运行 Python 后端；完整系统需要容器平台。现在上云会打断学习节奏，所以暂缓。

### 涉及的名词

- **Docker**：把应用和依赖打包成镜像，保证环境一致。
- **镜像（Image）/容器（Container）**：镜像是模板，容器是运行实例。
- **端口（Port）**：服务监听的入口，如 8000、7860。
- **PaaS**：平台即服务，如 Render、Hugging Face Spaces，帮你托管应用。
- **冷启动（Cold Start）**：免费实例休眠后，第一次访问要等它启动。
- **临时存储（Ephemeral Storage）**：重启后数据丢失；SQLite 在免费平台就是这个特性。

### 原理

```
Docker 构建：Node 构建前端 → 复制 dist → Python 安装依赖 → 启动 uvicorn
运行：浏览器 → 容器 8000/7860 → FastAPI → SQLite
```

### 效果

本地完整可用；云部署配置保留，后续直接使用。

---

## 11. 术语速查表

| 名词 | 一句话解释 |
|---|---|
| SUT | 被测系统 |
| API | 系统对外的调用接口 |
| REST | 用 URL + HTTP 方法表达资源的风格 |
| Endpoint | 方法 + URL |
| 状态码 | 200 成功、201 创建、400 请求错、404 找不到、422 校验失败、500 服务错 |
| JSON | 文本数据格式 |
| CRUD | 增删改查 |
| ORM | 用对象操作数据库 |
| Schema | 数据结构与约束 |
| OpenAPI | API 的机器可读文档 |
| 冒烟测试 | 只测最关键路径 |
| 单元测试 | 测单个函数/模块 |
| 集成测试 | 测多个组件一起工作 |
| E2E | 端到端，从用户界面走完整流程 |
| 黑盒测试 | 只看输入输出，不看内部实现 |
| 契约测试 | 验证接口结构和行为约定 |
| 正向/负向测试 | 合法输入期望成功 / 非法输入期望失败 |
| 边界值 | 取值范围的两端 |
| Fixture | 测试准备/清理 |
| 断言 | 实际结果 vs 预期结果 |
| 测试隔离 | 用例互不影响 |
| Flaky Test | 时好时坏的测试 |
| 覆盖率 | 测试执行到的代码比例 |
| 测试金字塔 | 多单元、少接口、更少 E2E |
| CI | 每次提交自动跑测试 |
| CD | 自动交付/部署 |
| CORS | 浏览器跨域限制 |
| 反向代理 | 后端代发请求 |
| JSONPath | 从 JSON 取值的路径 |
| SSRF | 服务端请求伪造 |
| SPA | 单页应用 |
| 组件 | 可复用 UI 单元 |
| 路由 | URL 到页面的映射 |
| 状态管理 | 集中管理共享数据 |
| 构建 | 把源码编译成可部署文件 |
| 同源 | 协议/域名/端口一致 |
| 容器 | 打包后的运行实例 |
| PaaS | 托管应用的平台 |
| 冷启动 | 休眠后首次访问的等待 |
| 语义化版本 | 主.次.补 |
| 快照 | 某一刻的完整副本 |
| RAG | 检索增强生成，先查资料再让模型回答 |
| LLM 评测 | 用数据集和指标评估大模型输出 |
| 虚拟用户（VU） | 压测里的并发用户 |
| P95/P99 | 95%/99% 请求的耗时上限 |

---

## 12. 简历上怎么写（只写真实做过的）

### 可以写的

- 独立搭建可运行的 AI 工单/知识库 SUT：FastAPI + SQLAlchemy + SQLite，8 个 HTTP 接口（6 个业务 + 2 个工作台），自动生成 OpenAPI 文档。
- 设计并实现 66 个真实 pytest 用例：33 个业务/接口契约 + 33 个迷你 pytest 框架元测试，覆盖 404/422/边界/非法枚举。
- clean-room 复刻 pytest 核心：收集、fixture、参数化、marker、断言内省、重试、JSON/HTML 报告；20 个演示用例。
- 自研 CDP Web 自动化：启动 Edge/Chrome、选择器、自动等待、断言、截图；6 个元测试 + 5 个 SUT UI 用例。
- 自研 ADB/UIAutomator Android 自动化：设备发现、元素定位、点击、等待、截图；5 个元测试 + 3 个 Settings 用例。
- 自研压测引擎：VU 并发、ramp-up、P95/P99、错误率、阈值判定、离线报告；8239 请求，1371 RPS。
- 使用 Vue 3 + Vite + Pinia + Router + ECharts 构建 6 页测试控制台，覆盖仪表盘、工单、知识库、API 工作台、报告与模块验收。
- clean-room 复刻 Hoppscotch 核心 API 工作台：请求构建、环境变量、5 类断言、集合保存、批量运行与报告；新增 5 个契约测试。
- 建立“日报 + 里程碑快照”的报告归档机制，Git tag 与静态站点可追溯。

### 面试可能追问

1. 为什么先做接口测试，而不是 UI 自动化？
   - 接口快、稳定、ROI 高；UI 慢且易碎，适合覆盖关键路径。
2. 测试数据为什么要随机后缀？
   - 避免多次运行数据冲突，保证可重复。
3. 为什么测试用内存数据库？
   - 隔离、快、不污染开发数据。
4. 为什么 API 工作台要用后端代理？
   - 绕过浏览器 CORS，统一超时和断言。
5. 断言为什么放后端？
   - 批量运行需要统一、可重复的判定。
6. 这个项目最大的边界是什么？
   - 没做登录/RBAC、真实 RAG、Playwright/Appium/性能/LLM 评测；SQLite 只适合演示。

### 不要写的

- 不要写“精通 Playwright/Appium/k6/LLM 评测”——这些模块还没做。
- 不要写“生产级高可用”——当前是本地演示。
- 不要写“从零自研所有工具”——API 工作台是核心闭环复刻，不是完整 Hoppscotch。

---

## 13. 下一步怎么学

模块 02、04、05、06 已完成。下一项是**模块 07：测试平台（项目/用例/计划/执行/缺陷/报表）**。

先把模块 02 的七个机制过一遍：

1. **用例收集**：框架怎么找到 `test_*.py` 里的函数；
2. **fixture**：怎么准备/清理依赖，怎么按作用域复用；
3. **参数化**：一组输入怎么生成多条用例；
4. **marker**：skip / xfail / retry / tag 怎么生效；
5. **断言内省**：失败时怎么给出 expected / actual / diff；
6. **失败重试**：怎么记录 attempt，怎么识别 flaky；
7. **报告**：JSON 和离线 HTML 怎么生成。

学完这些，你就能解释“为什么 pytest 能成为 Python 测试事实标准”，也能把同样的思路迁移到 Web、App、性能测试。

每天的节奏固定为：

```
读一点 → 写一点 → 跑测试 → 讲清楚 → 归档
```

每完成一项，必须能回答：**做了什么、为什么、名词、原理、效果**。答不出来，就还没学会。

---

## 14. 自测题

1. SUT 是什么？为什么测试前要先有 SUT？
2. 冒烟测试、接口测试、E2E 的区别是什么？
3. 为什么测试库要用临时/内存数据库？
4. 黑盒测试和契约测试分别关注什么？
5. 422 和 404 分别代表什么？各举一个本项目例子。
6. 为什么 API 工作台要经过 FastAPI 代理，而不是浏览器直接发？
7. JSONPath 断言解决了什么问题？
8. 为什么要做测试数据隔离？随机后缀有什么用？
9. CI 在什么时机跑？它解决了什么问题？
10. 报告归档为什么要“日报 + 里程碑快照”两层？
11. fixture 的 function / module / session 作用域分别什么时候创建、什么时候销毁？
12. 参数化为什么要先生成 case 再执行？一条 case 的 node ID 由什么组成？
13. 断言内省和普通 `assert` 的区别是什么？为什么失败位置要跳过框架自身文件？
14. CDP 是什么？测试脚本怎么通过它控制浏览器？
15. 自动等待解决什么问题？为什么不能页面一打开就断言？
16. ADB 和 UIAutomator 分别负责什么？控件树里的 bounds 怎么变成点击坐标？
17. 为什么移动端自动化要先 `force-stop` 再启动 App？
18. VU、RPS、P95 分别是什么？为什么平均值不够？
19. 压测阈值应该怎么定？P95 和错误率哪个优先？

如果这 19 题你能用自己的话答出来，这个项目就可以写进简历并接受面试追问了。

---

## 15. 五个常见问题（2026-11-03）

### 15.1 学习页标题为什么改了

学习页原来叫 “AI QA Lab”，现在改成 “AI全栈测试开发平台-shenle”。改的是浏览器标签、页面顶部和一级标题，内容不变。控制台侧边栏也同步换成了这个显示名，仓库名 `ai-qa-lab` 没变。

### 15.2 SUT 在哪里，我能看见吗

SUT 就是被测系统，英文 System Under Test，意思是“被测试的那套系统”。

代码在两个地方：

- `apps/sut/backend`：FastAPI + SQLAlchemy + SQLite，负责接口和数据；
- `apps/sut/frontend`：Vue 3，负责页面。

启动后有两个入口：

- `http://127.0.0.1:8000/ui/`：用户界面，能看仪表盘、工单、知识库、API 工作台、报告、模块验收；
- `http://127.0.0.1:8000/docs`：接口文档，能直接点 “Try it out” 发请求。

现在实际有 8 个 HTTP 接口：

1. `GET /health`：健康检查；
2. `GET /api/tickets`：工单列表；
3. `POST /api/tickets`：创建工单；
4. `GET /api/tickets/{ticket_id}`：查单个工单；
5. `PATCH /api/tickets/{ticket_id}`：更新工单状态/优先级；
6. `POST /api/kb/query`：知识库问答（mock）；
7. `POST /api/workbench/send`：API 工作台单请求；
8. `POST /api/workbench/run`：API 工作台批量运行。

之前报告写 7 个，是旧口径，已经更正为 8 个。

### 15.3 模块 03 接口自动化是什么

参考 Hoppscotch（80,721 星），它是一个开源的 Postman 类 API 工具，能发请求、管集合、管环境、做断言。

我们没复制源码，只复刻核心闭环：

- 请求构建：方法、URL、Header、Body；
- 环境变量：把 `{{base_url}}` 换成真实地址；
- 5 种断言：状态码、最大耗时、响应包含、JSON 路径存在、JSON 路径相等；
- 集合保存：把多条请求存起来；
- 批量运行：一次跑一组请求；
- 报告：看哪条通过、哪条失败。

入口是 `/ui/#/workbench`。它解决的是“接口测试不只是发请求”，还要有环境、断言、批量、报告。v0.1 不做 GraphQL、WebSocket、脚本和团队协作。

### 15.4 模块 01 方法论是什么

参考 awesome-test-automation（7,208 星），它是一个测试工具清单和地图，不是可运行程序。

我们用它来确定：

- 8 个模块分别考什么；
- 每个模块选哪个 GitHub 最高星项目做参考；
- 复刻规则：clean-room 重写、完整闭环、验收页、截图、原理说明。

产物是 `docs/requirements/module-matrix.md` 和 `CLAUDE.md` 里的规则。模块 01 排在最后，因为它要把整个项目总结成一张知识地图和选型决策页，不适合一开始就写。

### 15.5 模块 07 测试平台现在有什么

参考 MeterSphere（13,600 星），它是一个持续测试平台，管理项目、用例、计划、执行、缺陷、报表。

现在有 Vue 控制台 + FastAPI 后端，能看仪表盘、工单、知识库、API 工作台、报告、模块验收，所以叫“控制台雏形”。

还缺：

- 测试用例管理；
- 测试计划和执行历史；
- 缺陷跟踪；
- 用户、角色、权限；
- 和 CI 的完整集成。

这些是模块 07 要补的完整闭环，不是现在这一版的交付范围。
