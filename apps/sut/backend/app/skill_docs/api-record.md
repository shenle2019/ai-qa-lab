---
title: shenle-api-record
---

# shenle-api-record

> 分组：**录制采集**　来源：`.claude/skills/api-record`

## 它是什么

本地代理抓接口请求，装 CA 后可解 HTTPS，产出接口清单。

技能自带的触发描述：

> 通过 mitmproxy 录制 HTTP/HTTPS 接口流量的技能。当用户想要把浏览器、手机 H5、APP 或桌面应用的接口流量抓到本地批次目录（rawNN.json），供后续 AI 分析 / 生成接口文档 / 生成测试用例时，使用本技能。典型触发词：「帮我录一下接口」「抓一下 API」「录制 APP 接口」「手机抓

## 核心功能

- `record` 起代理并记录经过的请求
- `install-ca` 安装证书以解密 HTTPS
- `check` / `stop` 查看状态与收尾

## 怎么用

```bash
shenle-api-record record --port 8899
shenle-api-record install-ca
shenle-api-record check
```

## 产物与判读

请求清单（方法、路径、头、体）与回放所需上下文

## 常见失败模式

没装 CA 时只能看到 CONNECT 隧道，拿不到明文

## 相关

- 单跑记录：[shenle-api-record 单跑记录](/labs/skills/api-record)
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
