# TEST_REPORT

验收：**PASS**。实际执行 72 项测试；0 FAIL，0 ERROR，0 SKIP。

运行时间：2026-09-27T05:04:34.393461+00:00；Python 3.12.14。

## 指定历史错误的10个合成回归

|测试项|输入|预期|实际|PASS/FAIL|
|---|---|---|---|---|
|TEST-001|合成单元格公式 =A1+#REF!|BLOCK / Q002|BLOCK / Q002|PASS|
|TEST-002|2027赛事关键标题含2026年|BLOCK / Q011|BLOCK / Q011|PASS|
|TEST-003|分项100+200+300，声明总计650|BLOCK / Q005|BLOCK / Q005|PASS|
|TEST-004|测试专用：VIP 16×1080=17280；通票声明等于总和却写19980|BLOCK / Q021|BLOCK / Q021|PASS|
|TEST-005|库存原已闭合，再新增售出1张，超出可售总池|BLOCK / Q024|BLOCK / Q024|PASS|
|TEST-006|双人共房产品声明1间，成本计费2间|BLOCK / Q022|BLOCK / Q022,Q023|PASS|
|TEST-007|声称成本加10%，实际按成本/0.9报价|BLOCK / Q023|BLOCK / Q023,Q025|PASS|
|TEST-008|第二退款窗口提前一天开始，与首窗重叠|BLOCK / Q014|BLOCK / Q014|PASS|
|TEST-009|同一metric_id分别标为订单和票张|WARNING / Q007|WARNING / Q007|PASS|
|TEST-010|PUBLISHED price_version缺少approval_ref|BLOCK / Q016|BLOCK / Q016|PASS|

## 全部自动测试（实际运行记录）

|测试项|输入／操作|预期|实际|PASS/FAIL|
|---|---|---|---|---|
|tests.test_s0.ModelTests.test_demo_shape|test_demo_shape|所有断言成立|无断言失败|PASS|
|tests.test_s0.ModelTests.test_dependency_cycle|test_dependency_cycle|所有断言成立|无断言失败|PASS|
|tests.test_s0.ModelTests.test_derived_and_paid_rights|test_derived_and_paid_rights|所有断言成立|无断言失败|PASS|
|tests.test_s0.ModelTests.test_invalid_key_type_and_missing|test_invalid_key_type_and_missing|所有断言成立|无断言失败|PASS|
|tests.test_s0.ModelTests.test_product_mapping|test_product_mapping|所有断言成立|无断言失败|PASS|
|tests.test_s0.ModelTests.test_sqlite_roundtrip|test_sqlite_roundtrip|所有断言成立|无断言失败|PASS|
|tests.test_s1.RevenueTests.test_one_price_updates_all|test_one_price_updates_all|所有断言成立|无断言失败|PASS|
|tests.test_s1.RevenueTests.test_one_seat_updates_all|test_one_seat_updates_all|所有断言成立|无断言失败|PASS|
|tests.test_s1.RevenueTests.test_paid_rights_not_lost|test_paid_rights_not_lost|所有断言成立|无断言失败|PASS|
|tests.test_s1.RevenueTests.test_recompute_and_rollups|test_recompute_and_rollups|所有断言成立|无断言失败|PASS|
|tests.test_s1.RevenueTests.test_scenario_order|test_scenario_order|所有断言成立|无断言失败|PASS|
|tests.test_s2.GateSmokeTests.test_draft_can_preview_not_release|test_draft_can_preview_not_release|所有断言成立|无断言失败|PASS|
|tests.test_s2.GateSmokeTests.test_findings_have_contract|test_findings_have_contract|所有断言成立|无断言失败|PASS|
|tests.test_s2.GateSmokeTests.test_malformed_rule_blocks_not_crashes|test_malformed_rule_blocks_not_crashes|所有断言成立|无断言失败|PASS|
|tests.test_s2.GateSmokeTests.test_valid_demo_passes_release|test_valid_demo_passes_release|所有断言成立|无断言失败|PASS|
|tests.test_s2.GateSmokeTests.test_xlsx_readonly_arithmetic_and_contract|test_xlsx_readonly_arithmetic_and_contract|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_approved_with_draft_rule|test_approved_with_draft_rule|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_deduction_duplicate|test_deduction_duplicate|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_duplicate_json_keys_rejected|test_duplicate_json_keys_rejected|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_inconsistent_versions|test_inconsistent_versions|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_mismatched_inventory_times|test_mismatched_inventory_times|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_missing_cell_reference|test_missing_cell_reference|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_negative_and_over_capacity|test_negative_and_over_capacity|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_no_silent_nan_boolean_or_fractional_count|test_no_silent_nan_boolean_or_fractional_count|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_outputs_different_snapshot|test_outputs_different_snapshot|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_paid_rights_sold_not_lost|test_paid_rights_sold_not_lost|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_percentage_120|test_percentage_120|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_refund_gap|test_refund_gap|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_required_rate_no_silent_default|test_required_rate_no_silent_default|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_same_name_different_content|test_same_name_different_content|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_scenarios_order|test_scenarios_order|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_stale_hardcoded_summary|test_stale_hardcoded_summary|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_time_order_and_preparation|test_time_order_and_preparation|所有断言成立|无断言失败|PASS|
|tests.test_s3.EdgeTests.test_unit_warning_and_old_year_noncritical|test_unit_warning_and_old_year_noncritical|所有断言成立|无断言失败|PASS|
|tests.test_s3.ExcelEdgeTests.test_errors_and_blank|test_errors_and_blank|所有断言成立|无断言失败|PASS|
|tests.test_s3.ExcelEdgeTests.test_hardcoded_contract_mismatch|test_hardcoded_contract_mismatch|所有断言成立|无断言失败|PASS|
|tests.test_s3.ExcelEdgeTests.test_percent_and_parentheses|test_percent_and_parentheses|所有断言成立|无断言失败|PASS|
|tests.test_s3.HistoricalRegressionTests.test_TEST_001|合成单元格公式 =A1+#REF! → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_s3.HistoricalRegressionTests.test_TEST_002|2027赛事关键标题含2026年 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_s3.HistoricalRegressionTests.test_TEST_003|分项100+200+300，声明总计650 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_s3.HistoricalRegressionTests.test_TEST_004|测试专用：VIP 16×1080=17280；通票声明等于总和却写19980 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_s3.HistoricalRegressionTests.test_TEST_005|库存原已闭合，再新增售出1张，超出可售总池 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_s3.HistoricalRegressionTests.test_TEST_006|双人共房产品声明1间，成本计费2间 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_s3.HistoricalRegressionTests.test_TEST_007|声称成本加10%，实际按成本/0.9报价 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_s3.HistoricalRegressionTests.test_TEST_008|第二退款窗口提前一天开始，与首窗重叠 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_s3.HistoricalRegressionTests.test_TEST_009|同一metric_id分别标为订单和票张 → WARNING|所有断言成立|无断言失败|PASS|
|tests.test_s3.HistoricalRegressionTests.test_TEST_010|PUBLISHED price_version缺少approval_ref → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_s4.DiffTests.test_identical|test_identical|所有断言成立|无断言失败|PASS|
|tests.test_s4.DiffTests.test_numeric_confirmed_and_unknown|test_numeric_confirmed_and_unknown|所有断言成立|无断言失败|PASS|
|tests.test_s4.DiffTests.test_reordering_not_change|test_reordering_not_change|所有断言成立|无断言失败|PASS|
|tests.test_s4.DiffTests.test_seating_derived_and_product_add_delete|test_seating_derived_and_product_add_delete|所有断言成立|无断言失败|PASS|
|tests.test_s4.DiffTests.test_text_replacement_no_semantic_claim|test_text_replacement_no_semantic_claim|所有断言成立|无断言失败|PASS|
|tests.test_s4.DiffTests.test_unconfirmed_never_promoted|test_unconfirmed_never_promoted|所有断言成立|无断言失败|PASS|
|tests.test_s5.SnapshotTests.test_block_writes_nothing|test_block_writes_nothing|所有断言成立|无断言失败|PASS|
|tests.test_s5.SnapshotTests.test_immutable_and_repeatable|test_immutable_and_repeatable|所有断言成立|无断言失败|PASS|
|tests.test_s5.SnapshotTests.test_metadata_tamper|test_metadata_tamper|所有断言成立|无断言失败|PASS|
|tests.test_s5.SnapshotTests.test_release_single_snapshot_and_idempotent|test_release_single_snapshot_and_idempotent|所有断言成立|无断言失败|PASS|
|tests.test_s5.SnapshotTests.test_tamper_blocks_export|test_tamper_blocks_export|所有断言成立|无断言失败|PASS|
|tests.test_s5.SnapshotTests.test_warning_requires_ack|test_warning_requires_ack|所有断言成立|无断言失败|PASS|
|tests.test_s6.CLITests.test_block_cannot_publish|test_block_cannot_publish|所有断言成立|无断言失败|PASS|
|tests.test_s6.CLITests.test_escape_and_usb_prohibited|test_escape_and_usb_prohibited|所有断言成立|无断言失败|PASS|
|tests.test_s6.CLITests.test_full_cli_workflow|test_full_cli_workflow|所有断言成立|无断言失败|PASS|
|tests.test_s6.CLITests.test_json_edit_not_silently_authoritative|test_json_edit_not_silently_authoritative|所有断言成立|无断言失败|PASS|
|tests.test_s6.CLITests.test_warning_not_blocked_validate_but_requires_snapshot_ack|test_warning_not_blocked_validate_but_requires_snapshot_ack|所有断言成立|无断言失败|PASS|
|tests.test_s7.FinalAcceptanceTests.test_derived_product_price_updates|test_derived_product_price_updates|所有断言成立|无断言失败|PASS|
|tests.test_s7.FinalAcceptanceTests.test_missing_or_competing_rules_block_release|test_missing_or_competing_rules_block_release|所有断言成立|无断言失败|PASS|
|tests.test_s7.FinalAcceptanceTests.test_nonnumeric_summary_pointer_blocks|test_nonnumeric_summary_pointer_blocks|所有断言成立|无断言失败|PASS|
|tests.test_s7.FinalAcceptanceTests.test_schema_and_demo_no_actual_data|test_schema_and_demo_no_actual_data|所有断言成立|无断言失败|PASS|
|tests.test_s7.FinalAcceptanceTests.test_unrepresentable_money_and_boolean_const_fail_closed|test_unrepresentable_money_and_boolean_const_fail_closed|所有断言成立|无断言失败|PASS|
|tests.test_s7.FinalAcceptanceTests.test_version_b_all_categories_and_passes|test_version_b_all_categories_and_passes|所有断言成立|无断言失败|PASS|
|tests.test_s7.FinalAcceptanceTests.test_version_labels_cannot_be_reused_for_different_content|test_version_labels_cannot_be_reused_for_different_content|所有断言成立|无断言失败|PASS|
|tests.test_s7.FinalAcceptanceTests.test_zero_capacity_and_zero_demand|test_zero_capacity_and_zero_demand|所有断言成立|无断言失败|PASS|

## 阶段门禁

|阶段|实际执行数|结果|
|---|---:|---|
|S0|6|PASS|
|S1|11|PASS|
|S2|16|PASS|
|S3|47|PASS|
|S4|53|PASS|
|S5|59|PASS|
|S6|64|PASS|
|S7|72|PASS|

## 验证范围与已修复问题

- 测试均为合成数据；没有读取公司原文件、U盘正文或真实票务平台。
- 输入单价／座席变化、阶段和票档汇总、付费权益及产品映射均有可复算断言。
- CLI通过子进程执行，不以直接调用函数代替命令行验收。
- S6曾发现快照读回后的JSON键顺序导致幂等导出误判；统一序列化后重新运行S6全部通过，才进入S7。
- Excel为限定公式引擎，不声称验证任意工作簿；未知函数会BLOCK。
- 审批证据真实性、真实需求、平台并发和现场安全不在本原型可验证范围。
- 重跑：python tests/run_acceptance.py。退出码非0或存在SKIP，不算完整验收通过。
