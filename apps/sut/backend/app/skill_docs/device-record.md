---
title: shenle-device-record
---

# shenle-device-record

> 分组：**录制采集**　来源：`.claude/skills/shenle-device-record`

## 它是什么

连安卓设备，抓当前屏幕与界面层级，落盘成结构化快照，供后续定位与用例生成。

## 核心功能

- `record` 单次抓取，`serve` 起本地服务供连续采集
- 截图 PNG + `uiautomator` 层级 XML 一起存，定位信息不丢
- 支持 `-s <serial>` 指定设备，多机时分流

## 怎么用

```bash
adb devices                       # 确认状态是 device，不是 unauthorized
shenle-device-record record       # 抓一屏：截图 + 层级 + 元信息
shenle-device-record serve        # 连续采集，本地起服务
shenle-device-record record -s FA7B11A03073
```

## 产物与判读

时间戳批次目录下 `img/` 截图与 `json/` 层级各一份。判读看三点：设备是 `device`、批次目录是新的、JSON 里 `elements` 与截图对得上。

## 常见失败模式

- `device unauthorized`：手机上没点允许调试，不点永远不会变。
- `more than one device/emulator`：多设备没带 `-s`。
- 层级只有系统 UI：锁屏或系统弹窗盖住了，先解锁关弹窗再采。

## 相关

- 单跑记录：[shenle-device-record 单跑记录](/labs/skills/device-record)
- 全文与下载：[Skills 库](/skills/shenle-device-record)
- 返回：[Skills 手册](/kb/skills/)

## 评分（skill-judge）

总分 **111 / 120**（≥108 为 A 级），按 skill-judge 八维逐项打分：

| 维度 | 得分 | 满分 |
| --- | --- | --- |
| D1 知识增量 | 17 | 20 |
| D2 心智与流程 | 15 | 15 |
| D3 反模式 | 13 | 15 |
| D4 规格 | 15 | 15 |
| D5 渐进披露 | 14 | 15 |
| D6 自由度 | 12 | 15 |
| D7 模式识别 | 10 | 10 |
| D8 实用可用性 | 15 | 15 |

判定：✅ 达标，规范条数见 `docs/skill-scores.json`。
