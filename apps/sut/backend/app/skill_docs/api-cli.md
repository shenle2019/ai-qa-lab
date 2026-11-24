---
title: shenle-api-cli
---

# shenle-api-cli

> 分组：**执行与定位**　来源：`.claude/skills/shenle-api-cli`

## 它是什么

命令行发接口请求、抽字段、断言，替代 curl 给 AI 用。装在仓库里，用 `.venv\Scripts\shenle-api-cli.exe` 调用。

## 核心功能

- `send` 发请求并把 request / response 落盘到 `%TEMP%/shenle-api-results/`
- `call` 一步 send + extract，JSONPath 直接取字段
- `extract` 从已有 result 文件里取字段，`assert` 用自然语言断言（需 AI 配置）

## 怎么用

```bash
# 发一次请求，落盘结果
shenle-api-cli send req.json

# 发请求并直接取字段（推荐）
shenle-api-cli call req.json --field "$.full_name"

# 4xx 也要继续取值
shenle-api-cli call req.json --field "$.msg" --no-fail-on-status
```

`req.json` 形如 `{"method": "GET", "url": "https://...", "headers": [{"name": "Accept", "value": "application/json"}]}`。

## 产物与判读

`%TEMP%/shenle-api-results/<时间戳>-<hash>.json`，含 `request` / `response`（status、headers、body_text、body_json、elapsed_ms）/ `meta`。
`[OK] send: 200 GET <url> elapsed=676ms result_file=...` 说明请求真的发出去了；断言要看状态码与字段，光有 `[OK]` 不算通过。

## 常见失败模式

- `Unexpected UTF-8 BOM`：`req.json` 被 PowerShell 写成带 BOM 的 UTF-8，改用 `Set-Content -Encoding utf8NoBOM` 或 Python 写文件。
- `JSONPath 未匹配`：字段路径写错或 body 不是 JSON，改 `--field "返回的 X"` 走自然语言。
- `[FAIL] send: 网络请求失败`：先确认 URL 可达，再调 `--timeout`。

## 相关

- 单跑记录：[shenle-api-cli 单跑记录](/labs/skills/api-cli)
- 全文与下载：[Skills 库](/skills/shenle-api-cli)
- 返回：[Skills 手册](/kb/skills/)

## 评分（skill-judge）

总分 **109 / 120**（≥108 为 A 级），按 skill-judge 八维逐项打分：

| 维度 | 得分 | 满分 |
| --- | --- | --- |
| D1 知识增量 | 17 | 20 |
| D2 心智与流程 | 15 | 15 |
| D3 反模式 | 13 | 15 |
| D4 规格 | 15 | 15 |
| D5 渐进披露 | 12 | 15 |
| D6 自由度 | 12 | 15 |
| D7 模式识别 | 10 | 10 |
| D8 实用可用性 | 15 | 15 |

判定：✅ 达标，规范条数见 `docs/skill-scores.json`。
