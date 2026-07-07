---
description: 新功能开发工作流（5阶段：需求分析→概要设计→详细设计→评估与排期→实施）
argument-hint: phase:1 featureName:<name> featureDescription:<desc>
---

# feature-dev 工作流

调用 `.claude/workflows/feature-dev.workflow.js`。将用户参数解析为 args 对象后调用 Workflow 工具。

用户输入：$ARGUMENTS

## 参数解析
- 按 key:value 解析已知键：phase, featureName, featureDescription, feedback
- phase 必填（整数）；featureName 必填；featureDescription 可选（P1 用）；feedback 可选（重做时用）
- featureDescription 取该 `key:` 后到下一已知键前的全文（含空格/中文）
- 兜底：若用户输入为纯文本（无 key:value）→ 整段作为 featureDescription，并向用户询问 featureName 后再调用；若为空 → 提示用法

## 调用
Workflow({scriptPath: ".claude/workflows/feature-dev.workflow.js", args: {<解析出的对象>}})

## 规则
- 每阶段结束即停，输出下一阶段命令；用户审查确认后才调下一阶段
- 主 Agent 只编排，不直接改代码（详见 CLAUDE.md）
