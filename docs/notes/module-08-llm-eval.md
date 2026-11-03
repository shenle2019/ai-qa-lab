# 模块 08 笔记：LLM 评测别只看“像不像”

## 问题

LLM 输出没有唯一答案。只靠肉眼看“像不像”，无法回归，也无法比较两个版本。

评测要回答三件事：

1. 回答切题吗？
2. 回答忠于上下文吗？
3. 新版本比旧版本好吗？

## 方案

包放在 `libs/minieval`，不依赖 DeepEval。

| 能力 | 实现 |
|---|---|
| 数据集 | JSONL，一条一个 case |
| 裁判 | MockJudge（词法） / DeepSeekJudge（可选） |
| 指标 | 相关性、忠实度、上下文精确率/召回率、正确性 |
| 阈值 | overall >= 0.7 |
| 对比 | baseline vs candidate，输出 delta |
| 报告 | JSON + 离线 HTML |

## 结果

- 5 个框架元测试通过
- 5 条 SUT 问答数据集
- baseline 0.52 → candidate 0.72，delta +0.20
- 整体 PASS，2 条单测低于阈值
- 报告：`docs/portfolio/module-08-llm-report.html`

## 踩坑

1. 中文没有 jieba，用字符 + 英文单词做近似 token。
2. 上下文指标容易虚高。
3. 词法重叠高不等于语义正确。
4. 整体 PASS 不代表每条都好。
5. DeepSeek 裁判按条计费，大数据集要注意预算。

## 一句话

LLM 评测的价值不是给一个“感觉分”，而是把数据集、指标、阈值、对比固定下来，让每次改 prompt 都能回归。
