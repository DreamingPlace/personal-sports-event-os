# 架构入口

当前版本采用真正的模块内核。完整架构与插件协议见 [V1_1_ARCHITECTURE.md](../V1_1_ARCHITECTURE.md)。

- kernel/：通用身份、注册、依赖、结构、版本、证据、快照、存储、模块级Diff。
- modules/：独立业务schema、validator、calculate、diff、export。
- application/：稳定服务与显式v1.0迁移/兼容适配器。
- cli.py：调用应用服务，无深层业务实现导入。
- validators/legacy_checks/：仅v1.0兼容域检查。

旧架构已保存在 [v1_0/ARCHITECTURE.md](v1_0/ARCHITECTURE.md)，只说明旧数据格式，不代表当前Kernel。
