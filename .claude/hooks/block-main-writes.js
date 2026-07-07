#!/usr/bin/env node
// PreToolUse hook (M2.2 Part a): 主 Agent 禁止写非 .claude 配置文件；子 Agent 放行
// 抓包结论：主 agent 的 agent_id 为 null，子 agent 为非空字符串
const CFG = /(^|\/)\.claude\//;  // 项目 .claude/ 与用户 ~/.claude/ 都覆盖
let raw = '';
process.stdin.on('data', d => raw += d);
process.stdin.on('end', () => {
  let j; try { j = JSON.parse(raw); } catch (e) { process.exit(0); }
  const tool = j.tool_name;
  if (tool !== 'Write' && tool !== 'Edit' && tool !== 'NotebookEdit') process.exit(0);
  const agentId = j.agent_id;
  const isMain = !agentId;  // 主 agent: agent_id 为 null/undefined/空
  if (!isMain) process.exit(0);  // 子 agent: 放行（其 tools: frontmatter 已硬限制）
  // 主 agent：仅允许写 .claude/ 配置路径（plan/memory/settings/hooks/agents/workflows）
  const fp = ((j.tool_input && j.tool_input.file_path) || '').replace(/\\/g, '/');
  if (CFG.test(fp)) process.exit(0);
  console.error('❌ 主 Agent 禁止写非配置文件 ' + fp + '（仅允许 .claude/ 配置）。请委托子 Agent 执行。');
  process.exit(2);
});
