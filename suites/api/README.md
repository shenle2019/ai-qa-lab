# suites/api

接口自动化测试套件：pytest + requests，黑盒调用 SUT HTTP 接口。

## 运行

```bash
# 仓库根目录；自动启动本地 SUT
.venv\Scripts\python.exe -m pytest suites\api -q

# 已有一个运行中的 SUT 时，跳过自动启动
set SUT_BASE_URL=http://127.0.0.1:8000
.venv\Scripts\python.exe -m pytest suites\api -q
```

## 覆盖范围

- 健康检查与 OpenAPI 契约
- 工单创建、查询、列表、状态/优先级更新
- 异常场景：404、422、空值、超长字段、非法枚举、越界参数
- 知识库 mock 接口

## 设计

- `tests/conftest.py` 负责启动/停止 SUT，并为每个测试提供 `api` 客户端。
- 测试数据使用随机后缀，避免多次运行互相污染。
- 测试数据库放在 `suites/api/.tmp/`，不进入版本库。
