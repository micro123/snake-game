#!/usr/bin/env node
// PreToolUse hook: 放行只读 node，阻断含写效果 API 的 node 内联代码（node -e）
// 主 Agent 仅允许只读 node（如 JSON 解析）；文件写入请委托 developer 子 Agent
const fs = require('fs');
let raw = '';
process.stdin.on('data', d => raw += d);
process.stdin.on('end', () => {
  let j; try { j = JSON.parse(raw); } catch (e) { process.exit(0); }
  if (j.tool_name !== 'Bash') process.exit(0);
  const cmd = (j.tool_input && j.tool_input.command) || '';

  // 只管 node -e 内联代码（"生成代码来执行"的场景）；node <file.js> 不扫（预存脚本非运行时生成）
  let code = '';
  const qm = cmd.match(/(^|\s)node\s+(?:-[^\s]+\s+)*-e\s+(['"])([\s\S]*?)\2/);
  if (qm) code = qm[3];
  else {
    const um = cmd.match(/(^|\s)node\s+(?:-[^\s]+\s+)*-e\s+([^\s]+)/);
    if (um) code = um[2];
  }
  if (!code) process.exit(0);  // 非 node -e（git 等），放行

  // 写效果 API 模式
  const WRITE = /\b(writeFile|writeFileSync|appendFile|appendFileSync|unlinkSync|rmdir|rmdirSync|mkdir|mkdirSync|rename|renameSync|copyFile|copyFileSync|createWriteStream|rmSync)\s*\(|fs\.(write|append|unlink|rm|rmdir|mkdir|rename|copyFile)\s*\(|child_process|\b(execSync|spawnSync|execFile)\s*\(|fs\.open(Sync)?\s*\([^)]*['"][wa]/;
  const hit = WRITE.exec(code);
  if (hit) {
    console.error('❌ 拒绝执行含写效果 API 的 node 内联代码（命中: ' + hit[0] + '）。主 Agent 仅允许只读 node；文件写入请委托 developer 子 Agent。');
    process.exit(2);
  }
  process.exit(0);
});
