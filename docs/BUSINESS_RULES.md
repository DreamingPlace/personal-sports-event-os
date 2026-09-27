# BUSINESS_RULES

## 1. 可复算的收入模型

```text
A[s,z,k] = physical − functional − broadcast − free_rights − other_hold
U[s,z,k] = A − paid_rights
q[s,k,scenario] = session_rate × tier_rate
expected_tickets = U × q + paid_rights × paid_rights_rate
full_revenue = Σ A × price
scenario_revenue = Σ expected_tickets × price
sellable_rate = Σ A / Σ physical
average_price = scenario_revenue / Σ expected_tickets
```

每条数据已经对应单场，不再乘一次场次数；分阶段汇总不会重复放大。付费权益按对应票档价格计费，且没有从收入遗漏。单座区场次收入四舍五入到2位小数，再汇总同一组行；零分母输出null。

SUM_FACE_PRICES且price=null的通票价随门票价自动更新。独立产品售价是决策输入，不擅自随成本变动；价格拆解有矛盾则阻断。套餐额不额外叠加进已含全部座席的票房容量。

敏感性分别测试：全价格+1%且需求不变；有效公开池售罄率+1个百分点、上限1且权益率不变。不假设已识别价格弹性，也不承诺达到情景值。

## 2. 门禁输出契约

每条检查有rule_id、severity、message、source、expected、actual、suggested_action。

BLOCK优先于WARNING，WARNING优先于PASS。无适用违规返回该结构化规则PASS；不表示已验证未提供的资料。schema失效先BLOCK，不对损坏结构继续计算。XLSX专属Q030/031仅在指定工作簿时执行。

|rule_id|检查|严重性|
|---|---|---|
|Q001|结构、类型、唯一键、外键及缺失值|BLOCK|
|Q002|Excel错误值与计算错误|BLOCK|
|Q003|空单元格或缺失引用|BLOCK|
|Q004|硬编码摘要与派生值|不一致BLOCK；当前匹配但硬编码WARNING|
|Q005|分项与总计|BLOCK|
|Q006|百分比闭合|BLOCK|
|Q007|同一指标单位一致|WARNING|
|Q008|负可售库存|BLOCK|
|Q009|容量与付费权益边界|BLOCK|
|Q010|扣减标识重复|BLOCK|
|Q011|年度残留|关键字段BLOCK；背景文本WARNING|
|Q012|开始结束时间与有效期|BLOCK|
|Q013|赛前任务时序|BLOCK|
|Q014|退款窗口重叠|BLOCK|
|Q015|退款窗口空档|BLOCK|
|Q016|批准凭证|BLOCK|
|Q017|草案禁止发布|BLOCK|
|Q018|同名内容冲突|BLOCK|
|Q019|发布件引用规则状态|BLOCK|
|Q020|统一快照引用|BLOCK|
|Q021|通票等于票价之和的声明|BLOCK|
|Q022|旅行包房间数量|BLOCK|
|Q023|markup与margin|BLOCK|
|Q024|库存守恒与时点|BLOCK|
|Q025|产品价格与占票结构|BLOCK|
|Q026|需求情景排序|BLOCK|
|Q027|活动版本一致|BLOCK|
|Q028|任务完成凭证|BLOCK|
|Q029|规则内容结构|BLOCK|
|Q030|可验证的公式范围|BLOCK|
|Q031|Excel业务检查契约|缺契约WARNING；无效契约BLOCK|

## 3. 库存守恒

每个session/zone/tier的所有互斥库存状态之和必须等于可售总池，且使用同一as_of。PAID_RIGHTS的各状态数量之和必须等于paid_rights；已售付费权益仍属于此分配池，不会因由预留转为售出而从账上消失。AVAILABLE等状态不能同时代表同一批座席。

该规则验证输入快照，不修改真实或合成库存以“自动对平”。不同渠道可以分配，但每张票仅在一个互斥状态计数。产品份数转换成逐场占票张数，不直接拿“份”减所有场次总池。

## 4. 时间与版本

- 时间必须带UTC偏移；时区为IANA名称。结束必须晚于开始。
- 赛前任务必须在赛事首场前；赛后任务不能早于赛事结束。
- 退款窗口按[start,end)排序；覆盖期内无重叠、无空档，超出覆盖范围也阻断。
- 发布必须由已批准数据、价格及规则构成；批准引用不能为空或空白。
- snapshot_id必须一致，不能用一个报告中的旧快照掩盖另一个数据版本。
- 同名模型不同内容的声明会BLOCK；快照库还禁止相同data_version对应不同内容，并防止已冻结price_version/rules_version改变内容后复用旧编号。
- “最终／正式”标题不产生批准效力；只有文件名而没有批准信息仍会阻断。

## 5. Excel范围

支持的有限公式独立求值，不依赖已有缓存作为唯一真相。缓存不同于复算值时BLOCK；无缓存但支持公式可计算。未知函数、外部链接、循环、空引用均不按正常数据放行。

不能仅凭数字所在位置推断任意业务总计，因此硬编码摘要需结构化quality_evidence或XLSX totals契约。未配置的任意文字、百分比分母或业务单位，不声称已经自动理解。

## 6. 人工边界

批准证据真实性、定价决定、权益承诺、真实需求、座席安全、投诉补偿与财务付款不是本程序的判断权限。示例approval_ref是合成标记。所有门禁通过也不等于具备真实运营条件。
