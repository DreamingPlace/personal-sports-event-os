# 架构与事实流

## 最小架构

```text
合成JSON输入（schema校验＋引用/类型检查）
       ↓ 显式load事务
SQLite working_state（唯一可编辑业务事实）
       ├─ event/session/seating/price等只读SQL视图
       ├─ Revenue纯函数 → 统一计算行 → 汇总／敏感性／Markdown
       └─ Quality Gate → PASS / WARNING / BLOCK
                              ↓ 人工批准引用＋无BLOCK
                    不可变SQLite snapshot
                              ↓ 哈希核验＋再次门禁
                    同一snapshot的本地发布目录

版本A、版本B → 确定性Version Diff → 字段事实＋来源限定原因
```

SQLite保存一个规范JSON文档，并暴露九类具名SQL视图。不是九份独立维护的表：因此不会产生JSON／表格两套数据同时编辑的问题。关键字段类型、唯一键、外键和依赖环在模型层校验，单事务替换工作文档。SQLite还检查JSON有效性。这个选择针对小型单用户项目；不宣称数据库外键可以对JSON视图自动执行。

## 模块边界

- models：共享schema、确定性合成数据、类型／引用／依赖校验、派生容量与产品占票。
- database：SQLite工作事实与只读视图；不接外部系统。
- revenue：Decimal计算，每行金额到分，汇总同一组行；没有手写摘要总额。
- validators：业务／日期／版本门禁；XLSX适配器是独立只读、有限公式求值器。
- versioning：结构化／文本差异；批准快照及哈希校验。
- exporters：预览和不可覆盖发布目录；临时目录构建完整后再改名落盘。
- cli：用户入口、工作目录边界、退出码与输出。

## 发布不变量

1. 工作数据为DRAFT时可以试算，不能创建批准快照。
2. APPROVED/PUBLISHED及被引用价格／规则需要非空approval_ref；禁止自动补批准。
3. BLOCK禁止快照及发布件；WARNING需人工显式确认。
4. 快照ID由规范化内容SHA256生成。版本、价格、规则和批准引用随快照冻结。
5. 已存快照有SQLite禁止UPDATE／DELETE触发器。重新导入工作数据不改快照。
6. 发布只能接受再次验证通过的快照；所有输出使用同一payload。
7. 同ID重跑输出应相同；已有目录被修改则拒绝覆盖，不“修复”证据。

这是防误操作与可追溯设计，不是抵御拥有本机数据库／代码权限者的安全系统。未实现证书、真实审批仓库验证、多用户授权或数据库迁移框架。

## 目录与安装

源代码采用src/sports_os标准Python包布局；pyproject.toml支持可编辑安装和sports-os命令。demo与schema文件可由已安装包重建，不依赖本机绝对路径。

CLI所有读写限定在--workspace内，且拒绝/Volumes。模型库自身为纯数据函数，不扫描磁盘。测试只创建临时合成输入。

## 失败与恢复

- 错误输入：保存质量报告，退出码2，不更新SQLite／发布件。
- 草案质量问题：修改独立JSON后重跑validate，确认后显式load。
- 已发布内容有错误：回到工作副本修正，改变版本并重新批准；生成新快照，不覆盖旧快照。
- 现有预览文件可能来自上次成功运行；消费者必须检查本次退出码、data_version和snapshot_id。
- 核心不调用网络；Excel解析失败、未知公式及缺依赖不会被静默当作0或PASS。
