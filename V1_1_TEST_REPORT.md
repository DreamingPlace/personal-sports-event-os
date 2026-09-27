# V1_1_TEST_REPORT

v1.1 verdict: **PASS**

旧测试：72 / 通过 72；新增：68 / 通过 68。

实际执行 140 项；FAIL 0；ERROR 0；SKIP 0。

时间：2026-09-27T07:41:04.465631+00:00；Python 3.12.14。

## 基线与迁移说明

- S0源代码未修改前：72/72通过；见V1_0_BASELINE.md和S0_BASELINE.log。
- 保留原72项测试。test_s1分组汇总断言改为revenue_exact：分组显示金额相加可出现分币尾差，不能要求显示取整值反向闭合。
- 原5项CLI测试显式追加--legacy，验证v1适配器；新增独立CLI测试验证默认v1.1 ApplicationService。
- 10项历史错误另外通过显式迁移进入模块门禁再次执行，不仅验证兼容代码。
- S1修复后78/78；模块主验收32/32；本表为最终完整重跑结果。
- MOD-001～MOD-016均是实际测试方法，不是文档声明。外部插件测试使用临时独立distribution的entry_points元数据，没有改Kernel。

## 实际测试明细

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
|tests.test_v11_fixes.BusinessFixes.test_expired_rules|test_expired_rules|所有断言成立|无断言失败|PASS|
|tests.test_v11_fixes.BusinessFixes.test_price_class|test_price_class|所有断言成立|无断言失败|PASS|
|tests.test_v11_fixes.BusinessFixes.test_product_order|test_product_order|所有断言成立|无断言失败|PASS|
|tests.test_v11_fixes.BusinessFixes.test_rights_strategies|test_rights_strategies|所有断言成立|无断言失败|PASS|
|tests.test_v11_fixes.BusinessFixes.test_split_zone_invariant|test_split_zone_invariant|所有断言成立|无断言失败|PASS|
|tests.test_v11_fixes.BusinessFixes.test_travel_null|test_travel_null|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_001_kernel_schedule|MOD-001: Kernel+Schedule，无票务 → PASS|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_002_no_travel_validator|MOD-002: 禁用Travel → validator绝不运行|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_003_free_event_snapshot|MOD-003: 免费群众赛事 → validate/snapshot成功|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_004_missing_travel_dependency|MOD-004: Travel缺Pricing → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_005_disabled_payload_quarantined|MOD-005: 保留损坏的禁用payload，不执行/不冻结|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_006_cycle|MOD-006: 模块依赖环 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_007_price_class|MOD-007: 同tier不同zone不同price_class → 分别按价计算|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_008_rights_discount|MOD-008: 权益8折 → 采用有效单价，非公开价|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_009_travel_missing_price|MOD-009: Travel含非票成本但price=null → BLOCK，不能snapshot|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_010_rule_expiry|MOD-010: 所有规则模块适用期检查 → 过期BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_011_zone_split|MOD-011: 经济事实不变，zone拆分 → 精确总收入完全不变|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_012_product_order|MOD-012: 产品included_sessions仅重排 → 无业务差异|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_013_only_active_findings|MOD-013: Disabled未知模块坏payload → 不产生Finding|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_014_snapshot_enable|MOD-014: snapshot后启用新模块 → 历史记录字节/索引不变|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_015_upgrade_without_migration|MOD-015: 插件升级无migration → BLOCK，不静默解释|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_MOD_016_migration|MOD-016: v1.0迁移 → 与修正舍入后的模型精确对账|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_demand_missing_conflicting_and_unknown|test_demand_missing_conflicting_and_unknown|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_disable_rights_requires_inventory_reconciliation|test_disable_rights_requires_inventory_reconciliation|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_external_entrypoint_discovery|实际通过临时独立distribution元数据发现插件，不改Kernel注册表。|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_fresh_cli|test_fresh_cli|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_kernel_business_independence|test_kernel_business_independence|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_manifest_roundtrip|test_manifest_roundtrip|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_old_snapshot_not_relabelled|test_old_snapshot_not_relabelled|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_profiles_not_runtime_modes|test_profiles_not_runtime_modes|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_replace_demand|test_replace_demand|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_revenue_and_inventory_independent|test_revenue_and_inventory_independent|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_rights_fixed_price|test_rights_fixed_price|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_schema_missing_false_nan_unknown|test_schema_missing_false_nan_unknown|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_snapshot_integrity_and_immutable|test_snapshot_integrity_and_immutable|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_travel_closure_and_no_double_count|test_travel_closure_and_no_double_count|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_version_reuse_blocks|test_version_reuse_blocks|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.ModularTests.test_working_hash_tamper|test_working_hash_tamper|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.MigratedHistoricalTests.test_migrated_TEST_001|模块化迁移 TEST-001: 合成单元格公式 =A1+#REF! → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.MigratedHistoricalTests.test_migrated_TEST_002|模块化迁移 TEST-002: 2027赛事关键标题含2026年 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.MigratedHistoricalTests.test_migrated_TEST_003|模块化迁移 TEST-003: 分项100+200+300，声明总计650 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.MigratedHistoricalTests.test_migrated_TEST_004|模块化迁移 TEST-004: 测试专用：VIP 16×1080=17280；通票声明等于总和却写19980 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.MigratedHistoricalTests.test_migrated_TEST_005|模块化迁移 TEST-005: 库存原已闭合，再新增售出1张，超出可售总池 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.MigratedHistoricalTests.test_migrated_TEST_006|模块化迁移 TEST-006: 双人共房产品声明1间，成本计费2间 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.MigratedHistoricalTests.test_migrated_TEST_007|模块化迁移 TEST-007: 声称成本加10%，实际按成本/0.9报价 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.MigratedHistoricalTests.test_migrated_TEST_008|模块化迁移 TEST-008: 第二退款窗口提前一天开始，与首窗重叠 → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.MigratedHistoricalTests.test_migrated_TEST_009|模块化迁移 TEST-009: 同一metric_id分别标为订单和票张 → WARNING|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.MigratedHistoricalTests.test_migrated_TEST_010|模块化迁移 TEST-010: PUBLISHED price_version缺少approval_ref → BLOCK|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_evidence_confirmed_vs_unconfirmed|test_evidence_confirmed_vs_unconfirmed|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_optional_module_no_calculation|test_optional_module_no_calculation|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_all_module_calculations_json_serializable|test_all_module_calculations_json_serializable|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_schema_upgrade_explicit_migration|test_schema_upgrade_explicit_migration|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_unknown_disabled_plugin_not_loaded|test_unknown_disabled_plugin_not_loaded|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_warning_ack_snapshot|test_warning_ack_snapshot|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_no_mutation_by_calculation_or_export|test_no_mutation_by_calculation_or_export|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_missing_demand_rate_no_default|test_missing_demand_rate_no_default|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_demand_provider_conflict|test_demand_provider_conflict|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_sales_window_and_last_rights_node|test_sales_window_and_last_rights_node|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_sensitivity_and_group_exactness|test_sensitivity_and_group_exactness|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_seat_edit_propagates_and_inventory_blocks|test_seat_edit_propagates_and_inventory_blocks|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_blank_evidence_role_not_confirmed|test_blank_evidence_role_not_confirmed|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_decimal_context_does_not_change_result|test_decimal_context_does_not_change_result|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_snapshot_diff_metadata|test_snapshot_diff_metadata|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_configuration_edit_invalidates_approval_in_service|test_configuration_edit_invalidates_approval_in_service|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_failed_dependency_change_is_atomic|test_failed_dependency_change_is_atomic|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_unknown_schema_properties_block|test_unknown_schema_properties_block|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_numeric_input_precision_is_not_silently_rounded|test_numeric_input_precision_is_not_silently_rounded|所有断言成立|无断言失败|PASS|
|tests.test_v11_modular.AdditionalBoundaryTests.test_empty_kernel_snapshot_with_explicit_approval|test_empty_kernel_snapshot_with_explicit_approval|所有断言成立|无断言失败|PASS|

## 验收边界

完全合成离线数据；不证明真实审批、商业需求、现场容量安全或生产可用性。模块/插件为可信本地Python代码，不提供沙箱。
复现：`python tests/run_v11_acceptance.py`。退出码非0、旧测试不足72项或有SKIP均不算PASS。

## 交付包独立验证

- 将交付ZIP解压到独立校验目录，以非editable方式安装到独立site目录。
- 确认实际import来自新安装目录，而非开发源码路径。
- 该安装再次执行全部140项测试：140 PASS、0 FAIL/ERROR/SKIP。
- 在空工作目录实际执行demo、validate、snapshot：PASS。
- 日志：outputs/v1_1/ISOLATED_INSTALL.log、ISOLATED_TESTS.log。
- 原data/event.sqlite、原A/B数据及SN-*发布目录经git diff核对未改变。
