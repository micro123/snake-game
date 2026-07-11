---
description: 代码提交工作流（单阶段：生成提交信息；确认与提交由主Agent直接处理，不推送）
argument-hint: [phase:1] [type:feat] [scope:auth] [featureName:login] [bugId:001]
---

# code-submit 工作流

调用 `.claude/workflows/code-submit.workflow.js`。将用户参数解析为 args 对象后调用 Workflow 工具。

用户输入：$ARGUMENTS

## 参数解析
- 按 key:value 解析已知键：phase, type, scope, featureName, bugId, category, sub_category, previousOutputs
- phase 必填（整数，仅支持 1）；其余可选
- type 取值：feat/fix/refactor/docs/chore/perf/test/style；不提供则由 agent 从 staged diff 推断
- scope 不提供时由 agent 推断；featureName/bugId 用于读过程文档；category+sub_category 组合为 scope
- 兜底：若用户输入为空 → `{phase: 1}` 零参数调用，type/scope 均由 agent 从 staged diff 推断

## 调用
Workflow({scriptPath: ".claude/workflows/code-submit.workflow.js", args: {<解析出的对象>}})

## 主 Agent 确认循环
P1 返回 message 后，主 Agent **必须**先在对话中以代码块直接输出完整 commit message（subject + Summary + Changes），让用户完整阅读；然后再用 AskUserQuestion 询问「确认提交 / 需要修改」，**不要在 AskUserQuestion 的 preview 中重复贴 message**：
- 选「确认提交」→ 主 Agent 直接执行 Bash heredoc 提交 + `git log -1`，报告结果（不再调 Workflow phase 2）：
  ```
  git commit -F - <<'__CLAUDE_COMMIT_MSG_EOF__'
  <message>
  __CLAUDE_COMMIT_MSG_EOF__
  git log -1
  ```
- 选「需要修改」→ 用户经 Other 或文字给反馈 → 主 Agent 调 `Workflow({scriptPath: ".claude/workflows/code-submit.workflow.js", args: {phase: 1, feedback: "<反馈>"}})` 重新生成 → 再次 AskUserQuestion（循环至确认）

## 规则
- workflow 仅单阶段（P1 生成 message）；P1 结束后由主 Agent 用 AskUserQuestion 处理确认/修改循环
- 确认后主 Agent 直接执行 `git commit`（不含 `--amend`）提交已 staged 内容
- 主 Agent 仍禁 `git add`/`git push`/`git commit --amend`/`git reset --hard`/其它写 Bash（详见 CLAUDE.md）
- 提交不推送
