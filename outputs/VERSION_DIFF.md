# VERSION version_a → version_b

## 【价格变化】

- [修改／数值变化] `prices/S01/VIP/price`：730 → 765
  - 【原因：已确认原因（输入决定记录）】Fictional demand experiment；依据 SYNTHETIC-DECISION-1 / D-DEMO-1

## 【座席变化】

- [修改／数值变化] `seating/S01/MAIN/VIP/physical_capacity`：608 → 620
  - 【原因：无直接证据】原因无法由输入直接确认
- [修改／数值变化] `seating/S01/MAIN/VIP/sellable_capacity`：554 → 566
  - 【原因：无直接证据】原因无法由输入直接确认

## 【库存规则／数量】

- [修改／数值变化] `inventory/S01-VIP-MAIN-AVAILABLE/quantity`：530 → 542
  - 【原因：无直接证据】原因无法由输入直接确认
- [修改／数值变化] `rules/R-launch/content/rounds/0/fraction`：0.25 → 0.3
  - 【原因：无直接证据】原因无法由输入直接确认
- [修改／数值变化] `rules/R-launch/content/rounds/1/fraction`：0.45 → 0.4
  - 【原因：无直接证据】原因无法由输入直接确认

## 【时间变化】

- [修改／文件事实] `rules/R-launch/content/rounds/0/at`：2027-06-01T09:00:00+00:00 → 2027-05-30T09:00:00+00:00
  - 【原因：无直接证据】原因无法由输入直接确认

## 【产品变化】

- [删除／文件事实] `products/SINGLE-DEMO/included_sessions`：[{"session_id": "S01", "zone_id": "MAIN", "tier": "VIP", "ticket_quantity": 1}] → [不存在]
  - 【原因：无直接证据】原因无法由输入直接确认
- [删除／文件事实] `products/SINGLE-DEMO/price`：null → [不存在]
  - 【原因：无直接证据】原因无法由输入直接确认
- [删除／文件事实] `products/SINGLE-DEMO/price_claim`：SUM_FACE_PRICES → [不存在]
  - 【原因：无直接证据】原因无法由输入直接确认
- [删除／文件事实] `products/SINGLE-DEMO/product_id`：SINGLE-DEMO → [不存在]
  - 【原因：无直接证据】原因无法由输入直接确认
- [删除／文件事实] `products/SINGLE-DEMO/product_type`：SINGLE → [不存在]
  - 【原因：无直接证据】原因无法由输入直接确认
- [新增／文件事实] `products/WEEKEND-PASS-DEMO/included_sessions`：[不存在] → [{"session_id": "S15", "zone_id": "MAIN", "tier": "GOLD", "ticket_quantity": 1}, {"session_id": "S16", "zone_id": "MAIN", "tier": "GOLD", "ticket_quantity": 1}]
  - 【原因：无直接证据】原因无法由输入直接确认
- [新增／文件事实] `products/WEEKEND-PASS-DEMO/price`：[不存在] → null
  - 【原因：无直接证据】原因无法由输入直接确认
- [新增／文件事实] `products/WEEKEND-PASS-DEMO/price_claim`：[不存在] → SUM_FACE_PRICES
  - 【原因：无直接证据】原因无法由输入直接确认
- [新增／文件事实] `products/WEEKEND-PASS-DEMO/product_id`：[不存在] → WEEKEND-PASS-DEMO
  - 【原因：无直接证据】原因无法由输入直接确认
- [新增／文件事实] `products/WEEKEND-PASS-DEMO/product_type`：[不存在] → PASS
  - 【原因：无直接证据】原因无法由输入直接确认

## 【规则变化】

- [修改／数值变化] `rules/R-rights_return/content/hours_before`：60 → 72
  - 【原因：无直接证据】原因无法由输入直接确认

## 【文字变化】

- [修改／文件事实] `documents/demo/title/insert:A空@插入点2/B行2-2`：[] → ["Synthetic revised plan; reasons need evidence."]
  - 【原因：无直接证据】原因无法由输入直接确认

## 【版本／其他字段】

- [修改／文件事实] `data_version`：demo-a → demo-b
  - 【原因：无直接证据】原因无法由输入直接确认
- [修改／文件事实] `rules_version`：rules-a → rules-b
  - 【原因：无直接证据】原因无法由输入直接确认
- [修改／文件事实] `price_version`：prices-a → prices-b
  - 【原因：无直接证据】原因无法由输入直接确认

## 证据边界

- 本地确定性比较；不调用LLM、不推断动机。
- 已确认原因仅表示输入提供带来源的确认记录，不替代对批准真伪的人工核验。
- 文字替换可定位，但语义含义仍需人工确认；文本相同不证明图形或签章相同。
