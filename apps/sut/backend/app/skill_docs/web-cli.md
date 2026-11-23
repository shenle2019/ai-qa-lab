---
title: shenle-web-cli
---

# shenle-web-cli

> 分组：**执行与定位**　来源：`.claude/skills/web-cli`

## 它是什么

给网页截图，让视觉模型找元素，直接点击、输入、读回页面内容。

技能自带的触发描述：

> 通过自然语言驱动 Chromium 跑 WEB 测试用例。典型触发词：「用 shenle-web-cli 跑这个用例」「AI 执行登录流程」「自动化点这个按钮」「在搜索框里输入」「自动截图取证」「截一下当前页面」「点击「提交」按钮」「滚动到列表底部」「断言当前 URL」「跑一轮回归」「回放这个测试」。本技能封装 `sh

## 核心功能

- 子命令：`start / navigate / screenshot / click / input / get / scroll / url / title / close`
- `start --headless --port N` 起后台浏览器并把端口写进 state.json，后续命令自动复用
- `click "描述"` / `input "描述" "文本"` 收自然语言，不写选择器

## 怎么用

```bash
shenle-web-cli start --headless --port 9223
shenle-web-cli navigate http://127.0.0.1:8733/index.html
shenle-web-cli screenshot out/shot.png
shenle-web-cli click "页面上的登录按钮"
shenle-web-cli get "页面底部那行状态文字"
shenle-web-cli close
```

## 产物与判读

命令回显（点击返回坐标、截图返回尺寸、`get` 按布局/图标/文字/介绍四节输出）+ 截图文件

## 常见失败模式

需要视觉模型 key；9222 被占用时换 `--port`；未 `start` 就调用其它命令会报「未连接到当前设备」

## 相关

- 单跑记录：[shenle-web-cli 单跑记录](/labs/skills/web-cli)
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
