---
name: zentao-cli
description: "使用场景：用 zentao CLI 查询与操作禅道（项目集 / 产品 / 项目 / 执行 / 需求 / Bug / 任务 / 用例 / 测试单），含增删改查与状态流转。当用户提到禅道、zentao、查 Bug、建任务时触发。"
license: MIT
metadata:
  author: Sun Hao <sunhao@chandao.com>
  repository: https://github.com/easysoft/zentao-cli.git
  keywords: [zentao, 禅道, cli, project-management]
  version: 0.1.7
---

# 禅道 CLI

通过 `zentao` 命令行工具查询和操作禅道数据。CLI 自动处理认证、分页，支持工作区上下文和数据过滤/排序。

## 前置准备

### 安装

```bash
npm install -g zentao-cli
# 或 bun install -g zentao-cli
# 或 pnpm install -g zentao-cli
# 或免安装运行：npx zentao-cli
```

如果用户没有安装，引导用户进行全局安装使用，如果系统存在 bun 或 pnpm 则优先使用 bun 或 pnpm 进行全局安装。

### 认证

首次执行任意 `zentao` 命令会自动提示登录。也可显式登录：

```bash
zentao login -s https://zentao.example.com -u admin -p 123456
```

环境变量（优先级低于命令行参数）：

| 变量 | 说明 |
|------|------|
| `ZENTAO_URL` | 禅道服务地址 |
| `ZENTAO_ACCOUNT` | 用户账号 |
| `ZENTAO_PASSWORD` | 密码 |
| `ZENTAO_TOKEN` | 直接指定 Token（有此变量可省略密码） |

登录成功后凭证缓存在 `~/.config/zentao/zentao.json`，后续无需重复登录。

### 凭证安全

- 用户尚未登录时，不要在对话里收集账号密码。让用户直接在终端执行 `zentao login`，或执行任意 `zentao` 命令触发首次自动登录提示，由用户自行输入凭证。
- 严禁读取本地凭证：`ZENTAO_PASSWORD` / `ZENTAO_TOKEN` 环境变量、`~/.config/zentao/zentao.json` 配置文件。所有禅道数据均通过 `zentao` 命令获取，凭证由 CLI 内部处理。

## 命令格式

使用简写方式（推荐）：

| 操作 | 命令 |
|------|------|
| 列表 | `zentao <module>` |
| 详情 | `zentao <module> <id>` |
| 创建 | `zentao <module> create --field=value` |
| 更新 | `zentao <module> update <id> --field=value` |
| 删除 | `zentao <module> delete <id>` |
| 动作 | `zentao <module> <action> <id>` |
| 帮助 | `zentao <module> help` |

也支持 `--data='JSON'` 传入 JSON 数据。

## 模块与操作速查

| 模块名 | 中文 | 支持的操作 |
|--------|------|-----------|
| program | 项目集 | CRUD |
| product | 产品 | CRUD |
| project | 项目 | CRUD |
| execution | 执行/迭代 | CRUD |
| story | 需求 | CRUD + activate / change / close |
| epic | 业务需求 | CRUD + activate / change / close |
| requirement | 用户需求 | CRUD + activate / change / close |
| bug | Bug | CRUD + activate / close / resolve |
| task | 任务 | CRUD + activate / close / finish / start |
| testcase | 测试用例 | CRUD |
| testtask | 测试单 | CUD（按产品/项目/执行查列表） |
| productplan | 产品计划 | CUD（按产品查列表） |
| build | 版本 | CUD（按项目/执行查列表） |
| release | 发布 | CUD（按产品查列表） |
| feedback | 反馈 | CRUD + activate / close |
| ticket | 工单 | CRUD + activate / close |
| system | 应用 | CU（按产品查列表） |
| user | 用户 | CRUD |
| file | 附件 | 编辑名称 + 删除 |

> CRUD = 列表 + 详情 + 创建 + 更新 + 删除；CUD = 无独立列表接口，需指定所属范围

### 列表范围参数

部分模块的列表需要指定所属范围：

```bash
zentao story --product=1                # 产品 #1 的需求
zentao bug --product=1                  # 产品 #1 的 Bug
zentao task --execution=1               # 执行 #1 的任务
zentao execution --project=5            # 项目 #5 的执行
zentao build --project=5                # 项目 #5 的版本
zentao testtask --product=1             # 产品 #1 的测试单
zentao release --product=1              # 产品 #1 的发布
zentao productplan --product=1          # 产品 #1 的计划
zentao feedback --product=1             # 产品 #1 的反馈
zentao ticket --product=1               # 产品 #1 的工单
```

设置工作区后可省略这些参数（见下方工作区章节）。

## AI 使用策略

### 输出格式

- 展示给用户：不加 `--format` 参数，默认输出 Markdown 表格（列表）或列表（单个对象）
- 需要程序化处理：加 `--format=json`，返回结构化 JSON

### 交互确认

AI 场景下执行删除操作时加 `--yes` 跳过确认提示：

```bash
zentao bug delete 1 --yes
```

### 不知道 ID 时

先查列表获取 ID，再操作具体对象：

```bash
zentao product --pick=id,name           # 查看产品列表
zentao bug --product=1 --pick=id,title  # 查看 Bug 列表
zentao bug 42                           # 查看具体 Bug
```

### 写操作前确认

执行创建、更新、删除等写操作前，先向用户确认操作内容。用户明确要求不确认时可跳过。

### 更新操作自动补全

执行 `update` 时，CLI 会先 GET 当前对象，把用户未显式传入的字段用现值填充后再 PUT，避免禅道 PUT 覆盖未提交字段导致清空。因此只需传想改的字段即可，无需手动先查再传完整参数。

## 数据处理

### 摘取字段

```bash
zentao product --pick=id,name,status
```

### 过滤

```bash
zentao bug --product=1 --filter='status:active'
zentao bug --product=1 --filter='severity<=2,pri<=2'    # AND
zentao bug --product=1 --filter='status:active' --filter='status:resolved'  # OR
```

支持的运算符：`:` 等于、`!=` 不等于、`>` `<` `>=` `<=`、`~` 包含、`!~` 不包含。

### 模糊搜索

```bash
zentao bug --product=1 --search=登录 --search-fields=title,steps
```

### 排序

```bash
zentao bug --product=1 --sort=pri_asc,severity_asc
```

### 分页

```bash
zentao bug --product=1 --page=1 --recPerPage=50
zentao bug --product=1 --all            # 获取全部
zentao bug --product=1 --limit=10       # 只取前 10 条
```

## 常用操作示例

完整命令示例已拆到 references/commands.md，动手前 MANDATORY 先读它；本节只留最小示例。

`ash
zentao bug list --product 1 --status active
zentao bug view --id 42
`

## 错误处理

| 错误码 | 含义 | 处理方式 |
|--------|------|---------|
| E1001 | 未登录/凭证缺失 | 执行 `zentao login` |
| E1004 | Token 失效 | 执行 `zentao login` 重新登录 |
| E2001 | 模块不存在 | 执行 `zentao help` 查看可用模块 |
| E2002 | 对象不存在 | 检查 ID 是否正确 |
| E2003 | 缺少必要参数 | 执行 `zentao <module> help` 或 `zentao <module> <action> help` 查看操作参数 |
| E2006 | 无权限 | 提示用户检查权限 |
| E5001 | 请求超时 | 检查网络或禅道服务状态 |

## 注意事项

- 不确定模块参数时，先执行 `zentao <module> help` 查看帮助，不确定操作参数时，先执行 `zentao <module> <action> help` 查看帮助
- `browseType` 常用值：`all`（全部）、`doing`（进行中）、`closed`（已关闭）
- 多账号切换：`zentao profile` 查看和切换账号

<!-- hardened:six-shapes -->
## 执行顺序

1. 先确认登录状态与目标产品/项目 ID，没登录过的先跑登录。
2. 再补全资源 ID：产品 → 项目 → 执行 → 需求/Bug 的层级要一层层取。
3. 然后只读查询，拿到目标对象当前状态。
4. 接着执行写操作，一次只改一个对象，改完立刻回读确认。
5. 最后把改动记进变更日志：对象、旧值、新值、时间。

## 判断与选择

| 情形 | 选哪条 | 为什么 |
| --- | --- | --- |
| 不知道 ID | 先列表再按名称匹配 | 猜 ID 会改错对象 |
| 批量改状态 | 逐条改并回读 | 批量接口失败时不告诉你哪条没成 |
| 只查不改 | 用只读命令 | 少一次写就少一次事故 |
| 要关联需求与用例 | 先建关联再改状态 | 顺序反了会丢关联 |
| 名称重名 | 用 ID 二次确认 | 同名对象在禅道很常见 |

## 反模式

- **NEVER** 凭名称直接写操作 —— 因为重名会把改动落到别人的对象上。
- **NEVER** 跳过回读 —— 因为接口返回成功不等于状态真的变了。
- **NEVER** 批量改而不记录 —— 因为出问题无法回滚。
- **NEVER** 把账号密码写进命令历史 —— 因为会被 shell 记录。
- **NEVER** 在生产项目上试命令 —— 因为禅道没有回收站。
- **NEVER** 一次改多个字段 —— 因为失败时分不清是哪个字段被拒。

## 失败兜底

- 登录过期：重新登录后重放命令，写操作前先回读确认没生效。
- 接口报错：保留原文错误码，先查权限再查参数，不反复重试写操作。
- 批量中途中止：列出已成功与未执行的条目，逐条补齐。

## 一页速查

| 问题 | 怎么做 |
| --- | --- |
| 不知道对象 ID | 先列表按名匹配 |
| 写操作怎么确认 | 立刻回读 |
| 批量失败 | 逐条 + 记录 |
| 判断要不要写 | 只读够用就不写 |
| 重名怎么办 | 用 ID 二次确认 |
| 出错先查哪里 | 先权限后参数 |
| 交付前查什么 | 变更日志齐全 |

## 示例

```bash
# 查产品下的 Bug 列表
zentao bug list --product 1 --status active

# 改一条 Bug 的状态并回读
zentao bug resolve --id 42 --resolution fixed
zentao bug view --id 42
```
