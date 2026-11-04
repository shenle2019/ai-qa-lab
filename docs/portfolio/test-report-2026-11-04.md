# 2026-11-04 测试用例扩充与执行报告

> 生成时间：2026-11-04T16:44:35
> 执行方式：按类别分别运行 pytest，结果来自 JUnit XML。

## 结论

六类场景共设计并收集 **195** 条用例：通过 182，失败 0，跳过 13。跳过项全部是 Android 真机/模拟器用例，当前环境没有可用设备，未伪造通过。

| 类别 | 执行结果 |
|---|---|
| 接口测试 | `51 passed, 0 skipped` |
| 兼容性 | `35 passed, 0 skipped` |
| 可靠性 | `26 passed, 0 skipped` |
| Web 测试 | `29 passed, 0 skipped` |
| 性能测试 | `29 passed, 0 skipped` |
| App 测试 | `12 passed, 13 skipped` |

## 分类汇总

| 类别 | 用例数 | 通过 | 跳过 | 失败 | 设计方法 |
|---|---:|---:|---:|---:|---|
| 接口测试 | 51 | 51 | 0 | 0 | 等价类 / 边界值 / 错误推测 / 场景法 |
| 兼容性 | 35 | 35 | 0 | 0 | 协议 / 编码 / 格式 / 架构兼容 |
| 可靠性 | 26 | 26 | 0 | 0 | 重复性 / 并发 / 恢复 / 隔离 |
| Web 测试 | 29 | 29 | 0 | 0 | UI 等价类 / 边界 / 错误推测 / 场景 |
| 性能测试 | 29 | 29 | 0 | 0 | 并发 / 持续负载 / 爬坡 / 阈值 |
| App 测试 | 25 | 12 | 13 | 0 | 元素解析 + 真机场景 |

## 本次发现并修复

- 超大路径 ID（如 24 位整数）会触发 SQLite 溢出并返回 500，已改为参数越界直接返回 404。
- 执行器先开写事务再回调自身接口，会导致 `database is locked`；已在部署阶段修复为先执行后落库，并启用 WAL 与 30 秒 busy timeout。
- 测试基础设施：多个 `tests` 目录没有包标记，pytest 混合收集时 `page`/`sut` fixture 会串到其他目录；已补 `__init__.py` 并把冲突 fixture 改为唯一名称。

## 分类明细

### 接口测试（51 条）

- [x] `test_title_valid_equivalence_and_boundary[1]`
- [x] `test_title_valid_equivalence_and_boundary[2]`
- [x] `test_title_valid_equivalence_and_boundary[10]`
- [x] `test_title_valid_equivalence_and_boundary[50]`
- [x] `test_title_valid_equivalence_and_boundary[100]`
- [x] `test_title_valid_equivalence_and_boundary[199]`
- [x] `test_title_valid_equivalence_and_boundary[200]`
- [x] `test_title_invalid_equivalence_and_boundary[0]`
- [x] `test_title_invalid_equivalence_and_boundary[201]`
- [x] `test_title_invalid_equivalence_and_boundary[1000]`
- [x] `test_priority_valid_equivalence[low]`
- [x] `test_priority_valid_equivalence[medium]`
- [x] `test_priority_valid_equivalence[high]`
- [x] `test_priority_invalid_equivalence[urgent]`
- [x] `test_priority_invalid_equivalence[]`
- [x] `test_priority_invalid_equivalence[HIGH]`
- [x] `test_priority_invalid_equivalence[0]`
- [x] `test_description_valid_boundary[0]`
- [x] `test_description_valid_boundary[1]`
- [x] `test_description_valid_boundary[4999]`
- [x] `test_description_valid_boundary[5000]`
- [x] `test_description_over_limit`
- [x] `test_ticket_lifecycle_scenario`
- [x] `test_status_update_equivalence[open]`
- [x] `test_status_update_equivalence[in_progress]`
- [x] `test_status_update_equivalence[closed]`
- [x] `test_status_update_invalid[done]`
- [x] `test_status_update_invalid[]`
- [x] `test_status_update_invalid[OPEN]`
- [x] `test_status_update_invalid[closed ]`
- [x] `test_partial_update_keeps_other_fields`
- [x] `test_update_missing_ticket`
- [x] `test_get_missing_ticket`
- [x] `test_delete_missing_ticket`
- [x] `test_duplicate_titles_are_allowed`
- [x] `test_unicode_title`
- [x] `test_emoji_title`
- [x] `test_special_characters_are_preserved[quotes ' " `]`
- [x] `test_special_characters_are_preserved[line1\nline2\tend]`
- [x] `test_special_characters_are_preserved[%%%___---]`
- [x] `test_special_characters_are_preserved[a  b]`
- [x] `test_sql_injection_is_stored_literally`
- [x] `test_xss_payload_is_returned_as_data`
- [x] `test_invalid_title_payloads[payload0]`
- [x] `test_invalid_title_payloads[payload1]`
- [x] `test_invalid_title_payloads[payload2]`
- [x] `test_invalid_title_payloads[payload3]`
- [x] `test_invalid_title_payloads[payload4]`
- [x] `test_unknown_fields_are_ignored`
- [x] `test_created_ticket_appears_in_list`
- [x] `test_bulk_create_scenario`

### 兼容性（35 条）

- [x] `test_json_with_utf8_charset`
- [x] `test_text_plain_json_body_is_rejected`
- [x] `test_missing_content_type_still_parses_json`
- [x] `test_utf8_bom_json_is_accepted`
- [x] `test_accept_header_does_not_break_json[application/json]`
- [x] `test_accept_header_does_not_break_json[text/html]`
- [x] `test_accept_header_does_not_break_json[application/xml]`
- [x] `test_accept_header_does_not_break_json[*/*]`
- [x] `test_unsupported_methods[OPTIONS]`
- [x] `test_unsupported_methods[HEAD]`
- [x] `test_unsupported_methods[PUT]`
- [x] `test_unknown_query_parameters_are_ignored`
- [x] `test_trailing_slash_redirects`
- [x] `test_path_is_case_sensitive`
- [x] `test_ticket_response_schema_is_stable`
- [x] `test_created_at_is_iso_datetime`
- [x] `test_health_schema_is_stable`
- [x] `test_openapi_lists_ticket_endpoints`
- [x] `test_response_is_utf8_decodable`
- [x] `test_max_description_round_trip`
- [x] `test_unknown_field_is_ignored`
- [x] `test_duplicate_json_keys_last_one_wins`
- [x] `test_non_object_bodies_are_rejected[body0]`
- [x] `test_non_object_bodies_are_rejected[body1]`
- [x] `test_non_object_bodies_are_rejected[string-body]`
- [x] `test_non_object_bodies_are_rejected[123]`
- [x] `test_null_and_wrong_typed_optionals_are_rejected[payload0]`
- [x] `test_null_and_wrong_typed_optionals_are_rejected[payload1]`
- [x] `test_null_and_wrong_typed_optionals_are_rejected[payload2]`
- [x] `test_defaults_when_optional_fields_missing`
- [x] `test_oversized_id_is_rejected`
- [x] `test_negative_id_is_not_found`
- [x] `test_delete_returns_empty_204`
- [x] `test_error_body_has_detail`
- [x] `test_no_cors_headers_by_default`

### 可靠性（26 条）

- [x] `test_repeated_reads_are_consistent`
- [x] `test_concurrent_reads_succeed`
- [x] `test_concurrent_writes_succeed`
- [x] `test_create_delete_recreate`
- [x] `test_malformed_json_then_valid_request`
- [x] `test_validation_error_then_valid_request`
- [x] `test_delete_is_not_idempotent`
- [x] `test_status_round_trip`
- [x] `test_repeated_create_delete_cycles`
- [x] `test_health_survives_burst`
- [x] `test_error_detail_is_stable`
- [x] `test_list_is_sorted_by_id_desc`
- [x] `test_ids_increase_monotonically`
- [x] `test_workbench_can_call_health`
- [x] `test_workbench_reports_unreachable_target`
- [x] `test_workbench_rejects_invalid_url`
- [x] `test_workbench_blocks_metadata_address`
- [x] `test_workbench_batch_limit`
- [x] `test_workbench_batch_ok`
- [x] `test_execute_without_cases_is_rejected`
- [x] `test_executor_rejects_absolute_target`
- [x] `test_missing_execution_report`
- [x] `test_duplicate_model_name_is_rejected`
- [x] `test_model_key_is_masked`
- [x] `test_seed_is_idempotent`
- [x] `test_server_survives_bad_body_and_stays_healthy`

### Web 测试（29 条）

- [x] `test_tickets_page_loads`
- [x] `test_sidebar_has_ten_entries`
- [x] `test_dashboard_has_four_stat_cards`
- [x] `test_dashboard_shows_total_label`
- [x] `test_create_ticket_by_priority[low]`
- [x] `test_create_ticket_by_priority[medium]`
- [x] `test_create_ticket_by_priority[high]`
- [x] `test_create_with_description`
- [x] `test_create_title_variants[\u4e2d\u6587\u6807\u9898-\u6253\u5370\u673a\u65e0\u6cd5\u8fde\u63a5]`
- [x] `test_create_title_variants[\u652f\u4ed8\u5931\u8d25 \U0001f525\U0001f9fe]`
- [x] `test_create_title_variants[\u7279\u6b8a\u5b57\u7b26 <>&"']`
- [x] `test_title_input_declares_200_limit`
- [x] `test_empty_title_shows_error`
- [x] `test_whitespace_title_shows_error`
- [x] `test_cancel_modal`
- [x] `test_search_filters_rows`
- [x] `test_status_filter`
- [x] `test_priority_filter`
- [x] `test_update_status_inline`
- [x] `test_update_priority_inline`
- [x] `test_delete_ticket`
- [x] `test_data_persists_after_reload`
- [x] `test_navigation_pages[/ui/#/platform-\u6d4b\u8bd5\u5e73\u53f0]`
- [x] `test_navigation_pages[/ui/#/models-\u6a21\u578b\u4e2d\u5fc3]`
- [x] `test_navigation_pages[/ui/#/testcases-\u6d4b\u8bd5\u7528\u4f8b]`
- [x] `test_navigation_pages[/ui/#/report-\u9879\u76ee\u62a5\u544a]`
- [x] `test_navigation_pages[/ui/#/portfolio-\u6a21\u5757\u9a8c\u6536]`
- [x] `test_navigation_pages[/ui/#/methodology-\u65b9\u6cd5\u8bba]`
- [x] `test_navigation_pages[/ui/#/knowledge-\u77e5\u8bc6\u5e93\u95ee\u7b54]`

### 性能测试（29 条）

- [x] `test_health_under_concurrency[1]`
- [x] `test_health_under_concurrency[2]`
- [x] `test_health_under_concurrency[3]`
- [x] `test_health_under_concurrency[5]`
- [x] `test_health_under_concurrency[8]`
- [x] `test_ticket_list_under_concurrency[1]`
- [x] `test_ticket_list_under_concurrency[2]`
- [x] `test_ticket_list_under_concurrency[3]`
- [x] `test_ticket_list_under_concurrency[5]`
- [x] `test_sustained_load[2]`
- [x] `test_sustained_load[3]`
- [x] `test_ramp_up_keeps_success[0.2]`
- [x] `test_ramp_up_keeps_success[0.5]`
- [x] `test_p95_thresholds_pass[200]`
- [x] `test_p95_thresholds_pass[500]`
- [x] `test_p95_thresholds_pass[2000]`
- [x] `test_p95_threshold_can_fail`
- [x] `test_404_is_counted_as_error`
- [x] `test_error_rate_threshold`
- [x] `test_percentiles_are_ordered`
- [x] `test_rps_is_positive`
- [x] `test_total_exceeds_vus`
- [x] `test_min_rps_threshold`
- [x] `test_min_rps_can_fail`
- [x] `test_mixed_endpoint_sequence`
- [x] `test_high_concurrency_health`
- [x] `test_status_counts_present`
- [x] `test_average_latency_is_positive`
- [x] `test_thresholds_are_recorded`

### App 测试（25 条）

- [x] `test_element_text`
- [x] `test_element_resource_id`
- [x] `test_element_content_desc`
- [x] `test_element_class_name`
- [x] `test_element_bounds_parse`
- [x] `test_element_center`
- [x] `test_element_visible_with_area`
- [x] `test_element_invisible_zero_width`
- [x] `test_element_invisible_without_bounds`
- [x] `test_element_tap_uses_center`
- [x] `test_element_tap_without_bounds_raises`
- [x] `test_element_repr_contains_text`
- [-] `test_device_model`（跳过：无 Android 设备）
- [-] `test_device_serial`（跳过：无 Android 设备）
- [-] `test_settings_home_visible`（跳过：无 Android 设备）
- [-] `test_settings_entries_visible[Network & internet]`（跳过：无 Android 设备）
- [-] `test_settings_entries_visible[Connected devices]`（跳过：无 Android 设备）
- [-] `test_settings_entries_visible[Apps]`（跳过：无 Android 设备）
- [-] `test_settings_entries_visible[Notifications]`（跳过：无 Android 设备）
- [-] `test_settings_entries_visible[Display & touch]`（跳过：无 Android 设备）
- [-] `test_open_network`（跳过：无 Android 设备）
- [-] `test_open_apps_and_back`（跳过：无 Android 设备）
- [-] `test_press_home_stays_in_launcher`（跳过：无 Android 设备）
- [-] `test_screenshot_saved`（跳过：无 Android 设备）
- [-] `test_current_activity_is_settings`（跳过：无 Android 设备）
