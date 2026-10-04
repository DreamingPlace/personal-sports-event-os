# Desktop 0.1.1 打包修复 / 2026-10-05

## 问题与根因

用户从 Safari 下载 0.1.0 后，macOS 提示应用“已损坏”。下载副本与原始构建的主程序 SHA256 相同，严格签名验证均报：`code has no resources but signature indicates they must be present`。原配置没有显式 signingIdentity，只留下 linker ad-hoc executable signature，没有封装 bundle resources。之前本机 UI 与 sidecar 功能测试未覆盖这一分发门禁，原下载发行 PASS 已更正。

## 修复范围

- Desktop package / Cargo / Tauri 版本同步至 0.1.1；Kernel 1.1.1 和业务代码不变。
- Tauri 显式完整 ad-hoc 签名 app、主程序与 sidecar，封装 Info.plist 和资源。
- 初次修复在 smoke 中发现 hardened runtime 拒绝 frozen Python 内嵌 dylib（different Team IDs）；添加最小 library-validation entitlement，保留其余 hardened runtime。该失败候选包未上传。
- 新增 package_macos.py：严格签名、资源封装、真实 sidecar smoke、ZIP 解压后重复签名校验；失败不产出 ZIP，不覆盖已有归档。
- 新增 5 个打包回归测试；明确签名完整性不等于 Apple 信任。修正旧验收报告和下载说明。
- 不修改用户 Downloads 副本、项目数据或 U 盘；不移除 quarantine、不更改系统安全策略。

## 实测

|测试项|输入|预期|实际|结论|
|---|---|---|---|---|
|历史失败复现|原构建及下载 0.1.0|识别错误|相同资源签名错误；主程序 hash 相同|PASS（检出缺陷）|
|缺少资源封装|合成未封装 App|拒绝归档|BLOCK，无 ZIP|PASS|
|资源篡改|签名后修改 synthetic resource|拒绝归档|codesign 拒绝，无 ZIP|PASS|
|归档往返|合成合法签名 App|解压后签名有效|有效，Gatekeeper 不冒报通过|PASS|
|已有归档|存在的 ZIP|不覆盖|原内容保留|PASS|
|配置回归|版本、签名、entitlements|版本一致、仅必需例外、保留 runtime|符合|PASS|
|Python 回归|全部旧测试 + 5 个新增|全部通过|最终 198 tests，11.520s，含 entitlement 断言|PASS|
|Frontend|原 10 unit、TypeScript / ESLint / Vite|无回归|10 PASS；lint/build 成功|PASS|
|Tauri build|0.1.1 实际构建|完成完整签名|app / sidecar / main 均签名，明确跳过公证|PASS|
|修复包完整性|codesign --verify --deep --strict；逐个 binary；ZIP 解压|全部有效|PASS，资源封装存在|PASS|
|冻结业务 smoke|已签名 sidecar 及最终 ZIP 解压副本，PATH=/nonexistent|不依赖系统 Python|19 modules，11 项闭环检查含重启全部通过|PASS|
|Gatekeeper 评估|spctl --assess|不得将策略豁免算通过|accepted / override=security disabled；spctl --status 为 assessments disabled|无效环境，NOT VERIFIED|
|Apple 发行资格|syspolicy_check distribution|正式发行须通过|exit 70：Adhoc Signed App；Notary Ticket Missing|BLOCK|
|正常浏览器下载首开|独立正常 Gatekeeper 机器|无损坏提示且信任流程正常|尚未执行；当前机器策略不能证明标准行为|NOT VERIFIED|

当前电脑已有 Gatekeeper assessments disabled；本次只读取，没有修改。不能以本机 `accepted` 证明其他机器可以正常打开。此前 3 项 E2E 与完整 native UI 记录属于 0.1.0，不冒充 0.1.1 的新实测；本补丁未修改前端或业务实现。

## 交付结论

**PACKAGING_INTEGRITY = PASS；LOCAL_SIDECAR_WORKFLOW = PASS；STANDARD_MACOS_DISTRIBUTION = BLOCK。**

仅提供标明边界的私密仓库预发布测试包；0.1.0 标记为不可用，不静默替换其归档或 checksum。0.1.1 ZIP SHA256：

`e1065a41be09e8be5d2e3887ed802f0b1c31f9d7fcc0131b90c9c0acb6bb898c`

正式发行的剩余条件：可用 Developer ID Application 证书、内外层一致签名、Apple 公证及 stapling、正常 Gatekeeper 独立机器浏览器下载验收。不要在聊天或仓库保存私钥/密码。对于本测试版，用户只可自主选择 Apple 官方的单应用“仍要打开”流程；持续“已损坏”或恶意软件警告应停止，不建议绕过。

依据：[Tauri macOS signing](https://v2.tauri.app/distribute/sign/macos/)、[Apple 安全打开应用](https://support.apple.com/en-us/102445)、[Apple 公证](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)。
