---
description: 问题修复工作流（3阶段：Bug分析→方案与评估→执行修复）
argument-hint: phase:1 bugId:<id> bugDescription:<desc>
---

# bug-fix 工作流

调用 `.claude/workflows/bug-fix.workflow.js`。将用户参数解析为 args 对象后调用 Workflow 工具。

用户输入：$ARGUMENTS

## 参数解析
- 按 key:value 解析已知键：phase, bugId, bugDescription, feedback
- phase 必填（整数）；bugId 必填；bugDescription 可选（P1 用）；feedback 可选（重做时用）
- bugDescription 取该 `key:` 后到下一已知键前的全文（含空格/中文）
- 兜底：若用户输入为纯文本（无 key:value）→ 整段作为 bugDescription，并向用户询问 bugId 后再调用；若为空 → 提示用法

## 调用
Workflow({scriptPath: ".claude/workflows/bug-fix.workflow.js", args: {<解析出的对象>}})

## 规则
- 每阶段结束即停，输出下一阶段命令；用户审查确认后才调下一阶段
- 主 Agent 只编排，不直接改代码（详见 CLAUDE.md）
