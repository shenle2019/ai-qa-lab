---
name: shenle-test-runner
description: "按计划批量执行用例、汇总结果并产出报告时时使用。支持 runner, 执行, 结果汇总, 报告, 退出码 相关操作；Use when the task involves runner / 执行 / 结果汇总 / 报告 / 退出码."
---

# shenle-test-runner（AIQE 测试计划执行规约）

## 触发词
- "执行 plan / 跑这个测试计划"
- "执行 plan-web-xxx / 跑登录并修改用户昵称"
- "按 AI-自动化测试计划 跑一遍"
- "shenle-test-runner run <plan-id>"

## 前置
- 当前 CWD 必须是 **目标项目根**（含 `AI-自动化测试计划/` `AI-自动化测试编排/` `AI-自动化测试用例/` `AI-动态函数管理/` `AI-环境变量/` 5 个同级目录）
- 项目结构见 `示例项目-读书屋/`
- 执行器可以是本 skill 驱动的 agent、未来的 `shenle-test-runner run` CLI，或任何按本规约实现 runner 的程序

## 执行算法（核心循环）

```
输入：plan_id （目录名，如 plan-web-20260921-224910-登录并修改用户昵称（接口版））

1. 读 plan 元数据
   路径：AI-自动化测试计划/<plan_id>/meta.yaml
   取出：
     environmentKey   → 决定环境变量组
     executionStrategy → serial（目前仅支持串行）
     flows[]          → 要跑的编排列表

2. 初始化变量池
   从 AI-环境变量/<environmentKey>/env_var.yaml 加载全部扁平 key
   例：{api_project_url, test_username, test_password, ...}

3. 串行遍历 flows[]（顺序就是数组顺序，目前无并发）

4. 对当前 flow：
   读 AI-自动化测试编排/<sourceFlowFile>（YAML）
   取出 case_flows[]（一个编排文件理论上可含多个 case_flow，目前按数组顺序串行）
   对当前 case_flow：
     从上往下串行执行 tasks[]（数组顺序即执行顺序）

5. 对当前 task，按 type 分发到对应资源（见下一节）
   执行完后，把 task.output_datas 解析出的变量写回变量池

6. 一个 task 失败：默认中止整个 plan（executionStrategy: serial 下停止后续 flow）
```

## 任务类型 → 资源查找

编排里每个 task 形如：
```yaml
- title: 正常登录
  type: api                       # ← 决定去哪里找
  source_id: a1b2c3d4e5f647899aabbccddeeff001
  input_datas: [...]              # 可选：覆盖用例默认值
  output_datas: [...]             # 可选：从结果里抽变量
```

按 `type` 在以下目录里定位具体文件：

| type | 资源目录 | 匹配方式 |
|------|---------|---------|
| `dynamic-function` | `AI-动态函数管理/<function_type>/` | 匹配 META 头里的 `function_code` == `source_id` |
| `api` | `AI-自动化测试用例/api/<子目录>/` | 匹配 YAML 里的 `case_id` == `source_id` |
| `web` | `AI-自动化测试用例/web/<子目录>/` | 匹配 YAML 里的 `case_id` == `source_id` |
| `app` | `AI-自动化测试用例/app/<子目录>/` | 匹配 YAML 里的 `case_id` == `source_id` |

### dynamic-function 怎么加载

读 `AI-动态函数管理/<function_type>/<source_id>.py`：
- 第一行必须是 `# AIQE_DYNAMIC_FUNCTION_META {json}`，含 `function_code` / `function_type` / `function_name` / `enabled` / `params` / `outputs`
- `enabled: false` → 跳过该函数（[FAIL]）
- META 的 `outputs[]` 里每个 `key` 对应 `execute(**kwargs)` 返回 dict 的 key
- META 的 `outputs[].name` 是给编排/用例引用的 **变量名**
- 调用：`fn.execute(**task_input_kwargs)`，返回 dict → 写回变量池（key → name）

### api / web / app 怎么加载

读 `AI-自动化测试用例/<type>/<group>/<source_id>.yaml`：
- `case_content.request`：原始请求定义（api 用 url/method/headers/body，web/app 类似）
- `input_datas[]`：用例默认入参（name + value）
- `output_datas[]`：声明要从响应里抽什么变量（name + JSONPath / 表达式）
- `expected[]`：断言列表

## 变量解析优先级（**核心**）

**目的**：解决"任务需要数据"和"用例需要数据"两层关系。

当执行 task 时，凡遇到 `{{xxx}}` 占位符（包括 case 内部的 `{{xxx}}` 和 flow 注入的 `{{xxx}}`），按下面顺序找值：

```
1. 变量池（已有值就用）        ← 早期任务 output_datas 写入的变量
2. 当前 task 的 input_datas    ← 编排层注入（最高优先级覆盖）
3. 当前 case 的 input_datas    ← 用例层默认值
4. 环境变量                    ← AI-环境变量/<environmentKey>/env_var.yaml
5. 还找不到 → [FAIL]，报错并指明哪个 {{xxx}} 未绑定
```

**关键规则**：
- **flow task 的 `input_datas` 永远覆盖 case 自己的 `input_datas`**——编排层是"调用方"，用例是"被调方"
- `input_datas[].value` 可以是字面量，也可以是 `{{var}}` 表达式（按上面的链解析）
- task 执行完后，把 `output_datas[].value` 按 JSONPath / 字段名从响应里抽出来，写入变量池

### 表达式语法

| 写法 | 含义 | 示例 |
|------|------|------|
| `{{var}}` | 查变量池 / env | `{{test_username}}` → `'15096268001'` |
| `$.data.token` | JSONPath，从最近一次响应里抽 | `登录Token` 的 value 写这个 |
| 字面量 | 直接用 | `'15096268001'` |

## 端到端例子（示例项目-读书屋）

**MANDATORY — 先读整个文件**：`references/detail.md`（44 行，覆盖这一节的完整细节）。
**不要加载** 其他 references 文件。

## 失败行为
- 任一 task 失败（HTTP 非预期 / 断言失败 / 函数抛异常 / 变量未绑定）：
  - `executionStrategy: serial` → **中止整个 plan**，记录到结果文件
  - 未来如加 `parallel` / `continue-on-error`，再扩展
- 失败也要把已写入的变量、已执行的 task 列表、错误堆栈写进结果报告

## 报告输出
建议写到 `AI-自动化测试计划/<plan_id>/result-<timestamp>.yaml`：
```yaml
plan_id: plan-web-20260921-224910-...
started_at: '...'
finished_at: '...'
status: pass | fail
flows:
  - sourceFlowFile: f7d8a3b2-...yaml
    status: fail
    tasks:
      - title: 生成用户昵称
        status: pass
        duration_ms: 12
      - title: 正常登录
        status: pass
        duration_ms: 234
        response_excerpt: {...}
      - title: 正常更新用户昵称
        status: fail
        error: "expected status 200, got 401"
```

## 常见问题
| 现象 | 原因 | 修复 |
|------|------|------|
| `{{xxx}}` 报未绑定 | 变量名拼错 / env_var 没这个 key | 查 meta.yaml.environmentKey 指向的 env_var.yaml；检查大小写 |
| 用了 case 默认值而不是 flow 注入值 | flow 没写 input_datas，或 name 对不上 case 的 input_datas[].name | name 必须完全一致（中文也要一致） |
| dynamic-function 找不到 | `function_code` 和 `source_id` 不一致；或 `enabled: false` | 打开 .py 看 META 头 |
| 任务之间传值断了 | 前置 task 没声明 output_datas，或 output_datas[].name 拼错 | 名字要和下游 task 的 `{{xxx}}` 完全一致 |
| api case 的 url 渲染成 `{{api_project_url}}/...` 原样 | env_var.yaml 缺这个 key / 没被加载 | 检查 meta.yaml.environmentKey 拼写；env_var 是 YAML 不是 YML |

## 关联
- 生成 plan 的 skill：[shenle-test-plan-generator](../../shenle-test-plan-generator/skill/shenle-test-runner/SKILL.md)（如已建）
- 生成编排的 skill：[shenle-test-flow-builder](../../shenle-test-flow-builder/skill/shenle-test-runner/SKILL.md)（如已建）
- 生成动态函数的 skill：[shenle-dynamic-function-generator](../../shenle-dynamic-function-generator/skill/shenle-dynamic-function-generator/SKILL.md)
- 跑接口的底层工具：[shenle-api-record](../../shenle-api-record/skill/shenle-api-record/SKILL.md)（录制源数据）
- 跑 web/app 用例的底层工具：[shenle-web-cli](../../shenle-web-cli/skill/shenle-web-cli/SKILL.md)、[shenle-android-cli](../../shenle-android-cli/skill/shenle-android-cli/SKILL.md)

## 边界与反例

### 不要做（每条都给原因）

- **NEVER** 不要在失败后继续跑依赖它的后续用例——级联失败会把 1 个真问题放大成 20 条红，掩盖根因
- **NEVER** 不要把环境错误算作用例失败——混淆两者会让通过率失去意义，也让 CI 无法区分该修谁
- **NEVER** 不要用退出码 0 表示“跑完了”——CI 只看退出码，失败必须非 0

### 失败与兜底

| 现象 | 处理 |
| --- | --- |
| 用例全红 | 先看环境连通性与鉴权，不要逐条排查用例 |
| 结果缺失 | 检查报告目录是否被 `.gitignore` 忽略、是否写到了临时目录 |
| 个别用例偶发失败 | 标记 flaky 并单独重试，不要在主干里加长等待 |

### 何时不该用这个 skill

- 只需要读文档或写笔记：走知识库，不要调执行类命令。
- 需要改被测系统的业务数据：先确认数据隔离，再考虑用录制/回放。

## 执行顺序（顺序错了会白跑）

1. 先校验环境，再跑用例。
2. 先跑冒烟集，再跑全量。
3. 先分类失败，再定位根因。
4. 先出报告，再看退出码。

### 再加一条红线

- **NEVER** 不要在没有失败留证时重跑——重跑通过会掩盖真问题，也丢掉现场

### 兜底原则

任何一步失败，先留证（截图、响应体、日志），再重试；没有证据的重跑只会把问题变成偶发。

## 一页速查

| 想做什么 | 怎么做 |
| --- | --- |
| 跑全量 | 按 config 里的 cases 全部执行 |
| 只跑冒烟 | `--only smoke` 先过一遍主路径 |
| 看失败 | 先看分类（环境/数据/断言），再看单条 |
| 出报告 | Markdown 给人看，JUnit 给 CI 看 |

示例：先看真实帮助，再抄参数，别凭记忆写子命令。

```bash
shenle-test-runner --help
```
