# 2026-11-03 测试报告：CRUD 与分层用例扩充

> 目标：每个子项新增 20+ 用例，覆盖创建、读取、更新、删除和关键交互。
> 所有用例均本地真实运行，不使用 mock 数据替代被测系统。

## 1. 汇总

| 子项 | 新增 | 套件总数 | 命令 | 结果 |
|---|---:|---:|---|---|
| 接口 CRUD | 29 | — | `pytest suites/api -q` | 56 passed |
| Web UI CRUD | 28 | — | `python -m libs.minipytest libs/miniplaywright/demo` | 33 passed |
| App UI | 24 | — | `pytest libs/miniappium/tests -q` | 29 passed |
| 测试平台 CRUD | 26 | — | `pytest apps/sut/backend -q` | 38 passed |

- 本轮新增：**107** 个用例。
- 真实 pytest：172 个（接口 56 + 后端/平台 38 + 迷你 pytest 33 + 迷你 Playwright 6 + 迷你 Appium 29 + 迷你压测 5 + LLM 评测 5）。
- 迷你演示：58 个（迷你 pytest 20 + Web 33 + App 3 + 压测 1 + 评测 1）。

## 2. 接口 CRUD（29 个新增）

覆盖：创建默认值、优先级、空描述、200/201 字标题、422 拒绝、读取/404、列表倒序、状态/优先级更新、非法枚举、空更新、删除/404/重复删除。

| # | 用例 | 覆盖点 |
|---:|---|---|
| 1 | `test_create_minimal_returns_201` | 创建 |
| 2 | `test_create_defaults` | 创建 |
| 3 | `test_create_high_priority` | 创建 |
| 4 | `test_create_low_priority` | 创建 |
| 5 | `test_create_with_description` | 创建 |
| 6 | `test_create_empty_description` | 创建 |
| 7 | `test_create_title_200_chars` | 创建 |
| 8 | `test_create_title_201_chars_rejected` | 创建 |
| 9 | `test_create_blank_title_rejected` | 创建 |
| 10 | `test_create_missing_title_rejected` | 创建 |
| 11 | `test_create_single_char_title` | 创建 |
| 12 | `test_get_created_ticket` | 查询单条 |
| 13 | `test_get_missing_ticket_returns_404` | 查询单条 |
| 14 | `test_list_contains_created_ticket` | 列表 |
| 15 | `test_list_is_newest_first` | 列表 |
| 16 | `test_update_status_in_progress` | 更新 |
| 17 | `test_update_status_closed` | 更新 |
| 18 | `test_update_priority_high` | 更新 |
| 19 | `test_update_priority_low` | 更新 |
| 20 | `test_update_status_and_priority` | 更新 |
| 21 | `test_update_invalid_status_rejected` | 更新 |
| 22 | `test_update_invalid_priority_rejected` | 更新 |
| 23 | `test_update_missing_ticket_returns_404` | 更新 |
| 24 | `test_empty_update_keeps_values` | 更新 |
| 25 | `test_delete_ticket_returns_204` | 删除 |
| 26 | `test_delete_missing_ticket_returns_404` | 删除 |
| 27 | `test_deleted_ticket_is_gone` | 删除 |
| 28 | `test_deleted_ticket_not_in_list` | 删除 |
| 29 | `test_delete_twice_returns_404` | 删除 |

## 3. Web UI CRUD（28 个新增）

覆盖：页面加载、创建（最小/描述/高/低优先级）、取消、空标题校验、200 字标题、列表可见、状态/优先级更新、删除、搜索、状态/优先级筛选、7 个页面导航。

| # | 用例 | 覆盖点 |
|---:|---|---|
| 1 | `test_tickets_page_loads` | 其他 |
| 2 | `test_create_minimal_ticket` | 创建 |
| 3 | `test_create_ticket_with_description` | 创建 |
| 4 | `test_create_high_priority_ticket` | 创建 |
| 5 | `test_create_low_priority_ticket` | 创建 |
| 6 | `test_create_second_ticket` | 创建 |
| 7 | `test_cancel_modal` | 其他 |
| 8 | `test_empty_title_shows_error` | 空值/空更新 |
| 9 | `test_long_title_200` | 边界长度 |
| 10 | `test_created_ticket_visible` | 创建 |
| 11 | `test_update_status_in_progress` | 更新 |
| 12 | `test_update_status_closed` | 更新 |
| 13 | `test_update_priority_high` | 更新 |
| 14 | `test_update_priority_low` | 更新 |
| 15 | `test_update_status_and_priority` | 更新 |
| 16 | `test_delete_ticket` | 删除 |
| 17 | `test_delete_second_ticket` | 删除 |
| 18 | `test_deleted_ticket_not_in_search` | 删除 |
| 19 | `test_search_filters_title` | 搜索 |
| 20 | `test_status_filter_closed` | 筛选 |
| 21 | `test_priority_filter_high` | 筛选 |
| 22 | `test_navigate_workbench` | 页面导航 |
| 23 | `test_navigate_knowledge` | 页面导航 |
| 24 | `test_navigate_report` | 页面导航 |
| 25 | `test_navigate_portfolio` | 页面导航 |
| 26 | `test_navigate_platform` | 页面导航 |
| 27 | `test_navigate_methodology` | 页面导航 |
| 28 | `test_dashboard_loads_after_create` | 其他 |

## 4. App UI（24 个新增）

覆盖：Settings 首页 9 个元素、7 个页面打开/返回、返回首页、搜索 Wi-Fi、滑动、截图、当前 Activity、Home 后重启。

| # | 用例 | 覆盖点 |
|---:|---|---|
| 1 | `test_model` | 设备信息 |
| 2 | `test_serial` | 设备序列号 |
| 3 | `test_home_search_visible` | 搜索 |
| 4 | `test_home_network_visible` | 首页元素 |
| 5 | `test_home_connected_devices_visible` | 首页元素 |
| 6 | `test_home_apps_visible` | 首页元素 |
| 7 | `test_home_notifications_visible` | 首页元素 |
| 8 | `test_home_sound_visible` | 首页元素 |
| 9 | `test_home_modes_visible` | 首页元素 |
| 10 | `test_home_display_visible` | 首页元素 |
| 11 | `test_home_google_visible` | 首页元素 |
| 12 | `test_open_network` | 打开页面 |
| 13 | `test_open_apps` | 打开页面 |
| 14 | `test_open_notifications` | 打开页面 |
| 15 | `test_open_sound` | 打开页面 |
| 16 | `test_open_display` | 打开页面 |
| 17 | `test_open_connected_devices` | 打开页面 |
| 18 | `test_home_search_bar_visible` | 搜索 |
| 19 | `test_back_from_network` | 返回 |
| 20 | `test_search_wifi` | 搜索 |
| 21 | `test_swipe_home` | 滑动 |
| 22 | `test_screenshot` | 截图 |
| 23 | `test_current_activity` | 当前页面 |
| 24 | `test_home_key_and_restart` | 首页元素 |

## 5. 测试平台 CRUD（26 个新增）

覆盖：项目创建/重复/列表/404、用例创建/筛选/非法项目、计划创建/筛选/404、执行通过/失败/404、结果查询、缺陷创建/更新/筛选/非法状态、报告导入、汇总字段。

| # | 用例 | 覆盖点 |
|---:|---|---|
| 1 | `test_create_project_and_get` | 创建 |
| 2 | `test_duplicate_project_name_returns_same_id` | 重复数据 |
| 3 | `test_list_projects_contains_project` | 列表 |
| 4 | `test_missing_project_returns_404` | 不存在 |
| 5 | `test_create_case_and_list` | 创建 |
| 6 | `test_filter_cases_by_project` | 筛选 |
| 7 | `test_case_invalid_project_404` | 非法输入 |
| 8 | `test_case_high_priority` | 其他 |
| 9 | `test_case_low_priority` | 其他 |
| 10 | `test_case_web_module` | 其他 |
| 11 | `test_create_plan_and_get` | 创建 |
| 12 | `test_filter_plans_by_project` | 筛选 |
| 13 | `test_plan_invalid_project_404` | 非法输入 |
| 14 | `test_missing_plan_returns_404` | 不存在 |
| 15 | `test_run_plan_passed` | 执行 |
| 16 | `test_run_plan_failed` | 执行 |
| 17 | `test_run_missing_plan_404` | 执行 |
| 18 | `test_list_executions_contains_run` | 列表 |
| 19 | `test_get_execution_results` | 查询单条 |
| 20 | `test_missing_execution_404` | 不存在 |
| 21 | `test_create_defect_and_patch` | 创建 |
| 22 | `test_filter_defects_by_project` | 筛选 |
| 23 | `test_invalid_defect_status_422` | 非法输入 |
| 24 | `test_patch_missing_defect_404` | 更新 |
| 25 | `test_import_minipytest_report` | 导入 |
| 26 | `test_summary_shape` | 其他 |

## 6. 复现命令

```bash
cd /e/ailearning/ai-qa-lab
./.venv/Scripts/python.exe -m pytest suites/api -q
./.venv/Scripts/python.exe -m pytest apps/sut/backend -q
./.venv/Scripts/python.exe -m pytest libs/miniappium/tests -q
./.venv/Scripts/python.exe -m libs.minipytest libs/miniplaywright/demo
```

## 7. 边界

- App 用例跑在本机 Android 模拟器；CI 无设备时自动 skip。
- Web 用例跑在本机 Edge headless；CI 无 Chromium 时自动 skip。
- 接口和平台用例使用临时/内存 SQLite，不污染开发数据。
- 本轮新增以 CRUD 和关键交互为主，不代表生产级覆盖率。
