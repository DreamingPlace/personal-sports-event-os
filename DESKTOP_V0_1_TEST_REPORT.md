# Desktop v0.1 验收报告

- Desktop version: **0.1.0**
- Base commit: `bd99376568d007b13e81e99d939afe2b72cde835`
- New commit: 本报告随 Desktop 实现提交；以该提交的 Git SHA / GitHub 链接为准，最终交付消息给出确切 SHA。
- Environment: macOS Apple Silicon, Node 24.19.0, pnpm 11.19.0, Python build venv 3.12, PyInstaller 6.22.3, Cargo 1.98.1. 应用运行不使用系统 Python。
- Data: 合成 Demo / 临时测试目录。未读写 U 盘，未接真实公司/平台/AI。

## 实际执行
|测试项|输入 / 操作|预期|实际|结果|
|---|---|---|---|---|
|原有 Backend|原 180 tests，不修改已有测试|全部通过|180 PASS|PASS|
|Desktop Protocol|新增 13 tests；health/create/open/schema/data/update/patch/validate/calc/approve/snapshot/diff|全部通过|与旧测试合计 193 PASS，13.487s|PASS|
|错误协议|无效 JSON、重复 key、未知方法、异常、重复/并发 ID|结构化错误、最多执行一次|13-test suite 覆盖|PASS|
|持久化失败|合成磁盘异常|不替换 session state|原 state 保持|PASS|
|不完整草稿|新建缺必填规则项目、重开、篡改 hash|可保存 DRAFT，不能快照；篡改拒绝|符合预期|PASS|
|Snapshot 计算隔离|冻结旧价格，再改工作态价格|旧快照结果不变，工作态更新|后端回归及打包 smoke 均验证|PASS|
|Frontend unit|10 个控制/DTO/状态测试|全部通过|10 PASS|PASS|
|Frontend lint/build|TypeScript + ESLint、Vite production|无错误|PASS；JS gzip约104 KiB|PASS|
|E2E 1|空项目向导、启用模块、隐藏 disabled Revenue/Travel、依赖拒绝、草稿离开、Escape|行为完整|PASS|PASS|
|E2E 2|真实 frozen sidecar：Demo→改价→DRAFT→BLOCK→Gate→Revenue→模块/项目批准→双快照→只读→两种diff→重开|行为完整|PASS|PASS|
|E2E 3|模拟传输断开|可理解错误和重新连接入口|PASS|PASS|
|Accessibility|axe 检查项目首页、概览、Gate、Revenue、批准 Dialog、只读表格；键盘编辑/Tab/Escape|零违反；可完成关键路径|最终 0 violations；键盘测试通过|PASS|
|窗口尺寸|1440×900、1280×800、1040×700|无整窗横向溢出，导航/表格可用|自动检查及截图审查通过|PASS|
|Impeccable|安装项目 hook；detector + synthetic hook event|规则可执行，最终无 deterministic findings|detect=[]；hook 返回有效结果；原生 host trust 需用户按提示批准|PASS / trust caveat|
|Motion review|Emil 标准审查 + 原生批准弹窗|克制、可中断、键盘即时、reduced motion|符合 DESIGN.md；非逐帧性能测量|PASS|
|cargo check|Rust bridge/config|编译通过|PASS|PASS|
|tauri dev|实际启动开发窗口/sidecar|能启动|解除 macOS 沙箱测试限制后运行|PASS|
|tauri build|Release .app|真实 macOS bundle|33.21 MiB app 成功生成|PASS|
|Packaged sidecar smoke|App 内置二进制；PATH=/nonexistent|无 Python 环境完成 11 个检查|Registry 19/19；创建、编辑、批准失效、Gate、收入、批准、快照、两种diff、重启全部 PASS|PASS|
|Packaged native smoke|通过 macOS UI 实际操作，不是浏览器 mock|完整业务闭环|Demo、731 合成改价、DRAFT、BLOCK、PASS、Revenue、两级批准、两个快照、diff、退出重开、READ ONLY 均确认|PASS|

最终 E2E：**3 tests PASS，11.0s**。初次构建发现缺 icon；初次 axe 发现 footer 角色和只读滚动区域问题，已修复。macOS 沙箱首次阻止浏览器 Mach port / PyInstaller semaphore，使用显式执行权限完成验证，不将被阻止的运行算作通过。测试选择器/动画稳定等待也已修正；没有删除断言、关闭 axe 规则或使用伪造业务返回。

## 原生值核对（纯合成）
工作态将 S01/VIP 从 730 改为 731 后，满售收入由后端显示为 **52391214**。重启后打开旧快照，显示 **52390520**，验证未混用当前价格。旧快照 ID `SN11-382eee168ee742c1d3f13f49` 保持不变，新增第二快照，后端 hash 验证通过。

## 设计资源与页面
实际资源使用/取舍、两份参考、集中 critique/audit、统一修复、polish 及停止记录见 `apps/desktop/design/DESIGN_AUDIT.md`。研究前已创建 PRODUCT.md/DESIGN.md。

已实现：Projects、三步向导、Overview、动态模块导航与管理、schema 数据表/嵌套字段编辑器、Quality Gate、read-only Revenue、外部批准引用 Dialog、Snapshots/READ ONLY、Version Diff、错误/空态/载入/断连恢复。

## Known UX Iterations
技术字段对新手偏密；日期以 ISO 时区字符串编辑；无 Excel 批量粘贴、列拖拽或海量行虚拟化；差异中批准元数据较多。普通关闭/切换保护未提交编辑，但 Cmd+Q/强退可能丢弃界面草稿。

## Known Technical Limitations
仅当前 Apple Silicon/macOS 实测；未 notarize/未 App Store 分发。未做完整 VoiceOver、跨机器 Gatekeeper、Intel 和大规模性能验收。单写者项目目录；没有进程间编辑锁。CLI 不隐式读 desktop-draft.json。原生 Codex hook trust 未伪装为已批准。

- No Kernel business rewrite: **PASS**（Kernel / Modules 无修改）
- No AI / real company data / ApplicationService bypass / frontend business formula: **PASS**
- P0 Logic: **0 observed**
- P1 Logic: **0 observed in tested single-writer synthetic scope**
- **DESKTOP_V0_1 = PASS**
- Recommended next: **DESKTOP_V0_2_REAL_LOCAL**（下一阶段需重新审定真实数据边界；本版仍只允许合成数据）
