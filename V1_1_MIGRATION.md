# v1.0 → v1.1 Migration

## 先决条件

已冻结源提交 `8eb00c613f4270212639df3c1e0e4d8a42acb7af`。修改前72项通过，见V1_0_BASELINE.md。原SQLite、SN-*快照和旧报告保留。

迁移命令：

```bash
python -m sports_os migrate-v10 data/demo/version_a.json
python -m sports_os validate
python -m sports_os revenue
python -m sports_os snapshot
```

输入必须位于独立workspace中，且为 `schema_version=1.0, synthetic=true, snapshot_id=null` 工作数据。迁移工具先检查旧结构，再映射到模块，最后经过新模块完整门禁才能写入新库。旧规则过期/Travel漏价不会因为来自旧版而豁免。旧snapshot_id非空会拒绝，不能抹掉旧标识伪装成新快照。

## 映射

|v1.0|v1.1|
|---|---|
|event identity|manifest.project；版本附加-v11，合成属性和批准引用原样保留|
|event.venue|core.venue|
|sessions|core.schedule.rows；销售开始取最早price.valid_from，结束取末场end_time（迁移假设，需人工确认）|
|seating|ticketing.seating；price_class_id默认为原tier，移除paid_rights至Rights|
|prices|ticketing.pricing；session_id+price_class_id业务键，原price_version成为模块data_version|
|paid_rights|ticketing.rights；FACE_VALUE默认策略，已有显式策略保留；履约情景从原paid_rights_rate迁移|
|inventory|ticketing.inventory；原互斥分配不自动调整|
|SINGLE/PASS产品|product.pass；占票映射不变|
|TRAVEL产品|product.travel；缺报价闭合则BLOCK|
|rules|按类型分别迁移到refund/launch/identity/transfer/rights_return模块|
|scenarios|demand.multiplicative；权益履约率交给Rights|
|tasks / decisions|project.tasks / project.decisions|
|quality_evidence|quality.declarations（可禁用的声明检查模块）|
|明确绑定价格等changed_paths的Decision|同时转换为通用带模块路径的provenance记录；确认/未确认标签保留|

迁移不读取源文件正文，仅处理传入的合成结构化数据。资料出处以合成输入hash记录，不虚构外部证据。

## 收入对账

修正逐座区提前舍入后，精确值与新模块模型一致：

|指标|原v1.0显示值|修复后精确值|修复后显示到分|
|---|---:|---:|---:|
|满售|52390520.00|52390520|52390520.00|
|高|46096344.92|46096344.9440|46096344.94|
|中|37951452.76|37951452.7760|37951452.78|
|低|28848337.96|28848338.0000|28848338.00|

差异完全来自取消逐区round，没有修改合成席位/票价。旧组汇总测试改用exact字段，不要求“多个已round的组显示值相加”与总显示值相等。新MOD-011验证拆zone前后精确总额完全相同。

## 原72测试如何保留

- 72个测试方法全部保留，不删失败场景。
- 只有舍入层级断言按修复要求改为revenue_exact。
- 原5项CLI测试使用`--legacy`明确保留旧工作流；默认v1.1 CLI新增独立验收。
- 10项历史合成样本另外迁移进入模块门禁，继续识别错误。
- v1.0公开API用于旧数据兼容，不能用它向新模块根schema添加必填业务字段。

## 后续插件升级

module_version或schema_version与安装插件不符时BLOCK。必须调用模块自己的migrate，然后更新版本与payload。应用将迁移后的模块和项目标为DRAFT，批准引用清空，需人工重新批准。没有migration时不执行、不猜测兼容性。

历史快照查看只验证其完整性，不需要把历史schema解释为当前schema；重新导出计算时必须安装匹配版本，或显式迁移为新的工作态/快照。没有自动下载历史插件。

## 旧发布件的计算语义

已存在的v1.0发布目录保持原样。舍入修复改变了计算结果，因此不能用修复后的计算器覆盖旧SN-*目录；兼容导出检测内容不一致时会拒绝覆盖。若必须逐字节重现旧发布结果，使用V1_0_BASELINE记载的原提交；新的结果应显式迁移并生成SN11-*快照，而不是沿用旧结果标识。
