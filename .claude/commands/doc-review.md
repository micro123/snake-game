---
description: 文档审查工作流（单阶段：并行3视角审查 → 合并生成修改意见）
argument-hint: [phase:1] [featureName:login]
---

# doc-review 工作流

调用 `.claude/workflows/doc-review.workflow.js`。将用户参数解析为 args 对象后调用 Workflow 工具。

用户输入：$ARGUMENTS

## 参数解析
- 按 key:value 解析已知键：phase, featureName
- phase 必填（整数，仅支持 1）；featureName 必填
- 兜底：若用户输入为空 → 提示缺少参数

## 调用
Workflow({scriptPath: ".claude/workflows/doc-review.workflow.js", args: {<解析出的对象>}})

## 规则
- 独立工具，在 feature-dev P1 完成后手动调用
- 并行启动 3 个审查 agent（梦想家/实业家/批评家），各自审阅需求分析.md + 概要设计.md
- 整理者合并去重，按 P0/P1/P2 排列建议
- doc writer 产出 `docs/feature-{name}/文档审查.md`
- 主 Agent 只输出摘要 + P0/P1 条数
