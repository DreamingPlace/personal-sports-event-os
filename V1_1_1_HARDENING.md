# Sports Event OS v1.1.1 — Pre-Desktop Hardening

## 1. 结论与边界

**DESKTOP_READINESS = PASS**：本轮已列风险及新增边界测试通过，未发现已知P0或明显导致错误业务结果的P1。此结论限于离线、单用户、合成数据的桌面原型准备，不等于生产票务系统认证。

本轮没有新增业务模块、GUI、AI、平台连接、真实公司数据、云同步、权限或复杂规则引擎。Kernel主架构冻结；后续问题按“桌面实际使用 → 复现 → 测试 → 对应模块修复”推进。

## 2. 基线与实际验收

- base commit: `8ffdfb6b1905453e1940e968c506cfbd8d7dda5a`，main干净工作区开始。
- new commit: 本报告随v1.1.1实现一同提交；最终SHA见交付消息，仓库内用 `git log -1 --format=%H -- V1_1_1_HARDENING.md` 查询，避免把自引用SHA写进被哈希的同一提交。
- 原测试：140；通过140。原140项测试文件未改写或删除。
- 新测试：40；通过40，其中HARD-001～024为24个独立测试。
- 总计：180；FAIL 0；ERROR 0；SKIP 0。
- 实际逐项输入、预期、断言结果：[V1_1_1_TEST_REPORT.md](V1_1_1_TEST_REPORT.md)。机器结果和完整日志：outputs/v1_1_1/。

|风险|结论|实现/证据|
|---|---|---|
|P1-01 Approval invalidation|PASS|编辑失效批准；HARD-001～005、019～020及CLI闭环|
|P1-02 Provider completeness|PASS|Revenue显式schedule；价格、日程、权益替代Provider及冲突检查|
|P1-03 Multi-venue relation|PASS|可选venue_id、venues外键；HARD-009～011、021|
|P1-04 Rights billing basis|PASS|分配/履约/计费分离；HARD-012～014、022～023|
|P1-05 Rule scope readiness|PASS|ALL/SESSION、交集及半开时间冲突；HARD-015～018、024|

阶段门禁实际结果：S0 140/140 → S1 145/145 → S2 148/148 → S3 151/151 → S4 154/154 → S5 158/158 → S6 163/163 → S7 166/166 → S8 177/177 → 最终边界复查及S9/S10 180/180。各阶段通过后才继续。

独立安装验收：在项目之外安装1.1.1 wheel，并确认导入来自独立site目录；重跑180测试通过。CLI实际执行demo、validate、revenue、diff、snapshot及“编辑→发布BLOCK→人工再批准→发布”闭环。单价730→731后满售收入52390520→52391214（增加694），旧snapshot字节不变。证据：outputs/v1_1_1/INSTALLED_PACKAGE_TESTS.log、INSTALLED_PACKAGE_SMOKE.json。

## 3. 写入口及批准生命周期

风险：批准仅是状态字段时，直接改payload可能保留旧批准。现正式应用编辑入口统一为ApplicationService，CLI与未来GUI不得直接操作ModuleState生命周期。

```text
get_module_data（副本）
 → update_module_data（整份替换）/ apply_changeset（已有typed path替换）
 → canonical相等：完全不变
 → canonical不同：module DRAFT / approval_ref=None / data_version递增-rN
                  project DRAFT / approval_ref='' / version递增-rN
 → validate / calculate（DRAFT可预览）
 → approve_module（人工引用 + 当前data_version）
 → approve_project（人工引用 + 当前project.version；检查所有启用模块）
 → create_snapshot（WARNING需要确认；BLOCK禁止）
 → export_artifact
```

- 改票价后无需GUI同步行级price_version；Rule同理。纯函数Module.prepare_revision由所属模块维护嵌套版本/批准字段，Kernel不认识业务字段。
- 无变化不增版本；反复修改为 `原版本-r1`、`原版本-r2`，不堆叠-edited。一次原子changeset只增一次版本。
- methods返回独立Project；get返回payload副本。patch无效或依赖变化失败不修改输入。不支持负索引、bool索引、越界或标量穿透。
- patch只替换已有路径；增加/删除字段或行用整份update。save_project完整验证后持久化；跨模块编辑可先在内存连续修改、修正约束后再保存。
- approve接口只记录明确的人工作用，不产生或验证真实批准，不存在auto_approve。旧版本和空引用拒绝；已批准版本不能随意改写批准引用。
- 整份外部JSON导入统一DRAFT，不能用load/--data带入修改后的旧批准。手工修改TOML也会使打开后的项目DRAFT；项目ID冲突拒绝。
- enable既有模块时替换payload走同一生命周期；replace为已启用模块仍识别配置变化。无变化enable/disable不增版本。
- Project/dataclass、SQLite与插件不是恶意代码安全边界：不支持调用方绕过服务自行篡改内部对象再声称已批准。未来桌面应用只持有和提交服务返回的工作副本，不把内部可变对象当写接口。

## 4. Provider关系

缺陷是消费能力却依赖官方具体ID，或没有声明实际消费的schedule。现检查清单：

|消费者|必需能力|可选能力|
|---|---|---|
|Pricing|schedule|—|
|Seating|schedule, prices|—|
|Pass / Travel|capacity, prices|—|
|Rights|capacity, prices|—|
|Revenue|capacity, demand, prices, schedule|rights|
|Inventory|capacity|rights|
|Tasks|—|schedule|
|Schedule|—|venues|
|Rule模块|schedule|—|

Registry只增加通用optional_capabilities排序支持；多提供者仍冲突，缺必需提供者BLOCK，缺可选提供者不自动启用。

HARD-007用custom.pricing替换官方Pricing，所有相关模块继续运行；额外测试替换Schedule和Rights，分别验证Tasks时序和Inventory约束仍执行。quality.declarations的finance.revenue可选依赖保留，因为summary路径使用该具体输出契约。

## 5. Session/Venue

Schedule row新增可省略/null的venue_id；非空时必须有唯一venues Provider，并存在相应键。Venue返回venue_id→row，支持多个场馆。删除仍被引用场馆BLOCK。未启用Venue且无引用PASS。

本轮不增加“每场必须分配场馆”配置，不做地图、经纬度、房间层级或现场安全计算。

## 6. Rights收入确认口径

策略FACE_VALUE/FIXED_PRICE/DISCOUNT_RATE仍只决定有效单价。新增必填billing_basis独立决定计费票张：

|口径|权益计费票张|权益收入|预计履约票张|
|---|---|---|---|
|ALLOCATED|quantity|quantity × effective_unit_price|quantity × fulfillment|
|REDEEMED|quantity × fulfillment|quantity × fulfillment × effective_unit_price|quantity × fulfillment|

100张、单价300、履约80%时，分别收入30000/24000、履约均80；履约0时分别收入30000/0、履约均0。公开池收入不受billing_basis影响。

收入行/汇总明确输出public_expected_tickets、rights_allocated、rights_expected_fulfilled、rights_revenue_tickets、revenue_tickets、fulfilled_tickets、revenue_basis、public_revenue、rights_revenue、revenue。均价分母明确；0分母null。汇总revenue_basis记录每种基础对应的分配量，不把混合口径标成单一口径。删除旧歧义tickets/expected_tickets/average_price字段。

容量满售收入仍假定全量销售及全量履约；情景按计费基础分支。没有新增结算、财务确认或自动价格决策。

## 7. 最小Rule Scope

五个Rule模块共用同一结构：`{"type":"ALL"}` 或 `{"type":"SESSION","session_ids":["S01","S02"]}`。ALL不允许附加过滤器；SESSION非空、唯一、外键存在。rule_id唯一，有效期非空、合法。

冲突条件是“实际适用场次有交集 **且** 半开有效期有正长度重叠”，不是只比较scope对象是否完全相等。因此ALL/SESSION、部分SESSION交集也能识别；时间仅相接不冲突。

- Refund可以不同规则覆盖不同场次；逐条声明coverage/windows必须闭合，未声明范围不自动补造。
- Identity/Transfer允许相邻版本共同连续覆盖所辖每场销售至结束，空档BLOCK。
- RightsReturn/Launch基于所辖场次检查业务节点，仍要求每条包含其声明节点；不是动态优先级/继承引擎。
- 不做产品、渠道、优先级、多维覆盖。Scope数组只重排不产生业务diff。

## 8. 显式迁移与历史

应用版本1.1.1；容器format_version仍1.1。Schedule、Rights、Rule模块显式升级schema 2/module 1.1.1，Revenue因输出语义变化升级module 1.1.1/schema仍1；其他模块继续自己的既有版本。

- v1.0适配器继续可用，明确补REDEEMED和ALL；保留原经济语义。
- v1.1工作态在新实现下先BLOCK，通过migrate_project统一显式迁移后才保存。旧Rights映射REDEEMED、旧Rule映射ALL；变化模块及项目需要重新批准。
- 旧Snapshot、旧数据库样本、旧发布件、v1.0/v1.1测试报告不改写。旧快照hash仍可核验，不用新业务实现重新解释旧发布件；如需重算旧版，用对应Git版本及插件。
- 原140测试不需要改断言；它们通过v1.0适配器得到当前schema。新增兼容测试直接使用仓库真实v1.1合成工作样本和旧snapshot，避免只测新样本。

## 9. Kernel架构自检

本轮Kernel仅两个文件增加通用协议：contract.py的prepare_revision/optional_capabilities、registry.py的可选能力排序与描述。没有引入模块具体ID、ticket price、refund、travel、rights或venue业务逻辑。原静态隔离测试继续通过，额外源码扫描记录在outputs/v1_1_1/ARCHITECTURE_CHECK.json。

CLI只调用ApplicationService，不调用具体业务引擎。模块计算仍固定Decimal上下文、上下文副本、有限输入与精确聚合；不可变Snapshot实现未重写。

## 10. 已知限制 / POST-DESKTOP ITERATION

- 单用户串行工作态；没有多窗口并发冲突协调、撤销栈或跨SQLite/TOML文件事务。先在桌面使用中复现需求再补。
- 草稿必须修正BLOCK才能持久化；未来可根据真实编辑摩擦增加草稿暂存，不绕过发布门禁。
- 人工批准引用不是签名；可信本地插件和管理员可操作Python/文件，不声称权限或安全隔离。
- Rule不是复杂覆盖引擎；Refund只验证声明期，未定义的产品/渠道业务需后续明确输入合同后再扩展。
- 旧快照只读可核验；跨插件语义版本的重算需要对应旧实现，不提供自动降级。
- 尚无GUI、真实数据、真实结算或生产部署。Desktop下一阶段建议只做模块配置、结构化编辑、门禁查看、计算对账、明确人工批准和快照导出。

上述为范围边界和后续使用验证项，不据此继续扩大Kernel。本轮到此冻结主架构。
