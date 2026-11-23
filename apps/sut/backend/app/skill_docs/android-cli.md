---
title: shenle-android-cli
---

# shenle-android-cli

> 分组：**执行与定位**　来源：`.claude/skills/android-cli`

## 它是什么

连安卓设备，截图后视觉定位并执行点击、输入、滑动、按键。

技能自带的触发描述：

> 通过 shenle-android-cli CLI 驱动 adb 跑 Android 设备自动化。典型触发词：「用 shenle-android-cli 跑这个流程」「AI 点这个按钮」「自动点击登录按钮」「AI 在搜索框里输入」「截一下当前屏幕」「启动 App」「滑动列表」「长按」「冷启动测试」「force-stop

## 核心功能

- `-s SERIAL` 指定设备，`--debug` 打印定位过程
- `--input-method` 可选 clipboard / adbkeyboard 解决中文输入
- 支持滑动、按键、区域内容读取

## 怎么用

```bash
shenle-android-cli devices
shenle-android-cli -s <serial> screenshot
shenle-android-cli -s <serial> click "登录按钮"
```

## 产物与判读

每步截图 + 动作结果，失败时保留现场（按用户要求本轮不做真机验证）

## 常见失败模式

需要视觉模型 key；输入法联想会让读回文本与输入不一致

## 相关

- 单跑记录：[shenle-android-cli 单跑记录](/labs/skills/android-cli)
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
