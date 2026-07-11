export const meta = {
  name: 'bug-fix.workflow',
  description: '问题修复（3阶段）。P1 Bug分析(P1+P2合并) → P2 方案与评估(P3+P4合并) → P3 执行修复',
  phases: [
    { title: 'Bug分析' },
    { title: '方案与评估' },
    { title: '执行修复' },
  ]
}

// ─── callAgent retry wrapper ───────────────────────────────────────────────
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
      log('💡 可重新调用本阶段并传入 feedback 重试。');
      throw e;
    }
  }
}

// ─── State persistence (M3.1) ───────────────────────────────
function stateFile(prefix, id, n) { return 'docs/' + prefix + '-' + id + '/.phase' + n + '.json' }

async function writeState(prefix, id, n, obj) {
  var path = stateFile(prefix, id, n)
  await callAgent('将以下 JSON **原样**写入文件 `' + path + '`（一个字符不改，不要 markdown 代码块，直接写 JSON 文本）：\n\n' + JSON.stringify(obj, null, 2),
    {agentType: 'developer', label: 'state-write: phase' + n, phase: '状态'})
}

async function loadState(prefix, id, needed) {
  if (args.previousOutputs) return args.previousOutputs   // 向后兼容
  if (!needed || !needed.length) return {}
  var props = {}; needed.forEach(function(k){ props[k] = {type:'string'} })
  var r = await callAgent('从 `docs/' + prefix + '-' + id + '/` 读取以下文件，在对应字段返回**原始内容**（不解析、不改、不加代码块）：'
    + needed.map(function(k){ return k + ' ← .phase' + k.replace('phase','') + '.json' }).join(', ')
    + '。文件不存在则该字段留空字符串。',
    {agentType: 'developer', label: 'state-load', phase: '状态', schema: {type:'object', properties: props}})
  if (!r) return {}
  var prev = {}
  needed.forEach(function(k){ if (r[k]) { try { prev[k] = JSON.parse(r[k]) } catch(e){ log('⚠️ .phase'+k.replace('phase','')+'.json 解析失败: '+e.message) } } })
  return prev
}

// ─── Load previous phase results for reference when re-running with feedback (non-blocking) ──
async function loadPrevPhaseRef(bugId, phaseNum) {
  try {
    var filePath = 'docs/bug-' + bugId + '/.phase' + phaseNum + '.json'
    var r = await callAgent(
      '读取 `' + filePath + '`，在 `data` 字段返回文件的**原始内容**（一个字不改、不加代码块）。文件不存在则 `data` 留空字符串。',
      {agentType: 'developer', label: 'load-prev-phase' + phaseNum, phase: '状态',
       schema: {type:'object', properties: {data:{type:'string'}}}}
    )
    if (r && r.data) {
      try { return JSON.parse(r.data) } catch(e) { log('⚠️ .phase' + phaseNum + '.json 解析失败: ' + e.message) }
    }
  } catch(e) { /* non-blocking */ }
  return null
}

// ─── Schema helpers ────────────────────────────────────────────────────────
const DOC_META = { documentPath: { type: 'string' }, summary: { type: 'string' } }
function addDoc(s) { return { ...s, properties: { ...s.properties, ...DOC_META } } }

const S1 = addDoc({ type:'object', required:['title','severity','stepsToReproduce','expectedBehavior','actualBehavior'], properties:{ title:{type:'string'}, severity:{type:'string',enum:['Critical','Major','Minor','Trivial']}, stepsToReproduce:{type:'array',items:{type:'string'}}, expectedBehavior:{type:'string'}, actualBehavior:{type:'string'}, environment:{type:'object',properties:{os:{type:'string'},browser:{type:'string'},appVersion:{type:'string'}}}, frequency:{type:'string',enum:['Always','Sometimes','Rarely','Once']}, affectedComponent:{type:'string'}, logs:{type:'array',items:{type:'string'}}, reportedBy:{type:'string'}, reportedAt:{type:'string'} }})

const S2 = addDoc({ type:'object', required:['rootCause','causationChain','confidence'], properties:{ rootCause:{type:'object',required:['description'],properties:{file:{type:'string'},function:{type:'string'},line:{type:'string'},description:{type:'string'}}}, causationChain:{type:'array',items:{type:'object',properties:{step:{type:'integer'},description:{type:'string'},codeLocation:{type:'string'}}}}, triggerConditions:{type:'array',items:{type:'string'}}, affectedCodePaths:{type:'array',items:{type:'string'}}, relatedCode:{type:'array',items:{type:'object',properties:{file:{type:'string'},snippet:{type:'string'},relevance:{type:'string'}}}}, missingTests:{type:'array',items:{type:'string'}}, confidence:{type:'string',enum:['high','medium','low']}, additionalNotes:{type:'string'} }})

const S3 = addDoc({ type:'object', required:['primarySolution','alternatives','estimatedEffort'], properties:{ primarySolution:{type:'object',required:['description','fileChanges','rationale'],properties:{description:{type:'string'},fileChanges:{type:'array',items:{type:'object',properties:{file:{type:'string'},change:{type:'string',enum:['modify','create','delete']},description:{type:'string'}}}},references:{type:'array',items:{type:'string'}},rationale:{type:'string'}}}, alternatives:{type:'array',items:{type:'object',required:['description'],properties:{description:{type:'string'},pros:{type:'array',items:{type:'string'}},cons:{type:'array',items:{type:'string'}},whyNotChosen:{type:'string'}}}}, sideEffects:{type:'array',items:{type:'object',properties:{area:{type:'string'},risk:{type:'string',enum:['low','medium','high']},description:{type:'string'}}}}, estimatedEffort:{type:'object',required:['hours'],properties:{hours:{type:'number'},breakdown:{type:'string'}}}, testPlan:{type:'object',properties:{unitTests:{type:'array',items:{type:'string'}},integrationTests:{type:'array',items:{type:'string'}},manualVerification:{type:'array',items:{type:'string'}},regressionChecks:{type:'array',items:{type:'string'}}}} }})

const S4 = addDoc({ type:'object', required:['feasibility','regressionRisk','recommendation'], properties:{ feasibility:{type:'string',enum:['yes','no','conditional']}, feasibilityRationale:{type:'string'}, regressionRisk:{type:'string',enum:['high','medium','low']}, regressionRiskDetail:{type:'string'}, impactedAreas:{type:'array',items:{type:'object',properties:{area:{type:'string'},impactLevel:{type:'string',enum:['high','medium','low']},description:{type:'string'},mitigation:{type:'string'}}}}, testCoverageGaps:{type:'array',items:{type:'string'}}, deploymentConcerns:{type:'array',items:{type:'string'}}, recommendation:{type:'string',enum:['approved','needs-revision','rejected']}, approvalConditions:{type:'array',items:{type:'string'}}, additionalReviewers:{type:'array',items:{type:'string'}} }})

// ─── Phase definitions ────────────────────────────────────────────────────
var PHASES = [
  { num:1, title:'Bug分析', type:'merged', agent1:'bug-triage-engineer', schema1:S1, agent2:'code-analyst', schema2:S2, doc:'Bug分析.md', needed:[],
    prompt1: function(prev, bugId) { return '将以下反馈转化为结构化Bug报告：\n\n原始反馈：' + (args.bugDescription || '请根据上下文推断Bug情况') + '\n\n输出：Bug标题、严重程度(Critical/Major/Minor/Trivial)、复现步骤(编号列表)、期望行为、实际行为、运行环境(OS/浏览器/应用版本)、发生频率(Always/Sometimes/Rarely/Once)、受影响模块、相关日志。' },
    prompt2: function(prev, bugId, r1) { return '分析Bug根因：\n\n## Bug报告\n'+JSON.stringify(r1,null,2)+'\n\n请使用 Grep/Read 探索代码库，追踪从触发点到表现的因果链。输出：根因定位(文件/函数/行号/描述)、因果链(每步标注代码位置)、触发条件、受影响代码路径、相关代码片段、缺失测试、置信度(high/medium/low)、补充说明。' }
  },
  { num:2, title:'方案与评估', type:'merged', agent1:'solution-designer', schema1:S3, agent2:'tech-lead', schema2:S4, doc:'方案与评估.md', needed:['phase1'],
    prompt1: function(prev, bugId) { return '基于Bug分析提出修复方案（P1已有根因定位和受影响文件）：\n\n## Bug分析\n'+JSON.stringify(prev.phase1,null,2)+'\n\n输出：主方案(描述/文件变更列表/理由)、备选方案(至少1个/优缺点/未选用原因)、副作用(影响范围/风险等级)、预估工时(小时/分解)、测试计划(单元/集成/手动验证/回归)。主方案的 references 列出只读依赖文件（类型定义/工具类/基类等，修复时需了解但不修改）。' },
    prompt2: function(prev, bugId, r1) { return '评估修复方案可行性（不主动读源码——Bug分析已有根因定位，方案已有文件变更。基于这些直接评估，仅在发现明显疑点时读源码验证）：\n\n## Bug分析\n'+JSON.stringify(prev.phase1,null,2)+'\n\n## 解决方案\n'+JSON.stringify(r1,null,2)+'\n\n输出：可行性(yes/no/conditional)及理由、回归风险(high/medium/low)及说明、受影响区域(影响程度/缓解措施)、测试覆盖缺口、部署注意事项、建议(approved/needs-revision/rejected)、批准条件、额外审查人建议。' },
    checkGate: function(r2) { return r2.recommendation === 'rejected' || r2.feasibility === 'no' }
  },
  { num:3, title:'执行修复', type:'implement', agentType:'developer', doc:'执行修复.md', needed:['phase1','phase2'] },
]

// ─── Helper functions ─────────────────────────────────────────────────────
function docPath(bugId, doc) { return 'docs/bug-' + bugId + '/' + doc }
function docInst(dp, mode) {
  if (mode === 'step1') return '\n\n---\n## 文档输出\n\n完成分析后使用 Write 将结果写入 `' + dp + '`（子步骤1部分），在 `documentPath` 字段填 "' + dp + '"，在 `summary` 字段给出100字以内摘要。'
  return '\n\n---\n## 文档输出\n\n完成分析后：\n1. 使用 Write 工具将完整的过程文档写入 `' + dp + '`\n   格式：Markdown，含标题(# 阶段名)、元信息(Bug/阶段/角色/日期)、所有分析内容分节呈现\n2. 在返回的 `documentPath` 字段填 "' + dp + '"\n3. 在 `summary` 字段给出100字以内的摘要'
}
function nextCmd(n, bugId) {
  return 'Workflow({scriptPath: ".claude/workflows/bug-fix.workflow.js", args: {phase: ' + n + ', bugId: "' + bugId + '"}})'
}
function outputNextStep(info) {
  var n = info.num
  if (n < 3) {
    log('⚠️ 请先阅读 `' + docPath(args.bugId, info.doc) + '` 确认后调用阶段' + (n + 1) + '：\n```\n' + nextCmd(n + 1, args.bugId) + '\n```')
  }
}

// ─── Dispatch ──────────────────────────────────────────────────────────────
// args 字符串容错（Workflow 调用时 args 可能被当字符串注入）
if (typeof args === 'string') { try { args = JSON.parse(args) } catch (e) { args = {} } }
if (!args || typeof args !== 'object') args = {}

var phaseNum = (args && args.phase) ? Number(args.phase) : null
var info = phaseNum ? PHASES.find(function(p) { return p.num === phaseNum }) : null

if (!info) {
  log('## ⚠️ 缺少 phase 参数\n用法：{phase: 1, bugId: "001", bugDescription: "..."}\n\n可用阶段：')
  for (var i=0;i<PHASES.length;i++) log('  '+PHASES[i].num+'. '+PHASES[i].title)
} else if (!args || !args.bugId) {
  log('## ⚠️ 缺少 bugId 参数')
} else {
  try {
    if (info.type === 'merged') {
      await runMergedPhase(info)
    } else if (info.num === 3) {
      await runPhase3(info)
    }
  } catch(e) {
    log('❌ 阶段失败: ' + e.message)
  }
}

// ─── P1 / P2: Merged phase runner ─────────────────────────────────────────
async function runMergedPhase(info) {
  phase(info.title)
  var bugId = args.bugId, prev = await loadState('bug', bugId, info.needed || [])
  var fb = args.feedback ? '\n\n⚠️ 用户反馈：' + args.feedback : ''

  // Load previous phase results for reference when re-running with feedback
  var prevRef = ''
  if (fb) {
    var prevData = await loadPrevPhaseRef(bugId, info.num)
    if (prevData) {
      prevRef = '\n\n---\n## 上一轮产出（仅供参考，非绝对正确）\n以下是上一轮的完整分析结果。请结合用户反馈批判性地审视：保留仍适用的部分，修正反馈指出的问题，改进不足之处。不要全盘照抄，也不应无理由地推翻重来。\n\n' + JSON.stringify(prevData, null, 2)
      log('📄 已加载上一轮 P' + info.num + ' 产出作为参考')
    }
  }

  var dp = docPath(bugId, info.doc)
  var needed = info.needed || []
  for (var i = 0; i < needed.length; i++) { if (!prev[needed[i]]) { log('## ⚠️ 缺少 ' + needed[i]); return } }

  // Sub-step 1
  log('### 子步骤1：' + info.agent1)
  var r1 = await callAgent(info.prompt1(prev, bugId) + fb + prevRef + '\n\n---\n## 输出\n\n只返回结构化结果，**不要 Write 文件**（合并文档由后续步骤统一写入）。在 `documentPath` 字段填 "' + dp + '"，在 `summary` 字段给出100字以内摘要。', {agentType: info.agent1, phase: info.title, schema: info.schema1})
  if (!r1) { log('## ⚠️ 子步骤1未返回结果'); return }
  log('  ✅ 子步骤1完成: ' + (r1.summary || 'N/A'))

  // Sub-step 2 (receives sub-step 1 output as context)
  log('### 子步骤2：' + info.agent2)
  var r2 = await callAgent(info.prompt2(prev, bugId, r1) + fb + prevRef + docInst(dp, 'full'), {agentType: info.agent2, phase: info.title, schema: info.schema2})
  if (!r2) { log('## ⚠️ 子步骤2未返回结果'); return }
  log('  ✅ 子步骤2完成: ' + (r2.summary || 'N/A'))

  // Check feasibility gate for P2
  if (r2 && info.checkGate && info.checkGate(r2)) {
    log('⚠️ 评估未通过（建议: ' + (r2.recommendation||'N/A') + ', 可行性: ' + (r2.feasibility||'N/A') + '）。')
    log('请重新调用阶段2并传入 feedback 修改方案；如强制执行修复，请显式调用阶段3。')
    return
  }

  await writeState('bug', bugId, info.num, {step1: r1, step2: r2})

  log('## ✅ 阶段' + info.num + '完成：' + info.title + '\n**文档**: `' + dp + '`')
  outputNextStep(info)
}

// ─── P3: Implementation phase ──────────────────────────────────────────────
async function runPhase3(info) {
  phase('执行修复')
  var bugId = args.bugId, prev = await loadState('bug', bugId, info.needed || [])
  var fb = args.feedback ? '\n\n⚠️ 用户反馈：' + args.feedback : ''
  var needed = info.needed || []
  for (var i=0;i<needed.length;i++){ if(!prev[needed[i]]){ log('## ⚠️ 缺少 ' + needed[i]); return } }
  var p1 = prev.phase1, p2 = prev.phase2, dp = docPath(bugId, '执行修复.md')

  // ─── Resume support: load previous progress ──────────────
  var progressPath = 'docs/bug-' + bugId + '/.phase3-progress.json'
  var progress = {status: 'pending'}
  try {
    var pr = await callAgent(
      '读取 `' + progressPath + '`，在 `data` 字段返回文件的**原始内容**（不加代码块）。文件不存在则 `data` 留空字符串。',
      {agentType: 'developer', label: 'load-p3-progress', phase: '状态',
       schema: {type:'object', properties: {data:{type:'string'}}}}
    )
    if (pr && pr.data) { try { progress = JSON.parse(pr.data) } catch(e) {} }
  } catch(e) { /* non-blocking */ }

  if (progress.status === 'done') {
    log('📄 检测到修复已完成，跳过执行。如需重做请提供 feedback。')
    log('**文档**: `' + dp + '`')
    return
  }
  if (progress.status === 'in-progress') {
    log('📄 检测到上次修复中断，重新执行...')
  }

  log('## 🔧 阶段3：执行修复')
  log('**Bug分析**: ' + ((p1.step1 && p1.step1.summary) || (p1.step2 && p1.step2.summary) || '查看文档'))
  log('**方案与评估**: ' + ((p2.step1 && p2.step1.summary) || (p2.step2 && p2.step2.summary) || '查看文档'))
  log('')

  // ─── Fix ────────────────────────────────────────────────────────────
  // Build file context from P2 solution
  var solution = (p2.step1 && p2.step1.primarySolution) || {}
  var fileChanges = solution.fileChanges || []
  var references = solution.references || []
  var filesInfo = ''
  if (fileChanges.length || references.length) {
    filesInfo = '\n## 影响文件（来自方案与评估）\n'
    if (fileChanges.length) {
      filesInfo += '### 需修改/创建\n' + fileChanges.map(function(f) { return '- ' + f.file + ' (' + f.change + '): ' + f.description }).join('\n') + '\n'
    }
    if (references.length) {
      filesInfo += '### 只读依赖（类型/基类/工具）\n' + references.map(function(r) { return '- ' + r }).join('\n') + '\n'
    }
  }
  var fixResult = await callAgent(
    '执行Bug修复：\n\n## Bug分析\n' + JSON.stringify(p1, null, 2) + '\n\n## 方案与评估\n' + JSON.stringify(p2, null, 2) + filesInfo + '\n\n' + fb + '\n\n## 约束\n1. 以上述影响文件为起点，不主动探索项目全貌。仅在发现依赖缺失或设计矛盾时额外读取\n2. 修改文件实施修复 3. 编写/更新测试（若项目有测试框架） 4. 验证修复 5. 检查回归\n\n最后将修复记录写入 `' + dp + '`（含变更摘要、测试结果、验证步骤），并用 Write 更新进度 `' + progressPath + '` 写入 ' + JSON.stringify({status:'done'}) + '（直接写 JSON，不加代码块）。',
    { agentType: 'developer', phase: '执行修复' }
  )
  log('✅ 修复已执行')
  if (fixResult && fixResult.summary) { log('  摘要: ' + fixResult.summary) }

  // ─── Verification ───────────────────────────────────────────────────
  log('\n---\n## 🔍 验收')

  var verifyResult = await callAgent(
    '你是开发工程师。验收修复结果：\n1. 确认 Bug 复现步骤不再触发问题\n2. 运行测试（含新增的测试）确保通过\n3. 检查回归风险\n4. `verification` 字段输出验收结果\n5. `passed` 字段输出 true（Bug已修复）或 false（仍需处理）',
    { agentType: 'developer', phase: '执行修复', schema: { type:'object', required:['verification','passed'], properties:{ verification:{type:'string'}, passed:{type:'boolean'} } } }
  )
  if (verifyResult) { log('**验收结果**: ' + (verifyResult.passed ? '✅ Bug已修复' : '❌ 仍需处理') + '\n' + verifyResult.verification) }

  // ─── Stage files ────────────────────────────────────────────────────
  log('\n---\n## 📦 暂存文件')

  var stageResult = await callAgent(
    '你是开发工程师。执行：\n1. git add docs/bug-' + bugId + '/ 暂存过程文档（源码变更范围请用户 review `git status` 后确认）\n2. git diff --staged --stat 查看暂存结果\n3. `staged` 字段输出 git diff --staged --stat 结果\n4. `message` 字段输出确认信息',
    { agentType: 'developer', phase: '执行修复', schema: { type:'object', required:['staged','message'], properties:{ staged:{type:'string'}, message:{type:'string'} } } }
  )
  if (stageResult) { log('**暂存文件**:\n```\n' + stageResult.staged + '\n```\n' + stageResult.message) }

  // ─── Completion ─────────────────────────────────────────────────────
  log('\n---\n## 🎉 问题修复完成！')
  log('**文档**: `' + dp + '`')
  log('\n下一步：使用代码提交 workflow 生成 commit message。')
}
