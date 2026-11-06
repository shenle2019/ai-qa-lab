# Citrus Lab · 柠檬黄绿改版（2026-11-06）

按 `UI审查与改版规格.md` + `redesign-reference.html` 落地的一版。

## 做了什么

### P0 · 令牌与骨架

- 新增 `apps/sut/frontend/src/citrus.css`（替代已删除的 `theme.css`），`main.js` 只引这一份样式。
- 三套底层重排：`--bg #F7F9F0` / 侧栏 `--bg-2 #EFF4E3` / 卡片 `--panel #FFF`；文字 `--ink #1C2607` + `--muted #6B7545`；品牌 `--lime #A3E635` + `--lime-deep #4D7C0F` + `--yellow #FDE047`。
- 三条硬规则写进注释并遵守：lime 不做正文小字、大面积色块只有三处、yellow 只做渐变与下划线。
- `body::before` 三层氛围光（黄 + 黄绿 + 右下淡绿），固定不随滚动。

### P1 · 组件

| 部位 | 改动 |
| --- | --- |
| 侧栏 | 236px，线性图标（`components/NavIcon.vue`，24×24 stroke2），分组标签 10.5px 大写，选中态 lime 实底 + 深墨字 + 阴影 |
| 顶栏 | 56px sticky 毛玻璃，面包屑 + 全局搜索（⌘K / Ctrl+K 聚焦、Enter 跳转、Esc 清空）+ ghost 按钮 + 圆形头像 |
| hero | 从卡片改成页面头：eyebrow 胶囊 + 30px/800 标题 + 12.5px 说明 + 右侧指标 |
| 统计卡 | 白底 + 1px 线 + 18px 圆角 + 右上光斑（`::before`）+ 右下 data-URI sparkline（`::after`），数字 34px/800 tabular-nums |
| 表格 | 表头 11px 大写 + `--bg` 底；行 13px；hover `#FBFDEF`；ID 列 mono 徽标；`.row-actions .btn` 统一 mini 尺寸 |
| 按钮 | `.btn` = lime→yellow 渐变 + 深墨字 + shadow-2；`.btn.ghost` 白底描边；表格内 mini |
| 徽标 | `--*-soft` 底 + 深色字；补 `module-done/planned/failed` → 绿/灰/红 的映射（旧页面在用这套类名） |
| 输入 | `--bg` 底 + 10px 圆角；focus 绿边 + 3px lime 光环 |
| 提示条 / 空态 / skeleton | 语义色 + 左侧 3px 竖条；空态实线框；skeleton 扫光 |

### P2 · 页面结构

- **项目管理**：3 列卡片网格 + 卡片/表格切换 + 420px 抽屉新建（左侧 4px lime 条）；空态卡引导。
- **知识库**：刷新改 ghost、新建改主按钮；左栏选中项白底 + 3px lime 竖条。
- 其余页面沿用原结构，只吃新令牌与组件样式。

## 验证

| 项 | 结果 |
| --- | --- |
| 构建 | `✓ built in 8.1s` |
| 后端测试 | `142 passed` |
| 9 个页面截图 | `docs/ui-citrus/citrus-*.png` |
| pageerror | 0 |

## 还没做（下一步）

1. **概览页**：通过率环形、Skills 按 category 分组 chips、最近执行时间线。
2. **需求管理**：标题两行 + 优先级左侧 3px 色条。
3. **功能测试**：inline stat pill、36px slim banner、skill chips。
4. **空态**：还没全部换成「实线框 + 40px 图标 + 主按钮」。
5. **加载态**：只有三个列表有 skeleton，其余页面仍会闪空态。
6. **表格操作列**：还没有「只留一个实心主操作 + ⋯ 收纳次级」。
