# 探索式测试产物（2026-11-05）

被测系统：https://ai-qa-lab-production.up.railway.app/ui/#/
方法论来源：公众号文章《给 Agent 做探索式测试》七步法。

## 目录约定
- `screenshots/`：每一步的截图，文件名 `NNN-slug.png`
- `log.jsonl`：探索日志，一行一步，字段：ts / step / action / url / title / observed / judgment / severity / evidence
- `map.md`：第一阶段画出的系统地图
- `findings.md`：最终发现清单（现象 / 复现步骤 / 判断 / 严重程度）
- 脚本放在 `scripts/explore_2026_11_05.py`（一次性探索脚本，不进测试套件）

## 硬约束
只读/可逆。不创建、不修改、不删除任何业务数据；写操作请求一律不提交，只记录。
