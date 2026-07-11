---
description: 需求文档优化循环：交替运行feature-dev P1与doc-review，自动循环至收敛（无P0/P1建议）或达上限
argument-hint: featureName:string featureDescription:"..." [maxRounds:3]
---

# doc-review-loop 命令

用户输入：$ARGUMENTS

## 参数解析

- `featureName`（必填）：功能名称
- `featureDescription`（必填）：功能描述
- `maxRounds`（可选，默认 3）：最大循环轮数

## 首轮快速路径

进入循环前，先检查是否可以跳过首轮 P1：

```
若 需求分析.md 和 文档审查.md 都存在：
  用 ls -lt 比较时间戳
  若 文档审查.md 比 需求分析.md（或 概要设计.md）更旧：
    → 首轮跳过 feature-dev P1，直接从 doc-review 开始
    → 原因：P1 产出已更新但尚未审查，无需重跑 P1
  否则：
    → 正常执行首轮（P1 → doc-review）
否则：
  → 正常执行首轮（P1 → doc-review）
```

> 实现方式：主 Agent 用 `ls -lt docs/feature-{name}/需求分析.md docs/feature-{name}/文档审查.md` 比较输出顺序（排前面的更新）。

## 循环编排

主 Agent 执行以下循环（最多 `maxRounds` 轮）。维护一个趋势数组 `trends = []`，每轮记录 `{round, p0Count, p1Count, p2Count}`。

```
第1轮：
  若未跳过 P1：
    Workflow({scriptPath: ".claude/workflows/feature-dev.workflow.js", args: {phase:1, featureName, featureDescription}})
    等待完成
  Workflow({scriptPath: ".claude/workflows/doc-review.workflow.js", args: {phase:1, featureName}})
  等待完成，读返回值：{p0Count, p1Count, p0Items, p1Items}
  记录 trends.push({round:1, p0Count, p1Count, p2Count})

若 p0Count===0 && p1Count===0 → 停止（收敛）
若已达 maxRounds → 停止（达上限）

否则（有 P0/P1 建议，未达上限）→ 构造 feedback，下一轮：

  feedback = "文档审查发现以下问题，请根据建议逐条优化需求分析与概要设计：\n"
  feedback += "## P0（严重，必须修改）\n"
  for each item in p0Items: feedback += "- " + item.content + "\n"
  feedback += "## P1（重要，建议修改）\n"
  for each item in p1Items: feedback += "- " + item.content + "\n"

  Workflow({scriptPath: ".claude/workflows/feature-dev.workflow.js", args: {phase:1, featureName, featureDescription, feedback}})
  等待完成
  Workflow({scriptPath: ".claude/workflows/doc-review.workflow.js", args: {phase:1, featureName}})
  等待完成，读 p0Count/p1Count/p0Items/p1Items
  记录 trends.push({round:<当前轮数>, p0Count, p1Count, p2Count})

  停滞检测：若本轮 p0Count === 上轮 p0Count 且 本轮 p1Count === 上轮 p1Count
    → 停止（停滞：连续两轮 P0/P1 数量无变化，建议手动介入）
```

**关键规则**：
- 首轮无 feedback；后续每轮带 feedback 重跑 P1
- 每轮从 doc-review 返回值直接取 `p0Items`/`p1Items` 构造 feedback，**不需要 Read 文档审查.md**
- P0 + P1 = 0 时停止（收敛）
- 连续两轮 P0+P1 数量完全相同 → 提前停止（停滞），提示用户手动介入
- 达 maxRounds 时停止（达上限）
- 每轮保留最新产出的文档（需求分析.md / 概要设计.md / 文档审查.md）

## 最终报告

循环结束后主 Agent 输出：
- 收敛趋势表（每轮 P0/P1/P2 数量）
- 总轮数
- 最终 P0/P1/P2 数量
- 停止原因：收敛 / 停滞 / 达上限
- 最终文档路径
