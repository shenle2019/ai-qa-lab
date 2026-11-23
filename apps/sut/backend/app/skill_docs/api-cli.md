---
title: shenle-api-cli
---

# shenle-api-cli

> 分组：**执行与定位**　来源：`.claude/skills/api-cli`

## 它是什么

命令行发接口请求、抽字段、断言，替代 curl 给 AI 用。

## 核心功能

- `send` 发请求并把 request/response 落盘
- `extract` 用 JSONPath 取变量
- `call` 一步 send + extract，`assert` 自然语言断言（需 AI）

## 怎么用

```bash
echo '{"method":"GET","url":"http://127.0.0.1:8732/logo.svg"}' | shenle-api-cli send
shenle-api-cli call req.json --extract data.id
```

## 产物与判读

`%TEMP%/shenle-api-results/*.json`，含 request / response / meta

## 常见失败模式

请求体字段名写错时返回 400，先看 result 文件里的原始报文

## 相关

- 单跑记录：[shenle-api-cli 单跑记录](/labs/skills/api-cli)
- 返回：[Skills 手册](/kb/skills/)
