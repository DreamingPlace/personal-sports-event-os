# Personal Sports Event OS v1.0

本地、完全虚构数据的赛事票务原型。四个模块：**Revenue Model、Quality Gate、Version Diff、Event Master Data**。没有前端、云服务、票务平台连接、外部大模型或真实个人数据。

质量门禁出现 **BLOCK** 时，程序不会生成批准快照或正式发布目录。WARNING 可以查看，但生成快照需要显式 `--ack-warnings`。APPROVED/PUBLISHED 与非空 `approval_ref` 都必须来自输入；snapshot 命令不替你批准数据。

## 1. 环境与安装

要求 Python **3.11或更新版本**，并启用SQLite JSON函数（常规现代Python发行版已提供）。macOS自带的Python 3.9不满足要求。

进入本项目目录后：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[excel]'
```

Windows激活命令为 `.venv\Scripts\activate`。也可用 `python3.11` 等符合要求的解释器。

- 核心功能仅使用Python标准库，无必装第三方运行依赖。
- `excel`选装项提供openpyxl，只用于读取合成XLSX和运行Excel回归测试。
- 不需要Pandas、Streamlit、API Key或外部模型；当前规模没有引入它们的必要。
- 离线且已具备依赖时，可用 `python -m pip install --no-build-isolation --no-deps -e .`。需要已安装setuptools≥68；Excel测试另需openpyxl≥3.1.5。

## 2. 五条验收命令

```bash
python -m sports_os demo
python -m sports_os validate
python -m sports_os revenue
python -m sports_os diff version_a version_b
python -m sports_os snapshot
```

每条命令都可加 `--workspace /path/to/new-local-folder`，全部输入输出都限制在这个独立目录内。拒绝路径越界、符号链接越界及 `/Volumes` 路径；不会访问U盘。

初次 `demo` 创建：

```text
data/event.sqlite                 ← 唯一工作事实源
data/demo/version_a.json           ← 合成输入／复现样本，不是自动同步的第二份主数据
data/demo/version_b.json           ← 合成变更版本
data/schemas/event-master.schema.json
```

演示赛事为 **2027 Global Racket Masters**：16场、4阶段、5票档、每场8040物理席，主／侧座区，侧区标记视野受限；含功能／转播／免费权益扣减、付费权益、3轮开票、高中低需求、16场通票、双人共房旅行包。全部金额、场地和渠道为虚构。侧区标记不是现场安全认定。

`demo`可对未修改的初始数据重复运行；遇到已编辑数据会拒绝覆盖。要重新开始请换一个独立工作目录，不要删除自己的数据。

## 3. 输出在哪里

|命令|输出|含义|
|---|---|---|
|validate|outputs/QUALITY_GATE.json、.md|逐规则PASS/WARNING/BLOCK，七个规定字段齐全|
|revenue|outputs/REVENUE.json、.md|预览；含总额、各阶段／票档／场次、逐座区计算、平均票价、可售率、敏感性及产品占票|
|diff|outputs/VERSION_DIFF.json、.md|结构化或文本差异，证据与原因分开|
|snapshot|outputs/releases/SN-…/|固定批准快照、收入结果、质量结果和文件哈希清单；重复运行不覆盖变动内容|

退出码：`0`＝完成（validate的WARNING也返回0）；`2`＝BLOCK、需确认WARNING、输入错误或路径违规。自动流程必须检查退出码和JSON的status，不能只看输出文件是否存在。旧预览可能仍在，不代表本次运行成功。

发布目录中的 `snapshot.json` 含 snapshot_id、data_version、rules_version、price_version、created_at、approval_ref及完整合成数据。所有发布结果来自该快照，不读后来改变的工作数据。**本地“批准快照”不等于对外发布。** 演示批准引用仅为虚构流程标记，没有真实机构授权效力。

## 4. 如何修改一个价格或座席

```bash
python -m sports_os export-data
# 编辑 outputs/working-data.json 中的输入字段
python -m sports_os validate --data outputs/working-data.json
python -m sports_os revenue --data outputs/working-data.json
python -m sports_os load outputs/working-data.json
python -m sports_os revenue
```

注意：

1. JSON只是显式导入／试算文件；改JSON不会静默改变SQLite。`load`通过校验才原子替换工作数据，不动历史快照。
2. 改价格后收入、阶段／票档汇总和采用SUM_FACE_PRICES的派生产品价自动重算。独立定价的旅行包不会被程序擅自改价；若其票款＋旅游报价不再闭合，门禁会要求处理。
3. 改物理座席后可售量自动重算；库存状态总量若未同步确认，Quality Gate会BLOCK。程序不会为对平而自动增加真实库存。测试分别证明收入联动与库存不一致的阻断。
4. 正式修订应更改data_version／price_version／rules_version，填入新的人工批准引用；只改金额不等于重新获批。v1.0检查引用存在和版本一致，不验证审批文件真伪。
5. 不向主数据重复输入sellable_capacity或汇总收入。前者由字段公式／SQL视图导出，后者来自统一计算行。

## 5. 质量检查输入

### 结构化检查

主数据中的 `quality_evidence` 是待核证据区，不是第二份计算输入。可声明：公式错误／必填单元格、分项与总计、外部摘要、百分比分配、单位、关键标题、同名模型内容以及输出snapshot引用。

指定10类历史问题已写为**合成回归样本**，见tests/fixtures/regressions.json。TEST-004的17280／19980仅为用户指定的错误模式测试数字，不用于演示赛事的经营模型。

### 只读XLSX检查（可选）

```bash
python -m sports_os validate --xlsx data/demo/synthetic.xlsx \
  --excel-contract data/demo/excel-contract.json
```

把合成文件放在工作目录内；示例契约：

```json
{"totals":[{"sheet":"Model","components":["A1","A2","A3"],"total":"A4"}]}
```

可复算范围：数字、`+ - * /`、括号、百分数字面量、单元格／跨表引用、范围、SUM、AVERAGE。循环、外部链接、不支持的函数、命名区域及无法核验的公式**BLOCK**，不假装完整Excel引擎。空引用按缺输入BLOCK，不默认为0。

不提供业务契约时，对任意硬编码摘要不能可靠猜测其含义，因此明确WARNING。原XLSX只读，不重保存、不执行宏、不写缓存。这个适配器不是把任意公司Excel自动变成主数据；正式收入仍只由受控JSON／SQLite输入计算。

## 6. 比较文本和结构化版本

```bash
python -m sports_os diff data/demo/version_a.json data/demo/version_b.json
python -m sports_os diff data/demo/plan_a.txt data/demo/plan_b.txt
```

结构化数据按稳定业务键比较，列表顺序变化不冒充价格变化。通票／旅行映射按明确字段比较；退款及开票窗口按其顺序定位。

“已确认原因”仅来自输入Decision记录中明确匹配changed_paths、confirmed=true且有来源／批准角色的记录。未确认记录标为推测；没有记录就写“原因无法由输入直接确认”。文本只比较新增、删除和替换，语义仍需人工确认；不调用LLM补原因。

## 7. 运行测试

```bash
python -m unittest discover -s tests -v
python tests/run_acceptance.py
```

第二条命令重新执行测试并生成 `TEST_REPORT.md` 及 `outputs/acceptance-results.json`。所有测试都使用内存数据或临时目录，不读取U盘、公司档案和网络。

验收涵盖：十类错误、单价／座席输入联动、独立复算、库存守恒、空引用、单位、时间窗、版本、不可变快照、篡改、CLI退出码、路径隔离和重复运行。

## 8. 范围与限制

- 这是小型本地单用户原型，不是票务交易系统。
- 当前每赛事只支持一套全局规则，各规则类型恰好一条；不做分产品／渠道退款规则的冲突优先级。
- 付费权益默认与对应票档同价；履约率独立于公开池。复杂合同折价未实现。
- 产品有单份占票映射和价格拆解，尚无按产品销量驱动的完整组合销售优化；套餐金额不会与座席容量收入重复相加。
- 库存为已知时点的互斥状态快照，不连接平台、不自动调整或模拟真实出票。
- 扣减重复靠显式deduction_refs识别；不同ID实际指向同一物理座位，仍需现场图或更细座位级数据才能证明。
- 审批引用、Decision证据的真实性由人负责。哈希用于发现变化，不是数字签名、权限系统或法律认证。
- 不做正式合同、支付、公告发送、定价决定、现场安全判断、云部署或真实数据接入。

详见docs/DATA_DICTIONARY.md、docs/BUSINESS_RULES.md、docs/ARCHITECTURE.md，以及IMPLEMENTATION_REPORT.md。
