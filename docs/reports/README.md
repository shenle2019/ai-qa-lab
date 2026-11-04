# 报告归档规则

## 为什么分层

代码每天都会更新，但项目报告不应该每天生成一个新版本，否则会变成噪声。采用两层记录：

| 层 | 位置 | 频率 | 内容 |
|---|---|---|---|
| 日报 | `docs/progress/YYYY-MM-DD.md` | 每天 | 当天做了什么、验证结果、阻塞、下一步 |
| 里程碑报告 | `docs/reports/YYYY-MM-DD-vX.Y.Z/` | 每个模块/重大版本 | 不可变快照、指标、原理、成果、截图 |

## 版本规则

- `v0.1.0`：项目骨架 + SUT 最小版
- `v0.2.0`：SUT 控制台 + 接口套件 + API 工作台 v0.1 + 项目报告
- 每完成一个模块：minor +1（`v0.3.0`、`v0.4.0`…）
- 仅修复/小改动：patch +1
- 架构级变化：major +1

## 归档目录

```
docs/reports/2026-11-03-v1.0.0/
  index.html      静态报告快照（截图路径已改写为本地）
  report.md       Markdown 版报告
  screenshots/    快照自带截图
  metrics.json    版本、日期、commit、测试数、页面数
  README.md       快照说明
```

## 规则

1. 旧快照原则上不修改；措辞或安全类更正可直接修订，并在快照内新增 `corrections.md` 记录。
2. 根 `docs/index.html` 永远是最新报告；归档索引在 `docs/reports/index.html`。
3. 每次归档同时打 Git tag（与版本同名），标签即代码归档点。
4. `.gitignore` 只忽略根目录 `/reports/`，不要忽略 `docs/reports/`；否则快照不会进 Git，Pages 会 404。
4. 归档命令：

```bash
.venv/Scripts/python.exe scripts/archive_report.py \
  --version v0.2.0 --date 2026-11-02 \
  --tests 33 --pages 6 --modules 8 --replications 1
```

5. 归档后推送标签：

```bash
git push ssh-origin v0.2.0
```

## 公开地址

- 最新报告：https://shenle2019.github.io/ai-qa-lab/
- 归档索引：https://shenle2019.github.io/ai-qa-lab/reports/
- 快照示例：https://shenle2019.github.io/ai-qa-lab/reports/2026-11-03-v1.0.0/
