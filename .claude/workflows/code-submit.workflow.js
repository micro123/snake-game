export const meta = {
  name: 'code-submit.workflow',
  description: '代码提交（单阶段）：P1生成commit message。确认与commit由主Agent直接处理，不推送。',
  phases: [
    { title: '生成提交信息' },
  ]
}

// Agent call helper with retry
async function callAgent(prompt, options, retries) {
  if (retries === undefined) retries = 2;
  for (var attempt = 0; attempt <= retries; attempt++) {
    try {
      return await agent(prompt, options);
    } catch (e) {
      if (attempt < retries) {
        log('⚠️ Agent调用失败（' + e.message + '），重试 ' + (attempt + 1) + '/' + retries + '...');
        continue;
      }
      log('❌ Agent调用失败，已重试' + retries + '次: ' + e.message);
      throw e;
    }
  }
}

if (typeof args === 'string') { try { args = JSON.parse(args) } catch (e) { args = {} } }
if (!args || typeof args !== 'object') args = {}

var currentPhase = (args && args.phase) ? Number(args.phase) : null

try {
  if (currentPhase !== 1) {
    log('## ⚠️ 缺少或非法 phase 参数')
    log('阶段1(工作流): {phase: 1, type: "feat", featureName: "login", category: "auth", sub_category: "login"}')
    log('阶段1(临时): {phase: 1, type: "chore"} 或 {phase: 1, type: "refactor", scope: "workflows"}')
    log('阶段1(零参数): {phase: 1}  // type/scope 均由 agent 从 staged diff 推断')
  } else {
    await runPhase1()
  }
} catch (e) {
  log('❌ 阶段失败: ' + e.message)
}

async function runPhase1() {
  phase('生成提交信息')

  var type = args.type
  var featureName = args.featureName
  var bugId = args.bugId

  var typeInfer = !type

  var scopeStr = args.scope || (args.category ? (args.category + '/' + (args.sub_category || 'misc')) : (args.featureName || ''))
  var bugTag = (!typeInfer && type === 'fix' && bugId) ? (', bug#' + bugId) : ''
  var prefix = null
  if (!typeInfer) {
    if (scopeStr) {
      prefix = type + '(' + scopeStr + bugTag + ')'
    } else if (bugTag) {
      prefix = 'fix(bug#' + bugId + ')'
    }
  }
  // prefix 为 null → agent 推断（typeInfer 时 type+scope 均推断；否则仅 scope 推断）

  var docDir = featureName ? ('docs/feature-' + featureName) : (bugId ? ('docs/bug-' + bugId) : null)

  log('## 📝 阶段1：生成提交信息')
  log('**类型**: ' + (typeInfer ? '由你从 staged diff 推断' : type) + ' | **前缀**: ' + (prefix || '由 agent 从 staged diff 推断') + ' | **文档**: ' + (docDir || '无，仅 staged diff'))

  var fb = args.feedback ? '\n\n⚠️ 用户反馈（请按反馈修改 commit message）：' + args.feedback : ''
  var typeHint = typeInfer
    ? '按你推断的 type 选侧重：feat→功能+用途；fix→成因+修复思路；其它→变更核心+原因'
    : (type === 'feat')
      ? '侧重：功能+用途'
      : (type === 'fix')
        ? '侧重：成因+修复思路'
        : '侧重：变更核心+原因'
  var summaryGuide = '- 核心变更与动机（1-2条，每条≤25字符，合并what+why，不重复Changes；' + typeHint + '）'
  var prefixPlaceholder = prefix || (typeInfer ? '<type>(<scope>) 或 <type>（type+scope 均由你从 staged diff 推断）' : 'type(scope) 或 type')
  var prompt = '你是代码提交者。请生成 commit message：\n\n' +
    '## 参数\n- 类型: ' + (typeInfer ? '由你从 staged diff 推断' : type) + '\n- 前缀: ' + (prefix || '由你从 staged diff 推断') + '\n- 文档目录: ' + (docDir || '无') + '\n\n' +
    '## 步骤\n' +
    '1. git diff --staged 查看所有待提交变更\n' +
    '2. ' + (docDir ? ('阅读 ' + docDir + '/ 下的过程文档获取上下文') : '无显式文档目录；若 staged diff 含 docs/feature-*/ 或 docs/bug-*/ 文件，自行读这些过程文档获取上下文，否则仅依据 staged diff') + '\n' +
    '3. 按模板生成 commit message：\n\n' +
    '```\n' + prefixPlaceholder + ': 描述（≤25字，整行≤50字符）\n\n## Summary\n' + summaryGuide + '\n\n## Changes\n- 模块/路径: 简述（始终合并同类修改：同模块批量改动写一条，只有性质不同才分条；简述≤30字符，只说改了什么）\n\n## Extras（可选，无测试/文档则整节省略）\n- 测试/文档\n```\n\n## 简洁性约束（硬性）\n- subject：`type(scope): 描述`，描述≤25字，整行≤50字符\n- Summary：1-2条，每条≤25字符，合并what+why，不重复Changes\n- Changes：同模块/同性质批量改动合并为一条，简述≤30字符，只说改了什么不说原因\n- Extras：无测试/文档则整节省略（不写「无」）\n- 全文目标≤15行，硬上限≤20行' +
    (typeInfer
      ? '\n\n## 前缀推断规则\n从 staged diff 推断 type 和 scope：\n- type 按改动语义：新增功能→feat、修bug→fix、重构(不改行为)→refactor、纯文档→docs、依赖/构建/杂务→chore、性能→perf、测试→test、风格→style\n- scope 从模块/目录挑简短名\n- 用 `type(scope):` 或 `type:`（无明确 scope）' + (bugId ? '\n- 若你推断 type=fix 且提供了 bugId（' + bugId + '），在括号内加 `, bug#' + bugId + '`' : '')
      : (prefix ? '' : '\n\n## 前缀推断规则\n从 staged diff 推断一个简短 scope（模块/目录名），用 `type(scope):`；无明确 scope 则用 `type:`。不要编造 bug#。')) +
    '\n\n4. 在 `message` 字段输出完整 commit message（须满足上述简洁性约束）\n5. 在 `summary` 字段给出≤50字的摘要' + fb

  var result = await callAgent(prompt, {
    agentType: 'code-submitter', phase: '生成提交信息',
    schema: { type:'object', required:['message','summary'], properties:{ message:{type:'string'}, summary:{type:'string'} } }
  })

  if (!result) { log('## ⚠️ 未生成提交信息'); return }

  log('## ✅ 提交信息已生成\n')
  log('```\n' + result.message + '\n```\n')
  log('---\n### 📋 审查以上 commit message\n')
  log('⚠️ 请审查以上 commit message。确认与 commit 由主 Agent 用 AskUserQuestion 交互处理（脚本本身不再打印下一阶段命令）：用户「确认提交」→ 主 Agent 直接 `git commit -F -` heredoc 提交 + `git log -1` 报告结果；「需要修改」→ 用户给 feedback，主 Agent 调 `Workflow({phase:1, feedback})` 重新生成。')
}
