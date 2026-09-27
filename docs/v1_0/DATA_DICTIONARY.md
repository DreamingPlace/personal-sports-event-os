# DATA_DICTIONARY

所有输入仅允许合成数据。schema_version固定1.0，synthetic必须为布尔true；未知字段拒绝，数值不接受字符串、布尔值、NaN或Infinity。源字段使用JSON数字，运算使用Decimal，输出金额以十进制字符串保留精度；不是把文本当数值来源。

## 根字段

data_version、price_version、rules_version标识各自批准集合；status为DRAFT/APPROVED/PUBLISHED/RETIRED；approval_ref为人工提供的引用，未批准可为null。snapshot_id在工作数据为null，冻结后生成。quality_evidence只用于检查外部声明，不驱动收入。

## 字段清单

以下清单与运行时schema来自同一份代码；完整机器定义见data/schemas/event-master.schema.json。

### event

|字段|类型／枚举|必填|
|---|---|---|
|event_id|string|是|
|event_name|string|是|
|year|integer|是|
|venue|string|是|
|timezone|string|是|
|status|DRAFT, APPROVED, PUBLISHED, RETIRED|是|

### sessions

|字段|类型／枚举|必填|
|---|---|---|
|session_id|string|是|
|event_id|string|是|
|stage|string|是|
|start_time|string|是|
|end_time|string|是|

### seating

|字段|类型／枚举|必填|
|---|---|---|
|session_id|string|是|
|zone_id|string|是|
|tier|string|是|
|visibility|CLEAR, RESTRICTED|是|
|physical_capacity|integer|是|
|functional_hold|integer|是|
|broadcast_hold|integer|是|
|free_rights|integer|是|
|other_hold|integer|是|
|paid_rights|integer|是|
|deduction_refs|object|是|

### prices

|字段|类型／枚举|必填|
|---|---|---|
|price_version|string|是|
|session_id|string|是|
|tier|string|是|
|price|number|是|
|status|DRAFT, APPROVED, PUBLISHED, RETIRED|是|
|valid_from|string|是|
|approval_ref|['string', 'null']|是|

### inventory

|字段|类型／枚举|必填|
|---|---|---|
|inventory_id|string|是|
|session_id|string|是|
|zone_id|string|是|
|tier|string|是|
|channel|string|是|
|status|AVAILABLE, SOLD, LOCKED, PAID_RESERVED|是|
|allocation_type|PUBLIC, PAID_RIGHTS|是|
|quantity|integer|是|
|as_of|string|是|
|source_ref|string|是|

### products

|字段|类型／枚举|必填|
|---|---|---|
|product_id|string|是|
|product_type|SINGLE, PASS, TRAVEL|是|
|included_sessions|array|是|
|price|['number', 'null']|是|
|price_claim|INDEPENDENT, SUM_FACE_PRICES|是|
|travel|object|否|

### rules

|字段|类型／枚举|必填|
|---|---|---|
|rule_id|string|是|
|rule_type|refund, transfer, identity, rights_return, launch|是|
|version|string|是|
|content|object|是|
|valid_from|string|是|
|valid_to|string|是|
|status|DRAFT, APPROVED, PUBLISHED, RETIRED|是|
|approval_ref|['string', 'null']|是|

### tasks

|字段|类型／枚举|必填|
|---|---|---|
|task_id|string|是|
|title|string|是|
|owner_role|string|是|
|due_at|string|是|
|depends_on|array|是|
|status|TODO, DOING, DONE|是|
|acceptance|string|是|
|proof|['string', 'null']|是|
|phase|PRE_EVENT, DURING_EVENT, POST_EVENT|是|

### decisions

|字段|类型／枚举|必填|
|---|---|---|
|decision_id|string|是|
|issue|string|是|
|options|array|是|
|decision|string|是|
|reason|string|是|
|approved_by_role|string|是|
|effective_at|string|是|
|source_ref|string|是|
|confirmed|boolean|是|
|changed_paths|array|是|

## 业务键与派生字段

|对象|业务键／来源|说明|
|---|---|---|
|Event|event_id|一个工作库当前维护一个赛事；不做多租户|
|Session|session_id，外键event_id|时间必须ISO8601带UTC偏移；按Event.timezone判断年度|
|Seating|session_id + zone_id + tier|物理容量是该场该座区票档的容量；同场跨座区可累加|
|sellable_capacity|physical_capacity−functional_hold−broadcast_hold−free_rights−other_hold|派生函数和SQL视图提供，不允许重复手填|
|paid_rights|付费权益分配数量|仍在sellable内，不作为扣减项；公开池=可售−付费权益|
|deduction_refs|四类扣减各自的来源ID列表|正数扣减需要来源；同一池内重复ID阻断。仅凭不同ID无法认定物理席完全不重叠|
|Price|session_id + tier|当前数据只持有一个生效price_version；每档价适用于同场所有该票档座区|
|Inventory|inventory_id，关联座区键|allocation_type分PUBLIC/PAID_RIGHTS；SOLD、LOCKED、AVAILABLE、PAID_RESERVED是互斥状态|
|Product|product_id|included_sessions是映射数组：每项明确session_id、zone_id、tier、ticket_quantity|
|ticket_quantity|SUM(included_sessions.ticket_quantity)|SQL产品视图与收入输出提供；表示每份产品占用的票张，不是人数|
|price_claim|INDEPENDENT / SUM_FACE_PRICES|后者price=null时自动求和；提供数字时属于需核验的总和声明|
|Rule|rule_id及全局rules_version|content随rule_type使用受控结构；不是任意无法检查的长文本|
|Task|task_id，depends_on引用task_id|禁止循环；DONE必须有proof；owner_role而非人员信息|
|Decision|decision_id，changed_paths|精确绑定被改字段；confirmed及来源／角色齐全才标输入已确认原因|

## 需求与费用口径

- scenarios.low/mid/high均完整包含每场session_rates、每档tier_rates及paid_rights_rate。
- public_q=session_rate×tier_rate，每个因子在[0,1]；付费权益q独立。
- 同一场次座区：公开预期票=(sellable−paid_rights)×public_q，权益预期票=paid_rights×paid_rights_rate。
- “可售率”按跨场座席机会计算，不把16场席位总量说成场馆容量。
- “平均票价”=同口径收入÷同口径预计票张；0分母为null，不伪造0元均价。
- 金额单位为DEMO_CURRENCY；没有合同费率、税务、结算或银行到账数据。

## 旅行包

guests按人，room_quantity/expected_rooms按房，nights按房晚，room_cost按房晚成本，service_per_guest按人。成本=房数×房晚×房成本＋人数×每人服务成本＋other_cost。

expected_rooms表达产品已声明的房间配置；不假定所有双人包一定一间。演示包明确一间，若实际计费两间则BLOCK。报价字段是输入供应报价，必须与所选markup/margin方法核对；不将其当利润。

## 规则内容

当前v1为一个赛事一套全局规则；批准版本要求以下五类各一条，不支持同类多套按产品／渠道分域规则。

- refund：coverage_start/end、windows[]的start/end/fee_rate；半开区间[start,end)，边界相接不是重叠。
- launch：denominator固定PUBLIC_POOL；rounds[]的at/fraction，三轮是演示数据配置，引擎支持其他轮数；共同分母比例合计必须1。
- transfer：allowed布尔值。
- identity：mode文字标识，不保存个人身份信息。
- rights_return：hours_before非负整数。

## 数据不是从哪里来

本项目不包含公司名称、合作方原稿、真实观众、订单、身份证、手机号或银行账户。固定门票数与价格全部为合成；回归TEST-004按用户指定的合成错误数值独立构造，不参与演示经营结果。
