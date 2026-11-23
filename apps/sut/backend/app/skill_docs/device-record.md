---
title: shenle-device-record
---

# shenle-device-record

> 分组：**录制采集**　来源：`.claude/skills/device-record`

## 它是什么

连安卓设备，抓当前屏幕与界面层级，落盘成结构化快照。

## 核心功能

- `record` 单次抓取，`serve` 起本地服务供多次调用
- 截图 + `uiautomator` 层级一起存，定位信息不丢
- 支持指定设备序列号，多机时可分流

## 怎么用

```bash
shenle-device-record record
shenle-device-record serve
```

## 产物与判读

截图 PNG + 层级 XML + 元信息 JSON（按用户要求本轮不做真机验证）

## 常见失败模式

设备未授权 / 屏幕锁定时层级抓不全

## 相关

- 单跑记录：[shenle-device-record 单跑记录](/labs/skills/device-record)
- 返回：[Skills 手册](/kb/skills/)
