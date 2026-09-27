# Sports Event OS Modular Kernel v1.1

离线、确定性、完全合成数据的个人赛事工具。**Kernel 不认识票价、座席、退款或旅行包**；业务由可独立安装的 Python 模块提供。无 GUI、AI、网络平台连接、自动定价或真实库存操作。

## 安装与测试

Python **3.11+**，推荐独立环境：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[excel]'
python -m unittest discover -s tests -v
python tests/run_v11_acceptance.py
```

Windows 激活用 `.venv\Scripts\activate`。核心仅标准库；`excel` 用于保留的只读 Excel 适配器及其测试。不要跳过包安装：模块来自安装元数据的 `sports_os.modules` entry points；仅设置 PYTHONPATH 不等于完成安装。离线且已有 setuptools≥68/openpyxl 时可 `python -m pip install --no-build-isolation --no-deps -e .`。

基线 **72 项**，当前完整验收见 **V1_1_TEST_REPORT.md**；所有输入均为虚构。旧版本文档和批准快照保留，不改标为 v1.1。

## 立即运行

在项目根目录：

```bash
python -m sports_os modules
python -m sports_os demo
python -m sports_os validate
python -m sports_os revenue
python -m sports_os diff version_a version_b
python -m sports_os snapshot
```

Demo 是 **2027 Global Racket Masters**（16场、4阶段、5票档、8040物理席），使用模拟批准引用。现成 Demo 已随仓库提供；重复运行不会覆盖用户编辑过的数据。每条命令均支持 `--workspace /path/to/local-workspace`，所有路径限制在该独立目录内，拒绝 `/Volumes` 与越界符号链接。

不售票项目也可完整运行：

```bash
python -m sports_os demo --profile non-ticketed-event --workspace ./outputs/my-free-event
python -m sports_os validate --workspace ./outputs/my-free-event
python -m sports_os snapshot --workspace ./outputs/my-free-event
```

Profile 仅预填启用清单。没有 `profile == ...` 业务分支，不是限定项目只能有三种模式。已有预设：`ticketed-indoor-event`、`multi-session-tournament`、`non-ticketed-event`。不售票预设没有任何票务数据要求。

## 输入、工作态与输出

|位置|用途|
|---|---|
|project.toml|工作态项目身份和模块启停配置；打开时显式读取|
|data/modular.sqlite|模块工作payload、模块版本、内容hash及不可变快照|
|data/modular_demo/*.json|可复现合成A/B输入样本，不是第二个自动同步数据源|
|data/schemas/modules/*.json|各模块独立schema；无巨型业务根schema|
|outputs/V1_1_QUALITY_GATE.json|质量结果；每条违规均含七个规定字段|
|outputs/V1_1_finance.revenue.json|精确收入预览、阶段/票档/场次汇总和敏感性|
|outputs/V1_1_DIFF.json|模块增删、元数据、模块自行解释的业务差异|
|outputs/releases/SN11-*/|冻结manifest、模块版本/hash、批准引用、结果和完整性清单|

`validate`：PASS/WARNING 返回0，BLOCK返回2；输入错误返回2。任何 BLOCK 禁止 calculation/snapshot/export。WARNING 创建快照需要 `--ack-warnings`。旧预览文件可能来自上一次成功运行；不要把“文件存在”当本次成功。

金额在服务层保留 Decimal。JSON 将 Decimal 输出为**精确十进制字符串**；这是计算结果，不是输入数值替代。只在阅读展示时四舍五入到分，不能将取整显示值回灌。分组显示额相加可能有分币尾差；精确汇总严格闭合。

## 修改、启停、替换

```bash
python -m sports_os export-data
# 编辑 outputs/working-project.json，数据输入仍为JSON数字。
python -m sports_os validate --data outputs/working-project.json
python -m sports_os revenue --data outputs/working-project.json
python -m sports_os load outputs/working-project.json
python -m sports_os disable product.travel
python -m sports_os enable product.travel
python -m sports_os calculate ticketing.rights
```

禁用保留payload以便重新启用，但不运行其schema/validator/calculation/diff/export，快照只包含启用模块的payload。未安装且禁用的模块也不会阻塞。启用新模块用 `--payload path/to/payload.json`；缺依赖、能力冲突或依赖环立即BLOCK，不静默补默认值。

替换 Demand 示例：`replace demand.multiplicative demand.direct --payload data/direct-demand.json`。数据结构见字典。更换插件实现可通过 `Registry.register(replacement, replace=True)` 显式注入；插件升级必须提供并执行 `migrate_module()`，旧payload不默认为兼容。

CLI启停/替换会把项目设为DRAFT，需要重新批准。独立产品、权益、收入、库存均可启停，但依赖和跨模块约束不会被绕过：**禁用Rights后库存仍含付费权益分配时，必须人工处理或禁用库存，系统不替你改池**。

## 从空项目开始

```bash
python -m sports_os create --id SYNTHETIC-NEW --name "Synthetic community event" --timezone UTC --workspace ./outputs/my-project
```

生成合法但未批准的裸Kernel项目。加 `--profile` 只写入推荐manifest及 `outputs/project-skeleton.json`，**不编造业务payload**；按独立schema补齐各启用模块，再 `load`。批准必须由人输入 APPROVED/PUBLISHED 与非空 approval_ref；程序不会自动批准。

## v1.0迁移与兼容

```bash
python -m sports_os migrate-v10 data/demo/version_a.json
# 旧版原始工作流（显式兼容入口）：
python -m sports_os --legacy validate
```

如果已经编辑当前模块工作库，先导出备份，迁移会显式替换工作态。迁移只接受v1.0工作数据（snapshot_id=null）。旧SN-*快照仍为1.0，不伪装为SN11-*；旧SQLite `data/event.sqlite` 不改。详见 [迁移说明](V1_1_MIGRATION.md)。

保留 v1.0 类型/schema/SQL视图、Excel只读检查和发布能力作为兼容适配器；它们不是新Kernel实现。v1.0 CLI同样经 ApplicationService 转交兼容应用服务。新增模块不需要修改旧schema/gate。

## 第三方模块

独立本地可信 Python 包声明：

```toml
[project.entry-points."sports_os.modules"]
"custom.checklist" = "custom_package:Checklist"
```

继承 `sports_os.kernel.Module`，实现 `module_id`、`schema()`；按需实现validate、cross_validate、calculate、diff、export、release_requirements、migrate并声明依赖。calculate/export可不实现。安装后`modules`即能发现，不需修改Kernel注册表。完整示例见 [架构](V1_1_ARCHITECTURE.md)。插件是可信Python代码，不是沙箱。

## 边界

- 原型适合继续做**只读/轻编辑桌面原型**，不等于生产票务系统已验收。
- 每规则模块目前一条全局规则，未实现多产品/渠道作用域优先级。
- 收入是容量/需求情景，不是实际销量结算；旅行/通票营业额不叠加到已覆盖的座席收入。
- 只有两个内置Demand Provider；历史模型可扩展，但本次不实现AI或真实历史数据接入。
- 同名不同内容、人工批准状态和hash可以校验；审批真伪、证据真实性及插件代码可信度仍由人核实。
- 单用户SQLite；不支持并发编辑协调、分布式权限、插件安全沙箱或真实现场安全判断。

文档：[架构](V1_1_ARCHITECTURE.md) · [迁移](V1_1_MIGRATION.md) · [数据字典](docs/DATA_DICTIONARY.md) · [业务规则](docs/BUSINESS_RULES.md) · [测试](V1_1_TEST_REPORT.md)
