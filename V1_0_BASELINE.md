# v1.0 冻结基线

- 基线提交：8eb00c613f4270212639df3c1e0e4d8a42acb7af（GitHub main 初始发布）。
- 修改源代码前已阅读 README、IMPLEMENTATION_REPORT、TEST_REPORT、ARCHITECTURE、BUSINESS_RULES、DATA_DICTIONARY，全部 src/sports_os 与 tests。
- 实际执行：`python -m unittest discover -s tests -v`。
- 结果：72 / 72 PASS；0 FAIL、0 ERROR、0 SKIP。日志：outputs/v1_1/S0_BASELINE.log。
- 数据范围：仅仓库合成数据；未读取公司资料或 U 盘。
- 原始 v1.0 数据、报告、SQLite 和快照保留；v1.1 使用独立库，不将旧快照改标为新格式。

## 已确认的修复点

旅行漏价路径、非退款规则未验证适用期、逐座区提前舍入、产品映射数组顺序敏感、价格键缺 price_class、权益强制面值均可由当前代码确认。先修复并回归，再引入模块内核。
