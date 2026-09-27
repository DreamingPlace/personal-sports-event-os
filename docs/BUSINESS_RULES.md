# BUSINESS_RULES v1.1.1

## 容量、Price Class与权益

可售池 = physical − functional − broadcast − free_rights − other_hold。免费权益是扣减；付费权益由Rights提供数量，不再嵌入Seating必填字段。

Seating使用 `(session_id, zone_id, tier)` 为业务键，引用 `(session_id, price_class_id)` 的价格。同tier可以不同price_class，多zone也可以共用price_class，不创造假tier。

Rights支持：FACE_VALUE（按面值）、FIXED_PRICE（value为独立单价）、DISCOUNT_RATE（value为实付比例，0.8表示8折）。输出quantity、effective_unit_price、expected_fulfillment[scenario]及必填billing_basis。Revenue不猜权益协议价。

公开池 = 可售池 − Rights.quantity。容量收入 = 公开池×公开价格 + 权益量×权益有效价格；情景公开收入 = 公开池×Demand结果×公开价格。权益收入：ALLOCATED = 权益量×有效价；REDEEMED = 权益量×履约率×有效价。履约票张两种口径始终为权益量×履约率；计费票张和实际履约不得混用。Rights禁用时不分配付费池；若Inventory仍声明该分配会BLOCK，不自动转池。

所有收入核心使用Decimal，有限输入上限1e12、固定80位运算上下文，无逐区quantize。乘积和聚合保留精确值；比例和均价可能是有限精度的除法结果，不参与反向计算。货币展示四舍五入到分，显示值不能回灌。

## Demand

`demand.multiplicative`：场次率×票档系数，只是一种提供者。

`demand.direct`：逐scenario、逐容量键直接输入rate。

均必须完整覆盖容量键且rate在[0,1]。Revenue只消费标准结果；缺Provider、冲突、多余/缺失键BLOCK。包含low/mid/high时要求需求/权益履约率顺序正确。允许其他人工情景名称。敏感性只改变公开池参数，不擅自修改权益合同价。

## Products

每份产品占票 = included_sessions逐容量键ticket_quantity的和。映射数组按session_id/zone_id/tier规范化，仅重排不是变化。单场票占1张；通票和旅行包逐场消耗明确票张。

TRAVEL含任何非票成本或报价时，必须有INDEPENDENT显式总价，禁止price=null + SUM_FACE_PRICES。门票金额 + quoted_non_ticket = 产品总价。报价最多2位小数。

成本 = room_quantity×nights×room_cost + guests×service_per_guest + other_cost。实际计费房间必须等于expected_rooms；每场占票必须等于guests。markup=成本×(1+率)，margin=成本÷(1−率)，不混用，margin<1。

旅行/通票产品单位营业额**不额外叠加**到已经覆盖这些座席的容量票房。这不是完整产品销量/结算/利润模型。

## 时间与规则适用性

规则模块自有applicability，不由Kernel理解：

- identity：覆盖销售开始至末场结束，含入场期。
- transfer：不论允许/禁止，覆盖销售开始至末场结束。
- rights_return：覆盖登记起点至Scope内所有场次对应回流节点，不能只检查首场；节点在半开有效期内。
- refund：规则有效期包含声明coverage_start/end，windows半开区间必须首尾连续，无重叠/空档/倒置。
- launch：比例同分母闭合为1，时点严格递增，在销售期及规则有效期内，且早于Scope内首场。

每个启用规则模块至少一条规则，rule_id唯一，scope必填：ALL不带过滤器，SESSION带非空唯一session_ids且外键存在。同一模块的两条规则只要共享适用场次且半开有效期实际重叠即BLOCK；边界相接允许，无优先级。Identity/Transfer可用相邻版本共同连续覆盖各适用场次的销售至结束期；Refund逐条窗口闭合，不推断未声明覆盖期；RightsReturn/Launch仍要求每条覆盖其所辖业务节点。禁用模块不要求规则存在。此口径是当前官方模块的业务约定，可替换实现，不是Kernel通用真理。

## Gate与发布

Kernel只检查manifest、依赖/能力、schema与版本、Evidence结构、通用批准状态。模块验证自己的业务；Inventory验证Capacity/Rights约束，Products验证Price/Capacity，Revenue验证Demand/Rights结果。

PUBLISHED/APPROVED必须有非空批准引用；发布时所有启用模块也必须已批准。规则/价格行仍接受门禁检查；approve_module通过模块hook显式同步行级批准和版本，不能只手改模块字段绕过门禁。BLOCK禁止计算、snapshot、export；WARNING创建snapshot需确认。

每条违规都有rule_id、severity、message、source、expected、actual、suggested_action。PASS且无违规可返回空findings，不伪造“已检查未提供资料”的条目。

## 禁用与历史

禁用payload保留但隔离，不参加schema/validator/calculate/diff/export，不进入新快照。依赖模块仍启用时不能破坏硬依赖；需要先禁用依赖方或替换Provider。

快照完整冻结模块manifest与版本/hash。启停不会更改历史。版本号复用不同内容BLOCK。批准引用和输入证据只表明有人提供这些标识，不认证现实真伪。

## 保留的声明与Excel检查

quality.declarations校验显式cells/totals/percentages/metrics/documents/named_models/summaries/output_refs。任意自然语言和未知摘要不自动推断业务语义。

v1.0 Excel只读适配器继续可用（`--legacy validate --xlsx ...`）；仅支持算术、SUM/AVERAGE和有限引用，未知公式BLOCK。未迁移成默认Kernel必装能力。

## 编辑生命周期与场馆

ApplicationService的update_module_data/apply_changeset检测canonical内容：变化才使模块、项目DRAFT并清批准，生成递增-rN版本。批准API必须显式给出当前版本和非空人工批准引用。仅批准项目而变化模块仍DRAFT会BLOCK。JSON导入和外部TOML更改不能转移批准。直接改内部dataclass/SQLite不属于受支持应用入口；本地管理员及可信插件不是安全隔离对象。

Session的venue_id可省略或null；非空必须有唯一venues Provider且该ID存在。Venue不启用且无引用完全合法；删除仍被引用场馆BLOCK。本轮没有强制每场分配场馆的额外配置、地图或现场安全判断。
