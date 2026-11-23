---
name: shenle-dynamic-function-generator
enabled: true
description: "需要为测试平台动态生成可复用函数（数据处理、断言、适配器）时时使用。支持 generator, 动态函数, 代码生成, 适配器, 校验 相关操作；Use when the task involves generator / 动态函数 / 代码生成 / 适配器 / 校验.。触发词：cli / record / runner / adapter / skill。"
---
重点： 请使用中文沟通！！

# AI 动态函数生成器

在 AI 自动化流程执行过程中，直接在工作区创建符合规范的动态函数文件。

> **执行边界：** 本 Skill 负责动态函数文件的生成规范，不负责为测试计划拼接
> shell 命令。`shenle-ai-test-runner` 执行已有 dynamic-function Task 时必须调用
> `run_dynamic_function` 工具；不得使用 Bash、Write/Edit、wrapper、context.json
> 或 bat 文件替代。该工具会自动注入计划环境变量，并通过 stdin 传递 Flow outputs。

---

## 🎯 我该怎么用这个技能？

> **如果你是第一次使用，先读这一节。** 后面的「参考手册」是给需要查细节时用的。

### 三种使用模式

| 模式 | 适用场景 | 引导程度 | 触发方式 |
|------|---------|---------|---------|
| **跳过模式** | 你已经知道 function_type / function_code / 用途三个关键信息 | 0 个问题 | 用户一句话说清楚时自动进入 |
| **快速补全** | 只缺 1-2 个关键信息 | 1-2 个问题 | 启发式判断后自动进入 |
| **场景向导** | 完全没头绪 / 说"我不会做" | 4-6 个问题 | 启发式判断后自动进入 |

### 启发式判断规则（AI 自动执行）

AI 收到请求后会提取三个关键信号：

1. **`function_code` 是否明确** —— 例：`query_user_info`、`http_login`
2. **`function_type` 是否明确** —— 例：`数据库查询`、`通用工具`
3. **用途是否清楚** —— 例："查询用户信息"、"调用登录接口"

判定：

- ✅ **三个都给齐** → 跳过模式，直接生成文件
- ⚠️ **只缺 1-2 个** → 快速补全模式，只问缺失的那 1-2 项
- ❌ **三个都缺 / 用户说"我不会" / 描述模糊** → 场景向导模式，按下面分叉问

### 随时退出

在引导的任何一步，你都可以说：

- **"跳过"** —— 立即按已有信息生成文件，缺失字段留空
- **"我自己来"** —— 退出引导，给你一个空白模板
- **"先这样"** —— 用当前信息先生成，回头再改

---

## 📋 场景向导：5 个常见场景分叉

> 这是「场景向导」模式的具体提问清单。AI 会先问你属于哪个场景，然后只问 4-6 个关键问题。

### 场景 A：数据库查询 🗄️

**典型用途**：连 MySQL 查数据、读配置、批量更新

**AI 会问你**：
1. 库表定位 —— `SQL` 语句还是"按表+条件"自动拼？
2. 连接配置 —— 走环境变量（推荐）还是函数参数传入？
3. 查询/返回哪些字段？
4. 输出是单行、多行、还是聚合结果？

**典型 function_type**：`数据库查询`
**典型 params**：`sql` 或 `table_name`+`where_clause`
**典型 outputs**：`rows` / `count` / `first_row`

**模板示例**：[数据库查询/query_user_info.py](../../AI-动态函数管理/数据库查询/query_user_info.py)

---

### 场景 B：HTTP / API 调用 🌐

**典型用途**：调登录接口、请求第三方 API、文件上传下载

**AI 会问你**：
1. base_url 放哪 —— 环境变量（推荐）还是函数参数？
2. 请求方法 —— GET / POST / 其它？
3. 入参在 query、body、还是 header？
4. 鉴权方式 —— 无 / Bearer Token / Cookie / 自定义 Header？
5. 返回什么 —— 整个响应体、提取特定字段、还是状态码？

**典型 function_type**：`API调用`
**典型 params**：`url` / `method` / `headers` / `body` / `params`
**典型 outputs**：`response` / `status_code` / `extracted_field`

---

### 场景 C：通用工具 🛠️

**典型用途**：生成随机字符串、获取固定配置、日期格式化、文件读取

**AI 会问你**：
1. 输入是什么、要做什么处理？
2. 输出是什么格式（字符串 / 数字 / dict）？
3. 有没有现成的"输入 → 输出"映射逻辑？

**典型 function_type**：`通用工具`
**典型 params**：按业务自定义
**典型 outputs**：按业务自定义

**模板示例**：[通用工具/get_login_info.py](../../AI-动态函数管理/通用工具/get_login_info.py)

---

### 场景 D：数据处理 📊

**典型用途**：JSON 解析、字符串清洗、Excel 读写、数据转换、批量处理

**AI 会问你**：
1. 输入数据格式 —— 字符串 / JSON / 文件路径 / 列表？
2. 处理逻辑 —— 解析 / 清洗 / 转换 / 聚合？
3. 输出去向 —— 返回 dict / 写文件 / 打印？
4. 是否需要 pandas / openpyxl 这类数据处理库？

**典型 function_type**：`数据处理`
**典型 params**：`input_data` / `field_mapping` / `output_format`
**典型 outputs**：`processed_data` / `record_count` / `output_path`

**模板示例**：见下方「参考手册」中的 `parse_json_response.py`

---

### 场景 E：其它 / 不确定 🎲

**AI 会问你**：
1. 一句话描述这个函数要做什么？
2. 输入从哪来 —— 用户传、文件读、还是 _context 里拿？
3. 输出给谁用 —— 下一个节点？日志？写文件？
4. 有没有现成的库可以用？

**典型 function_type**：根据回答新建一个类型目录（如 `邮件通知`、`文件操作`）

---

## 🚪 生成后的回退与修改

生成完文件后：

- **想改字段** —— 直接说"把 outputs 的 xxx 字段类型改成 number"，AI 会重新生成文件
- **想加参数** —— 说"加一个 param：name=timeout，type=number，default=30"
- **想换类型目录** —— AI 会创建新目录并把文件移过去
- **想删除** —— 告诉 AI 删除，它会从文件系统直接删除
- **想看现有函数** —— 让 AI 读 `AI-动态函数管理/{type}/` 目录，列出所有函数

---

# 📚 参考手册（详细规范）

> 下面是和 AIQE 动态函数相关的所有规范细节。生成文件过程中如有疑问，AI 会从这里查证。

## 文件路径规范

```
AI-动态函数管理/{function_type}/{function_code}.py
```

- AI-动态函数管理： 这是统一存放动态函数的文件夹
- `function_type`: 函数类型目录，如 `通用工具`、`数据处理`、`API调用` 等
- `function_code`: 函数代码，同时也是文件名（不含 .py 后缀）

## 文件格式

每个动态函数文件包含两部分：**元数据行** + **代码体**

```python
# AIQE_DYNAMIC_FUNCTION_META {"function_code": "xxx", "function_type": "xxx", ...}

def execute(**kwargs):
    """函数说明..."""
    ...
```

## 元数据格式

元数据是 JSON 格式，放在文件第一行 `# AIQE_DYNAMIC_FUNCTION_META ` 之后：

| 字段          | 类型   | 必填 | 说明                                                          |
| ------------- | ------ | ---- | ------------------------------------------------------------- |
| function_code | string | 是   | 函数代码，字母/下划线开头，数字不能开头。例：`http_request` |
| function_type | string | 是   | 函数类型，对应文件夹名。例：`通用工具`                      |
| function_name | string | 是   | 函数名称，用于展示。例：`HTTP请求`                          |
| description   | string | 否   | 函数说明                                                      |
| enabled       | bool   | 否   | 是否启用，默认 `true`                                       |
| params        | array  | 否   | 输入参数表                                                    |
| outputs       | array  | 否   | 规则输出表                                                    |

### params 元素格式

```json
{"key": "token", "name": "访问令牌", "value_type": "string", "required": true, "default_value": "", "description": "", "test_value": ""}
```

| 字段          | 类型   | 必填 | 说明                      |
| ------------- | ------ | ---- | ------------------------- |
| key           | string | 是   | 参数代码                  |
| name          | string | 否   | 参数名称                  |
| value_type    | string | 否   | 参数类型，默认 `string` |
| required      | bool   | 否   | 是否必填，默认 `false`  |
| default_value | string | 否   | 默认值                    |
| description   | string | 否   | 参数说明                  |
| test_value    | string | 否   | 测试值                    |

> **特殊参数：** `_context` 是系统自动传入的运行时上下文信息 JSON 字符串，无需在 params 中定义即可通过 `kwargs.get("_context", "")` 获取。

### outputs 元素格式

```json
{"key": "result", "name": "执行结果", "value_type": "string", "description": ""}
```

| 字段        | 类型   | 必填 | 说明                      |
| ----------- | ------ | ---- | ------------------------- |
| key         | string | 是   | 输出代码                  |
| name        | string | 否   | 输出名称                  |
| value_type  | string | 否   | 输出类型，默认 `string` |
| description | string | 否   | 输出说明                  |

## 代码体规范

**MANDATORY — 先读整个文件**：`references/detail.md`（287 行，覆盖「代码体规范」的完整细节）。
**不要加载** 其他 references 文件，本任务只需要这一份。

## 创建函数步骤

1. **确定函数类型目录**：根据函数用途选择或创建类型目录（如 `通用工具`）
2. **确定函数代码**：使用有意义的英文名，以下划线分隔，如 `parse_json_response`
3. **编写元数据 JSON**：按照上述格式编写
4. **编写代码体**：实现 `execute(**kwargs)` 函数
5. **添加 CLI 入口（必做）**：在文件末尾追加 `if __name__ == "__main__":` 块，使用上文「推荐模板」里的固定模板，让 `python <脚本> --_context '<json>'` 能直接跑出 JSON 结果。**缺这步 agent 调用会失败**。
6. **写入文件**：创建 `{function_code}.py` 文件

## 示例

**MANDATORY — 先读整个文件**：`references/detail-1.md`（100 行，覆盖「示例」）。
**不要加载** 其他 references 文件。

## 验证规则

- `function_code` 必须是有效的 Python 变量名：`^[A-Za-z_]\w*$`
- 文件第一行必须是 `# AIQE_DYNAMIC_FUNCTION_META {...}`
- 代码体必须包含 `execute(**kwargs)` 函数定义
- 文件末尾必须包含 `if __name__ == "__main__":` 块（否则 agent `python` 调用无输出,直接 FAIL）
- 同一类型目录下不能有重复的 `function_code`
- `params` 和 `outputs` 中的 `key` 不能重复

## 常见错误处理

- 如果类型目录不存在，先创建目录
- 如果函数已存在，应更新而非重复创建
- JSON 元数据中的引号应使用双引号，字符串值需要转义
- 代码体语法错误会导致函数执行失败，写入前应检查

## 边界与反例

### 不要做（每条都给原因）

- **NEVER** 不要让生成结果直接落库执行——未校验的代码一旦执行就是任意代码执行入口
- **NEVER** 不要生成依赖具体环境的常量——换环境即失效，且难以定位
- **NEVER** 不要省略生成后的语法校验——语法错的函数会在运行时才炸，且报错位置与真实原因错位

### 失败与兜底

| 现象 | 处理 |
| --- | --- |
| 生成结果无法 import | 先 `compile()` 校验语法，再检查依赖是否在白名单 |
| 函数签名对不上 | 以调用方的 schema 为准，不要反向改调用方 |
| 生成内容被截断 | 降低单次生成规模，分函数生成 |

### 何时不该用这个 skill

- 只需要读文档或写笔记：走知识库，不要调执行类命令。
- 需要改被测系统的业务数据：先确认数据隔离，再考虑用录制/回放。

## 执行顺序（顺序错了会白跑）

1. 先定签名，再生成实现。
2. 先语法校验，再单测。
3. 先在沙箱跑，再落库。
4. 先评审，再发布。

### 再加一条红线

- **NEVER** 不要让生成代码访问网络或文件系统——生成物的能力边界必须显式限制

### 兜底原则

任何一步失败，先留证（截图、响应体、日志），再重试；没有证据的重跑只会把问题变成偶发。
