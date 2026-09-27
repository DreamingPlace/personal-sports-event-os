# Sports Event OS Modular Kernel v1.1

## 边界

```
CLI / 将来GUI
    ↓ ApplicationService（结构化对象，不依赖stdout）
    ├─ Project Manifest + ModuleState → SQLite
    ├─ Registry（importlib.metadata.entry_points）
    ├─ Kernel Gate → Module Validators → Cross-module Validators
    ├─ Context → 各模块calculate / capability provider
    ├─ Kernel Diff → 各模块diff
    └─ Gate → Immutable Snapshot → 各模块export
```

Kernel位于 `src/sports_os/kernel/`：Project/ModuleState/Module/Context、Registry、结构校验、依赖DAG、通用能力索引、Evidence/Provenance、模块版本/hash、SQLite存储、不可变快照、模块级Diff。没有travel/refund/ticketing业务字段、业务模块导入或按模块ID的if/elif分发。静态回归测试验证这一点。

官方业务模块位于 `src/sports_os/modules/`，每个模块拥有schema及校验/差异职责。Schedule/Venue/Task/Decision都是模块，不强制塞入Kernel。

v1.0 `models/schema.py` 仅保留用于旧格式读写/迁移/回归，默认v1.1路径不导入这个schema。旧gate已按seat/inventory/pricing/rules/tasks/products/demand/evidence拆到 `validators/legacy_checks/`。新的 `kernel/gate.py` 只管通用契约。不是把所有业务分支换个名字再放回一个gate。

## Module Contract

`Module`是可继承协议：

- 标识：module_id、module_version、schema_version。
- 依赖：dependencies（模块ID）、optional_dependencies（启用才排序）、requires_capabilities（唯一启用提供者）、provides。
- schema()：模块自有受控结构，未知字段默认拒绝。
- validate(context, gate)：本模块输入和语义。
- cross_validate(context, gate)：与已启用Provider之间的约束。
- calculate(context)：可省略，默认None。通过Context消费依赖结果，禁止偷读未启用payload。
- diff(old,new)：模块按自身业务键解释差异，可重载canonical_row。
- export(context)：可省略，默认None。
- release_requirements(context,gate)：发布前额外约束，可省略。
- migrate(old_version,old_schema,payload)：默认抛错，**必须显式实现**；不能把新代码静默用于旧版本数据。

Context复制输入并缓存一次调用内的确定性结果；返回副本。插件是受信任进程内代码，不提供恶意插件隔离。entry_points真正支持独立Python包；验收测试创建临时独立distribution元数据并成功计算42，无修改Kernel。

## Provider契约

- schedule：session_id映射、首末场时间、可选销售期。
- prices：`(session_id, price_class_id) → Decimal单价`。
- capacity：`(session_id, zone_id, tier) → 容量、price_class和展示信息`。
- rights：同容量键 → quantity、effective_unit_price、expected_fulfillment[scenario]。只有Rights解释商务定价策略。
- demand：scenario → 同容量键 → Decimal需求率。Revenue不读取session_rates或tier_rates。

Provider冲突、缺失和循环均BLOCK。默认Demand是 `MultiplicativeDemandModel`；`DirectDemandModel`提供独立直接需求输入，替换测试证明同经济事实结果相同。可增加其他模块提供demand；Kernel不认识其内部模型。

## 数据与版本

SQLite包含projects、module_state、snapshots、snapshot_modules。每个模块独立payload/schema版本/data_version/status/approval_ref/hash。project.toml是可编辑模块manifest；打开项目时覆盖数据库中最近保存的manifest。`save_project`验证后保存SQL和manifest；它们是两个本地文件，不声称具备跨文件事务。异常中断后应核对manifest再保存；历史快照不依赖工作manifest。

Snapshot冻结完整manifest（包括显式false）、启用模块payload、模块/Schema/数据版本、批准引用、内容hash、来源证据、质量结果和创建时刻。禁用模块残留数据不进入快照。record_hash覆盖元数据，content_hash覆盖冻结项目，snapshot_modules逐项核对。导出manifest的files值为规范JSON字符串内容的SHA256（不是直接文件字节hash），验证时需使用kernel.data.digest(text)。SQLite禁止UPDATE/DELETE，导出前再次核验；旧记录只读。

同一个项目version不能对应不同冻结内容，同一个已批准模块data_version不能更换内容后复用。工作态可以编辑，但新快照需要新版本和人工批准。哈希不是签名，管理员仍有能力修改磁盘/代码；不把它描述为安全认证。

## Application Service

`ApplicationService(workspace, registry=None)` 提供create_project、open_project、list_modules、enable_module、disable_module、replace_module、validate_project、calculate_module、compare_versions、create_snapshot、list_snapshots、export_artifact、migrate_module、migrate_v10、save_project等结构化接口。

启停返回副本并将项目标记DRAFT、清空批准引用、变更项目版本；禁用保留状态用于恢复。缺依赖的启停失败且不更改原对象。CLI仅解析参数和选择应用操作，不调用深层业务引擎。未来GUI可复用服务；本次没有GUI。

## 最小外部插件

```python
from sports_os.kernel import Module

class Checklist(Module):
    module_id = 'custom.checklist'
    module_version = '1.0.0'
    schema_version = '1'

    def schema(self):
        return {'type': 'object', 'properties': {}, 'additionalProperties': False}
```

在独立包的pyproject中注册 `sports_os.modules` entry point，安装后启用即可。禁用无需卸载包。重复模块ID在discovery时BLOCK；替换实现必须由调用方显式 `register(replacement, replace=True)`，同时遵守版本兼容检查。

## 适合进入Desktop阶段吗

**可以进入轻量桌面原型，不适合直接生产上线。** 已有无票务项目、插件发现、服务边界、依赖/快照/迁移测试。桌面下一步应仅提供模块配置、结构化输入、门禁查看、对账预览，不新增真实票务连接或自动发布。仍需实测编辑体验、跨文件恢复、插件安装信任流程和备份恢复；未建立生产并发及权限机制。

## 内置模块与依赖

以下清单由当前Registry生成，能力依赖也必须满足；不是固定运行模式。

|模块|必需模块|必需能力|可选模块|提供能力|
|---|---|---|---|---|
|core.schedule|—|—|—|schedule|
|core.venue|—|—|—|—|
|demand.direct|—|capacity|—|demand|
|demand.multiplicative|—|capacity|—|demand|
|finance.revenue|ticketing.pricing|capacity, demand|ticketing.rights, product.pass, product.travel|—|
|product.pass|ticketing.pricing|capacity|—|—|
|product.travel|ticketing.pricing|capacity|—|—|
|project.decisions|—|—|—|—|
|project.tasks|—|—|core.schedule|—|
|quality.declarations|core.schedule|—|finance.revenue|—|
|ticketing.identity|core.schedule|—|—|—|
|ticketing.inventory|—|capacity|ticketing.rights|—|
|ticketing.launch|core.schedule|—|—|—|
|ticketing.pricing|core.schedule|—|—|prices|
|ticketing.refund|core.schedule|—|—|—|
|ticketing.rights|ticketing.seating, ticketing.pricing|—|—|rights|
|ticketing.rights_return|core.schedule|—|—|—|
|ticketing.seating|core.schedule, ticketing.pricing|—|—|capacity|
|ticketing.transfer|core.schedule|—|—|—|
