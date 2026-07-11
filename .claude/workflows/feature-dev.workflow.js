export const meta = {
  name: 'feature-dev.workflow',
  description: '新功能开发（4阶段）。P1需求与设计(原需求分析+概要设计合并) → P2详细设计 → P3评估与排期 → P4按计划实施',
  phases: [
    { title: '需求与设计' }, { title: '详细设计' },
    { title: '评估与排期' }, { title: '按计划实施' },
  ]
}

// ─── Schemas ───────────────────────────────────────────────────

const DOC_META = { documentPath: { type: 'string' }, summary: { type: 'string' } }
function addDoc(s) { return { ...s, properties: { ...s.properties, ...DOC_META } } }

const S1 = addDoc({ type:'object', required:['featureTitle','problemStatement','userStories','acceptanceCriteria'], properties:{ featureTitle:{type:'string'}, problemStatement:{type:'string'}, targetUsers:{type:'string'}, userStories:{type:'array',items:{type:'object',required:['role','want','soThat'],properties:{role:{type:'string'},want:{type:'string'},soThat:{type:'string'},priority:{type:'string',enum:['must-have','should-have','nice-to-have']}}}}, acceptanceCriteria:{type:'array',items:{type:'string'}}, scope:{type:'object',properties:{included:{type:'array',items:{type:'string'}},excluded:{type:'array',items:{type:'string'}}}}, dependencies:{type:'array',items:{type:'string'}}, assumptions:{type:'array',items:{type:'string'}} }})

const S2 = addDoc({ type:'object', required:['functionalRequirements','nonFunctionalRequirements'], properties:{ functionalRequirements:{type:'array',items:{type:'object',required:['id','description'],properties:{id:{type:'string'},description:{type:'string'},priority:{type:'string',enum:['P0','P1','P2','P3']},acceptanceCriteria:{type:'array',items:{type:'string'}}}}}, nonFunctionalRequirements:{type:'object',properties:{performance:{type:'array',items:{type:'string'}},security:{type:'array',items:{type:'string'}},usability:{type:'array',items:{type:'string'}},reliability:{type:'array',items:{type:'string'}}}}, constraints:{type:'array',items:{type:'string'}}, dataEntities:{type:'array',items:{type:'object',properties:{name:{type:'string'},fields:{type:'array',items:{type:'string'}},relationships:{type:'array',items:{type:'string'}}}}}, edgeCases:{type:'array',items:{type:'string'}}, integrationPoints:{type:'array',items:{type:'string'}} }})

const S3 = addDoc({ type:'object', required:['architecturePattern','components','techStack','designDecisions'], properties:{ architecturePattern:{type:'string'}, architectureRationale:{type:'string'}, components:{type:'array',items:{type:'object',required:['name','responsibility'],properties:{name:{type:'string'},responsibility:{type:'string'},interfaces:{type:'array',items:{type:'string'}},dependencies:{type:'array',items:{type:'string'}}}}}, techStack:{type:'object',properties:{frontend:{type:'array',items:{type:'string'}},backend:{type:'array',items:{type:'string'}},database:{type:'array',items:{type:'string'}},infrastructure:{type:'array',items:{type:'string'}},tools:{type:'array',items:{type:'string'}}}}, dataFlow:{type:'string'}, integrationPoints:{type:'array',items:{type:'object',properties:{name:{type:'string'},type:{type:'string',enum:['internal','external-api','database','message-queue','file-system']},description:{type:'string'}}}}, designDecisions:{type:'array',items:{type:'object',required:['decision','rationale'],properties:{decision:{type:'string'},rationale:{type:'string'},alternatives:{type:'array',items:{type:'string'}},tradeoffs:{type:'string'}}}} }})

const S4 = addDoc({ type:'object', required:['modules'], properties:{ modules:{type:'array',items:{type:'object',required:['name','classes'],properties:{name:{type:'string'},files:{type:'object',properties:{affected:{type:'array',items:{type:'string'}},references:{type:'array',items:{type:'string'}}}},classes:{type:'array',items:{type:'object',properties:{name:{type:'string'},methods:{type:'array',items:{type:'string'}},properties:{type:'array',items:{type:'string'}},description:{type:'string'}}}},functions:{type:'array',items:{type:'string'}}}}}, apiEndpoints:{type:'array',items:{type:'object',required:['method','path'],properties:{method:{type:'string',enum:['GET','POST','PUT','PATCH','DELETE']},path:{type:'string'},description:{type:'string'},request:{type:'object',properties:{body:{type:'object'},params:{type:'object'},query:{type:'object'},headers:{type:'object'}}},response:{type:'object',properties:{status:{type:'integer'},body:{type:'object'}}},auth:{type:'string',enum:['none','bearer','api-key','session']}}}}, dataModels:{type:'array',items:{type:'object',required:['entity','fields'],properties:{entity:{type:'string'},fields:{type:'array',items:{type:'object',properties:{name:{type:'string'},type:{type:'string'},required:{type:'boolean'},description:{type:'string'},constraints:{type:'array',items:{type:'string'}}}}},relationships:{type:'array',items:{type:'object',properties:{entity:{type:'string'},type:{type:'string',enum:['one-to-one','one-to-many','many-to-many']},foreignKey:{type:'string'}}}}}}}, keyFlows:{type:'array',items:{type:'object',properties:{name:{type:'string'},steps:{type:'array',items:{type:'string'}},errorScenarios:{type:'array',items:{type:'string'}}}}}, errorHandling:{type:'object',properties:{strategy:{type:'string'},errorCodes:{type:'array',items:{type:'object',properties:{code:{type:'string'},httpStatus:{type:'integer'},message:{type:'string'},retryable:{type:'boolean'}}}},loggingStrategy:{type:'string'},fallbackStrategy:{type:'string'}}} }})

const S5 = addDoc({ type:'object', required:['difficultyScores','overallComplexity','risks','priority','effortEstimate'], properties:{ difficultyScores:{type:'array',items:{type:'object',required:['module','score'],properties:{module:{type:'string'},score:{type:'integer',minimum:1,maximum:5},reasoning:{type:'string'}}}}, overallComplexity:{type:'string',enum:['low','medium','high','very-high']}, complexityRationale:{type:'string'}, risks:{type:'array',items:{type:'object',required:['type','severity','description'],properties:{type:{type:'string',enum:['technical','dependency','timeline','security','performance']},severity:{type:'string',enum:['low','medium','high','critical']},description:{type:'string'},mitigation:{type:'string'}}}}, priority:{type:'string',enum:['P0','P1','P2','P3','P4']}, priorityRationale:{type:'string'}, effortEstimate:{type:'object',required:['min','max'],properties:{min:{type:'number'},max:{type:'number'},unit:{type:'string',enum:['person-day','person-week']}}}, dependencies:{type:'array',items:{type:'string'}}, suggestedApproach:{type:'string'} }})

const S6 = addDoc({ type:'object', required:['tasks','milestones','implementationOrder'], properties:{ tasks:{type:'array',items:{type:'object',required:['id','title','description','estimateHours'],properties:{id:{type:'string'},title:{type:'string'},description:{type:'string'},estimateHours:{type:'number'},dependencies:{type:'array',items:{type:'string'}},requiredSkills:{type:'array',items:{type:'string'}},module:{type:'string'},acceptanceCriteria:{type:'array',items:{type:'string'}}}}}, milestones:{type:'array',items:{type:'object',required:['name','targetTasks'],properties:{name:{type:'string'},description:{type:'string'},targetTasks:{type:'array',items:{type:'string'}}}}}, implementationOrder:{type:'array',items:{type:'object',properties:{phase:{type:'string'},taskIds:{type:'array',items:{type:'string'}},rationale:{type:'string'}}}}, riskMitigationTasks:{type:'array',items:{type:'object',properties:{risk:{type:'string'},mitigationTask:{type:'string'},timing:{type:'string',enum:['before-dev','during-dev','after-dev']}}}}, totalEffortSummary:{type:'object',properties:{totalPersonDays:{type:'number'},recommendedTeamSize:{type:'number'},estimatedCalendarDays:{type:'number'},confidenceLevel:{type:'string',enum:['high','medium','low']}}}, taskBatches:{type:'array',items:{type:'object',required:['name','taskIds','rationale'],properties:{name:{type:'string'},taskIds:{type:'array',items:{type:'string'}},rationale:{type:'string'},totalEstimateHours:{type:'number'}}}} }})

// ─── PHASES ────────────────────────────────────────────────────

var PHASES = [
  { num:1, title:'需求与设计', type:'merged', steps:[{agent:'requirements-analyst',schema:S1},{agent:'requirements-engineer',schema:S2, writeDoc:'需求分析.md', writeDocFrom:0},{agent:'software-architect',schema:S3, writeDoc:'概要设计.md'}], docs:[{file:'需求分析.md', fromSteps:[0,1], writer:'requirements-engineer'},{file:'概要设计.md', fromSteps:[2], writer:'software-architect'}] },
  { num:2, title:'详细设计', type:'single', agentType:'senior-developer', schema:S4, doc:'详细设计.md', needed:['phase1'] },
  { num:3, title:'评估与排期', type:'merged', steps:[{agent:'tech-lead',schema:S5},{agent:'project-manager',schema:S6, writeDoc:'评估与排期.md', writeDocFrom:0}], docs:[{file:'评估与排期.md', fromSteps:[0,1], writer:'project-manager'}], needed:['phase1','phase2'] },
  { num:4, title:'按计划实施', type:'implement', agentType:'developer', doc:'按计划实施.md', needed:['phase1','phase2','phase3'] },
]

// ─── Helpers ───────────────────────────────────────────────────

function docPath(fn, doc) { return 'docs/feature-' + fn + '/' + doc }

function phaseDocs(info) {
  if (info.docs) return info.docs.map(function(d) { return d.file })
  if (info.doc) return [info.doc]
  return []
}

function docInst(dp, mode) {
  if (mode === 'step1') {
    return '\n\n---\n## 文档输出\n\n完成分析后使用 Write 将结果写入 `' + dp + '`（子步骤1部分），在 `documentPath` 字段填 "' + dp + '"，在 `summary` 字段给出100字以内摘要。'
  }
  return '\n\n---\n## 文档输出\n\n完成分析后：\n1. 使用 Write 工具将完整的过程文档写入 `' + dp + '`\n   格式：Markdown，含标题(# 阶段名)、元信息(功能/阶段/角色/日期)、所有分析内容分节呈现\n2. 在返回的 `documentPath` 字段填 "' + dp + '"\n3. 在 `summary` 字段给出100字以内的摘要'
}

function buildPrompt(info, prev) {
  if (info.num === 2) {
    return '基于需求与设计（含需求分析+概要设计）产出详细设计：\n\n## 需求与设计\n' + JSON.stringify(prev.phase1, null, 2) + '\n\n输出：模块设计(类名/方法/属性/文件)、API端点(方法/路径/请求/响应/认证)、数据模型(实体/字段/类型/关系)、关键流程、错误处理。每个模块的 files 分 affected（需修改或创建的文件路径）和 references（只读依赖，如类型定义/工具类/基类）。文件路径要具体，即使尚不存在也列出预期路径。'
  }
  return ''
}

function outputNextStep(info) {
  var fn = args.featureName
  var n = info.num
  if (n >= 4) return
  var cmd = 'Workflow({scriptPath: ".claude/workflows/feature-dev.workflow.js", args: {phase: ' + (n + 1) + ', featureName: "' + fn + '"}})'
  var docs = phaseDocs(info).map(function(f) { return docPath(args.featureName, f) })
  var docsList = docs.map(function(d) { return '`' + d + '`' }).join(' + ')
  if (n === 3) {
    log('')
    log('⚠️ **回退门禁（CLAUDE.md 规则）**：P3评估与排期完成后不得再回退到之前的步骤。如需修改请用 git revert。')
    log('⚠️ 请先阅读 ' + docsList + ' 确认后调用阶段4：')
    log('```\n' + cmd + '\n```')
  } else {
    log('')
    log('⚠️ 请先阅读 ' + docsList + ' 确认后调用阶段' + (n + 1) + '：')
    log('```\n' + cmd + '\n```')
  }
}

// ─── callAgent with retry wrapper ─────────────────────────────

async function callAgent(prompt, options, retries) {
  if (retries === undefined) retries = 2
  for (var attempt = 0; attempt <= retries; attempt++) {
    try {
      return await agent(prompt, options)
    } catch (e) {
      if (attempt < retries) {
        log('⚠️ Agent调用失败（' + e.message + '），重试 ' + (attempt + 1) + '/' + retries + '...')
        continue
      }
      log('❌ Agent调用失败，已重试' + retries + '次: ' + e.message)
      log('💡 可重新调用本阶段并传入 feedback 重试。')
      throw e
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

// Load previous phase results for reference when re-running with feedback (non-blocking)
async function loadPrevPhaseRef(fn, phaseNum) {
  try {
    var filePath = 'docs/feature-' + fn + '/.phase' + phaseNum + '.json'
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

// ─── P4 Progress persistence (resume-after-interrupt) ──────────

function phase4ProgressPath(fn) { return 'docs/feature-' + fn + '/.phase4-progress.json' }

async function loadPhase4Progress(fn) {
  try {
    var fp = phase4ProgressPath(fn)
    var r = await callAgent(
      '读取 `' + fp + '`，在 `data` 字段返回文件的**原始内容**（一个字不改、不加代码块）。文件不存在则 `data` 留空字符串。',
      {agentType: 'developer', label: 'load-p4-progress', phase: '状态',
       schema: {type:'object', properties: {data:{type:'string'}}}}
    )
    if (r && r.data) {
      try { return JSON.parse(r.data) } catch(e) { log('⚠️ .phase4-progress.json 解析失败: ' + e.message) }
    }
  } catch(e) { /* non-blocking */ }
  return {completed: [], log_lines: []}
}

async function savePhase4Progress(fn, progress) {
  try {
    var fp = phase4ProgressPath(fn)
    var json = JSON.stringify(progress, null, 2)
    await callAgent(
      '将以下 JSON **原样**写入文件 `' + fp + '`（一个字符不改，不要 markdown 代码块，直接写 JSON 文本）：\n\n' + json,
      {agentType: 'developer', label: 'save-p4-progress', phase: '按计划实施'}
    )
  } catch(e) { log('⚠️ 保存进度失败: ' + e.message) }
}

// ─── Dispatch ──────────────────────────────────────────────────

// args 字符串容错（Workflow 调用时 args 可能被当字符串注入）
if (typeof args === 'string') { try { args = JSON.parse(args) } catch (e) { args = {} } }
if (!args || typeof args !== 'object') args = {}

var phaseNum = (args && args.phase) ? Number(args.phase) : null
var info = phaseNum ? PHASES.find(function(p) { return p.num === phaseNum }) : null

async function main() {
  if (!info) {
    log('## ⚠️ 缺少 phase 参数\n用法：{phase: 1, featureName: "login", featureDescription: "..."}\n\n可用阶段：')
    for (var i = 0; i < PHASES.length; i++) log('  ' + PHASES[i].num + '. ' + PHASES[i].title)
  } else if (!args || !args.featureName) {
    log('## ⚠️ 缺少 featureName 参数')
  } else if (info.type === 'merged') {
    await runMergedPhase(info)
  } else if (info.type === 'single') {
    await runSinglePhase(info)
  } else if (info.type === 'implement') {
    await runImplementPhase(info)
  }
}

try {
  await main()
} catch (e) {
  log('❌ 阶段失败: ' + (e && e.message ? e.message : String(e)))
}

// ─── Phase Implementations ─────────────────────────────────────

async function runMergedPhase(info) {
  phase(info.title)
  var fn = args.featureName, prev = await loadState('feature', fn, info.needed || [])
  var fb = args.feedback ? '\n\n⚠️ 用户反馈：' + args.feedback : ''
  var docs = info.docs || []
  var firstDp = docs.length ? docPath(fn, docs[0].file) : docPath(fn, info.doc)

  // Generic needed validation
  var needed = info.needed || []
  for (var ni = 0; ni < needed.length; ni++) {
    if (!prev[needed[ni]]) { log('## ⚠️ 缺少 ' + needed[ni]); return }
  }

  // Build per-step prompts based on phase + step index
  var steps = info.steps
  var prompts = []

  // P1 需求与设计 (3 sub-steps: 需求分析师 → 需求工程师 → 架构师)
  if (info.num === 1) {
    var desc = args.featureDescription || '请根据项目上下文推断'

    // Load previous phase1 results for reference when re-running with feedback
    var prevRef = ''
    if (fb) {
      var prevData = await loadPrevPhaseRef(fn, 1)
      if (prevData) {
        prevRef = '\n\n---\n## 上一轮产出（仅供参考，非绝对正确）\n以下是上一轮的完整分析结果。请结合用户反馈批判性地审视：保留仍适用的部分，修正反馈指出的问题，改进不足之处。不要全盘照抄，也不应无理由地推翻重来。\n\n' + JSON.stringify(prevData, null, 2)
        log('📄 已加载上一轮 P1 产出作为参考')
      }
    }

    prompts.push('将功能描述转化为结构化需求定义。用户故事是全文的锚点——先搞清楚"谁、要什么、为什么"，后续所有分析（功能需求、数据实体、边界情况等）都应回应用户故事提出的问题，避免发散。\n\n功能描述：' + desc + '\n\n输出（按顺序）：\n1. 功能标题、问题陈述\n2. 用户故事(As a...I want...So that...格式/优先级)——作为全文锚点置于文档前部\n3. 目标用户、验收标准、范围边界(包含/不包含)\n4. 外部依赖、假设条件' + prevRef)
    prompts.push('基于需求定义撰写规格文档：\n\n## 需求定义\n{PREV_OUTPUTS}\n\n输出：功能需求(FR-001格式/优先级P0-P3/验收标准)、非功能需求(性能/安全/可用性/可靠性)、约束、数据实体、边界情况、集成点。' + prevRef)
    prompts.push('基于需求和规格产出概要设计：\n\n## 需求定义\n{PREV_OUTPUTS}\n\n输出：架构模式及理由、组件划分(职责/接口/依赖)、技术栈、数据流、集成点、设计决策(决策/理由/备选/权衡)。' + prevRef)
  }
  // P3 评估与排期 (2 sub-steps: Tech Lead → 项目经理)
  else if (info.num === 3) {
    // Load previous phase3 results for reference when re-running with feedback
    var prevRef = ''
    if (fb) {
      var prevData = await loadPrevPhaseRef(fn, 3)
      if (prevData) {
        prevRef = '\n\n---\n## 上一轮产出（仅供参考，非绝对正确）\n以下是上一轮的完整分析结果。请结合用户反馈批判性地审视：保留仍适用的部分，修正反馈指出的问题，改进不足之处。不要全盘照抄，也不应无理由地推翻重来。\n\n' + JSON.stringify(prevData, null, 2)
        log('📄 已加载上一轮 P3 产出作为参考')
      }
    }

    prompts.push('基于需求和详细设计评估（P2 已含模块/文件/API/数据模型，足够评估）：\n\n## 需求与设计\n' + JSON.stringify(prev.phase1, null, 2) + '\n\n## 详细设计\n' + JSON.stringify(prev.phase2, null, 2) + '\n\n不主动读源码——基于 P2 设计直接评估。仅在发现设计中有明显疑点或缺失信息时才读源码验证。输出：模块难度(1-5/理由)、整体复杂度、风险(类型/严重度/缓解)、优先级(P0-P4)、预估工时(最少-最多人天)、依赖、实施策略。' + prevRef)
    prompts.push('基于需求、设计和评估排期：\n\n## 需求与设计\n' + JSON.stringify(prev.phase1, null, 2) + '\n\n## 详细设计\n' + JSON.stringify(prev.phase2, null, 2) + '\n\n## 评估\n{PREV_OUTPUTS}\n\n输出：任务列表(T-001/标题/描述/工时/依赖/技能/模块/验收)、里程碑、实施顺序、风险缓解、总工时摘要。taskBatches：根据任务依赖关系与实施顺序，将修改同一模块/共享同一文件/逻辑上紧密连续的任务归入同一批次以便实施阶段一次性完成。要求：(1) 每批次总工时 ≤4h (2) 每个 task 只出现在一个批次中 (3) 批次按执行先后排序 (4) 命名体现该批次的主题。' + prevRef)
  }

  // Run each sub-step sequentially, injecting all prior results
  var results = []
  for (var si = 0; si < steps.length; si++) {
    var s = steps[si]
    log('---\n### 子步骤' + (si + 1) + '：' + s.agent)
    var p = prompts[si]
    if (si > 0) {
      // Inject all prior sub-step results as JSON
      var prevOutputs = ''
      for (var pi = 0; pi < si; pi++) {
        prevOutputs += '\n## 子步骤' + (pi + 1) + ' 输出\n' + JSON.stringify(results[pi], null, 2) + '\n'
      }
      p = p.replace('{PREV_OUTPUTS}', prevOutputs.trim())
    }
    var tailInst = s.writeDoc
      ? (s.writeDocFrom !== undefined
        ? '\n\n---\n## 文档输出\n\n使用 Write 工具将第' + (s.writeDocFrom + 1) + '至' + (si + 1) + '子步骤的输出整合为完整的过程文档写入 `' + docPath(fn, s.writeDoc) + '`。格式：Markdown，含标题、元信息、所有分析内容分节呈现。在返回的 `documentPath` 字段填该路径，在 `summary` 字段给出100字以内摘要。'
        : docInst(docPath(fn, s.writeDoc), 'full'))
      : '\n\n---\n## 输出\n\n只返回结构化结果，**不要 Write 文件**（文档由后续步骤统一写入）。在 `documentPath` 字段填 "' + firstDp + '"，在 `summary` 字段给出100字以内摘要。'
    var r = await callAgent(p + fb + tailInst,
      {agentType: s.agent, phase: info.title, schema: s.schema})
    if (!r) { log('## ⚠️ 子步骤' + (si + 1) + '未返回结果'); return }
    log('  ✅ 子步骤' + (si + 1) + '完成: ' + (r.summary || 'N/A'))
    results.push(r)
  }

  var docsList = docs.map(function(d) { return '`' + docPath(fn, d.file) + '`' }).join(' + ')
  log('\n## ✅ 阶段' + info.num + '完成：' + info.title)
  log('**文档**: ' + docsList)

  // Dynamic state object {step1, step2, ..., stepN}
  var stateObj = {}
  for (var sti = 0; sti < results.length; sti++) {
    stateObj['step' + (sti + 1)] = results[sti]
  }
  await writeState('feature', fn, info.num, stateObj)

  outputNextStep(info)
}

async function runSinglePhase(info) {
  phase(info.title)
  var fn = args.featureName, prev = await loadState('feature', fn, info.needed || [])
  var fb = args.feedback ? '\n\n⚠️ 用户反馈：' + args.feedback : ''

  // Load previous phase results for reference when re-running with feedback
  var prevRef = ''
  if (fb) {
    var prevData = await loadPrevPhaseRef(fn, info.num)
    if (prevData) {
      prevRef = '\n\n---\n## 上一轮产出（仅供参考，非绝对正确）\n以下是上一轮的完整分析结果。请结合用户反馈批判性地审视：保留仍适用的部分，修正反馈指出的问题，改进不足之处。不要全盘照抄，也不应无理由地推翻重来。\n\n' + JSON.stringify(prevData, null, 2)
      log('📄 已加载上一轮 P' + info.num + ' 产出作为参考')
    }
  }

  var dp = docPath(fn, info.doc)

  var needed = info.needed || []
  for (var i = 0; i < needed.length; i++) {
    if (!prev[needed[i]]) { log('## ⚠️ 缺少 ' + needed[i]); return }
  }

  var prompt = buildPrompt(info, prev) + fb + prevRef + docInst(dp, 'full')
  var r = await callAgent(prompt, {agentType: info.agentType, phase: info.title, schema: info.schema})
  if (!r) { log('## ⚠️ 阶段未返回结果'); return }

  log('\n## ✅ 阶段' + info.num + '完成：' + info.title)
  log('**文档**: `' + dp + '`')
  log('**摘要**: ' + (r.summary || 'N/A'))

  await writeState('feature', fn, info.num, r)

  outputNextStep(info)
}

async function runImplementPhase(info) {
  phase('按计划实施')
  var fn = args.featureName, prev = await loadState('feature', fn, info.needed || [])
  var fb = args.feedback ? '\n\n⚠️ 用户反馈：' + args.feedback : ''

  var needed = info.needed || []
  for (var i = 0; i < needed.length; i++) {
    if (!prev[needed[i]]) { log('## ⚠️ 缺少 ' + needed[i]); return }
  }

  var p1 = prev.phase1, p3 = prev.phase3
  var p3tasks = (p3.step2 && p3.step2.tasks) || p3.tasks || []
  var p3order = (p3.step2 && p3.step2.implementationOrder) || p3.implementationOrder
  var dp = docPath(fn, '按计划实施.md')

  // ─── Resume support: load previous progress ──────────────
  var progress = await loadPhase4Progress(fn)
  var completed = progress.completed || []
  var isResume = completed.length > 0

  if (isResume) {
    log('📄 检测到中断恢复：已完成 ' + completed.length + ' 个任务 [' + completed.join(', ') + ']')
    if (!fb && !args.resume) {
      log('💡 如需从头开始，请设置 resume: false 或提供 feedback')
    }
  }

  log('## 🔨 阶段4：按计划实施')
  log('**功能**: ' + ((p1.step1 && p1.step1.featureTitle) || (p1.featureTitle) || 'N/A') + ' | **任务数**: ' + p3tasks.length)

  if (fb) log(fb)

  // Build task list with completion markers
  var log_lines = isResume ? progress.log_lines : ['# 按计划实施\n', '**功能**: ' + ((p1.step1 && p1.step1.featureTitle) || (p1.featureTitle) || 'N/A'), '**架构**: ' + ((p1.step3 && p1.step3.architecturePattern) || 'N/A'), '']
  if (p3tasks.length) {
    log_lines.push('## 任务清单\n')
    for (var i = 0; i < p3tasks.length; i++) {
      var t = p3tasks[i]
      var done = completed.indexOf(t.id) >= 0 ? ' ✅' : ''
      log_lines.push('- **' + t.id + '** ' + t.title + ' (' + t.estimateHours + 'h)' + (t.dependencies && t.dependencies.length ? ' ← ' + t.dependencies.join(', ') : '') + done)
    }
    log_lines.push('')
  }

  // ── Task batch mode (P3 taskBatches) ──
  var p3batches = (p3.step2 && p3.step2.taskBatches) || p3.taskBatches || null
  if (p3batches && p3batches.length) {
    log('\n## 🔧 批量实施（' + p3batches.length + ' 批次）')
    for (var bj = 0; bj < p3batches.length; bj++) {
      var batch = p3batches[bj]
      var bTasks = p3tasks.filter(function(t) { return (batch.taskIds || []).indexOf(t.id) >= 0 })
      var remaining = bTasks.filter(function(t) { return completed.indexOf(t.id) < 0 })
      if (!remaining.length) { log('⏭️ 批次完成: ' + batch.name); continue }
      log('\n### 📦 批次 ' + (bj + 1) + '/' + p3batches.length + ': ' + batch.name + ' (' + remaining.length + ' 任务, ' + (batch.totalEstimateHours || '?') + 'h)')
      if (batch.rationale) log(batch.rationale)
      // Build batch task list
      var batchTaskList = ''
      for (var bt = 0; bt < remaining.length; bt++) {
        var bTask = remaining[bt]
        batchTaskList += '\n### ' + bTask.id + ': ' + bTask.title + ' (' + bTask.estimateHours + 'h)\n描述: ' + bTask.description + '\n验收: ' + (bTask.acceptanceCriteria ? bTask.acceptanceCriteria.join('; ') : 'N/A') + '\n模块: ' + (bTask.module || 'N/A')
      }
      var batchCompleted = completed.concat(batch.taskIds || [])
      var progressJson = JSON.stringify({completed: batchCompleted})
      var tr = await callAgent(
        '按顺序完成以下 ' + remaining.length + ' 个紧密相关的任务：\n' + batchTaskList + '\n\n## 需求与设计\n' + JSON.stringify(p1, null, 2) + '\n\n## 详细设计\n' + JSON.stringify(prev.phase2, null, 2) + '\n\n## 约束\n1. 以上述文件为起点，仅在发现依赖缺失或设计矛盾时额外读取。不主动探索项目全貌\n2. 按编号顺序实施，修改/创建文件\n3. 编写测试（若项目有测试框架）\n4. 每个任务完成后输出简短摘要，全部完成后给出总体变更摘要(≤150字)\n5. 最后用 Write 将进度写入 `' + pp + '`（直接写 JSON 文本，不加代码块）：' + progressJson,
        {agentType: 'developer', phase: '按计划实施'}
      )
      var trSummary = (tr && tr.summary) ? tr.summary : (tr ? JSON.stringify(tr) : 'N/A')
      log('✅ **批次 ' + batch.name + '** → ' + trSummary)
      log_lines.push('## 📦 ' + batch.name + '\n\n' + trSummary + '\n')
      completed = batchCompleted   // mark all batch tasks done
      progress.completed = completed
      progress.log_lines = log_lines
    }
    log('📄 进度已保存: ' + completed.length + '/' + p3tasks.length + ' 任务完成')
  }

  else if (p3order) {
    for (var j = 0; j < p3order.length; j++) {
      var ip = p3order[j]
      log('\n---\n### 📦 ' + ip.phase)
      if (ip.rationale) log(ip.rationale)
      if (!isResume) { log_lines.push('## ' + ip.phase + '\n'); if (ip.rationale) log_lines.push(ip.rationale + '\n') }

      var ptasks = p3tasks.filter(function(t) { return (ip.taskIds || []).indexOf(t.id) >= 0 })
      var remaining = ptasks.filter(function(t) { return completed.indexOf(t.id) < 0 })
      var total = ptasks.length
      for (var k = 0; k < ptasks.length; k++) {
        var task = ptasks[k]
        // Skip already completed tasks
        if (completed.indexOf(task.id) >= 0) {
          log('⏭️ 跳过已完成: ' + task.id + ' ' + task.title)
          continue
        }
        var doneCount = completed.length
        log('📦 进度 ' + (k + 1) + '/' + total + ' — ' + task.id + ' ' + task.title + ' (已完成: ' + doneCount + ')')
        log('\n#### 🔧 ' + task.id + ': ' + task.title + ' (' + task.estimateHours + 'h)')
        // Build file context from P2 detailed design
          var p2modules = (prev.phase2 && prev.phase2.modules) || []
          var taskModule = p2modules.find(function(m) { return m.name === (task.module || '') })
          var filesInfo = ''
          if (taskModule && taskModule.files) {
            filesInfo = '\n## 影响文件（来自详细设计）\n'
            if (taskModule.files.affected && taskModule.files.affected.length) {
              filesInfo += '### 需修改/创建\n' + taskModule.files.affected.map(function(f) { return '- ' + f }).join('\n') + '\n'
            }
            if (taskModule.files.references && taskModule.files.references.length) {
              filesInfo += '### 只读依赖（类型/基类/工具）\n' + taskModule.files.references.map(function(f) { return '- ' + f }).join('\n') + '\n'
            }
          }
          var newCompleted = completed.concat([task.id])
          var progressJson = JSON.stringify({completed: newCompleted})
          var tr = await callAgent(
          '实施任务：\n\n任务 ' + task.id + ': ' + task.title + '\n描述: ' + task.description + '\n工时: ' + task.estimateHours + 'h\n模块: ' + (task.module || 'N/A') + '\n验收: ' + (task.acceptanceCriteria ? task.acceptanceCriteria.join('; ') : 'N/A') + filesInfo + '\n\n## 需求与设计\n' + JSON.stringify(p1, null, 2) + '\n\n## 详细设计\n' + JSON.stringify(prev.phase2, null, 2) + '\n\n## 约束\n1. 以上述影响文件为起点，不主动探索项目全貌。仅在发现依赖缺失或设计与实际代码矛盾时，才额外读取相关文件\n2. 修改/创建文件 3. 编写测试（若项目有测试框架） 4. 输出变更摘要\n5. 最后用 Write 将进度写入 `' + pp + '`（直接写 JSON 文本，不加代码块）：' + progressJson,
          {agentType: 'developer', phase: '按计划实施'}
        )
        var trSummary = (tr && tr.summary) ? tr.summary : (tr ? JSON.stringify(tr) : 'N/A')
        log('✅ **' + task.id + '** ' + task.title + ' → ' + trSummary)
        log_lines.push('### ' + task.id + ' ' + task.title + '\n\n' + trSummary + '\n')
        completed.push(task.id)
        progress.completed = completed
        progress.log_lines = log_lines
      }
    }
  } else if (p3tasks.length) {
    var total2 = p3tasks.length
    for (var m = 0; m < p3tasks.length; m++) {
      var t2 = p3tasks[m]
      // Skip already completed tasks
      if (completed.indexOf(t2.id) >= 0) {
        log('⏭️ 跳过已完成: ' + t2.id + ' ' + t2.title)
        continue
      }
      var doneCount2 = completed.length
      log('📦 进度 ' + (m + 1) + '/' + total2 + ' — ' + t2.id + ' ' + t2.title + ' (已完成: ' + doneCount2 + ')')
      log('\n#### 🔧 ' + t2.id + ': ' + t2.title + ' (' + t2.estimateHours + 'h)')
      var newCompleted2 = completed.concat([t2.id])
      var progressJson2 = JSON.stringify({completed: newCompleted2})
      var tr2 = await callAgent(
        '实施任务：\n\n任务 ' + t2.id + ': ' + t2.title + '\n描述: ' + t2.description + '\n工时: ' + t2.estimateHours + 'h\n模块: ' + (t2.module || 'N/A') + '\n\n## 约束\n1. 以该模块涉及的文件为起点，仅在发现依赖缺失或设计矛盾时才额外读取。不主动探索项目全貌\n2. 输出文件变更和代码 3. 编写测试（若项目有测试框架） 4. 输出变更摘要\n5. 最后用 Write 将进度写入 `' + pp + '`（直接写 JSON 文本，不加代码块）：' + progressJson2,
        {agentType: 'developer', phase: '按计划实施'}
      )
      var tr2Summary = (tr2 && tr2.summary) ? tr2.summary : (tr2 ? JSON.stringify(tr2) : 'N/A')
      log('✅ **' + t2.id + '** ' + t2.title + ' → ' + tr2Summary)
      log_lines.push('### ' + t2.id + ' ' + t2.title + '\n\n' + tr2Summary + '\n')
      completed.push(t2.id)
      progress.completed = completed
      progress.log_lines = log_lines
    }
  }

  // ─── Clean up progress file ──────────────────────────────
  await savePhase4Progress(fn, {completed: completed, log_lines: log_lines, finished: true})
  log('📄 进度已保存: ' + completed.length + '/' + p3tasks.length + ' 任务完成')

  // ─── Verification ─────────────────────────────────────────
  log('\n---')
  log('## 🔍 验收')
  var verifyResult = await callAgent(
    '你是开发工程师。验收实施结果：\n1. 检查所有文件变更是否完整、正确\n2. 运行测试确保通过\n3. 对照验收标准逐项确认\n4. `verification` 字段输出验收结果摘要\n5. `passed` 字段输出 true（通过）或 false（不通过）\n6. 用 Write 将实施记录写入 `' + dp + '`（从下方 log_lines 取内容，Markdown格式，末尾附验证检查清单）\n\n---\n## 实施记录\n' + log_lines.join('\n'),
    {agentType: 'developer', phase: '按计划实施', schema: { type: 'object', required: ['verification', 'passed'], properties: { verification: { type: 'string' }, passed: { type: 'boolean' } } } }
  )
  if (verifyResult) {
    log('**验收结果**: ' + (verifyResult.passed ? '✅ 通过' : '❌ 不通过'))
    log(verifyResult.verification)
  }

  // ─── Stage files ──────────────────────────────────────────
  log('\n---')
  log('## 📦 暂存文件')
  var stageResult = await callAgent(
    '你是开发工程师。执行：\n1. git add docs/feature-' + fn + '/ 暂存过程文档\n2. git diff --staged --stat 查看暂存结果\n3. `staged` 字段输出 git diff --staged --stat 结果\n4. `message` 字段输出确认信息\n\n注意：源码变更范围请用户 review `git status` 后确认，不要使用 `git add -A`。',
    {agentType: 'developer', phase: '按计划实施', schema: { type: 'object', required: ['staged', 'message'], properties: { staged: { type: 'string' }, message: { type: 'string' } } } }
  )
  if (stageResult) {
    log('**暂存文件**:\n```\n' + stageResult.staged + '\n```')
    log(stageResult.message)
    log('💡 源码变更范围请 review `git status` 后自行确认是否暂存。')
  }

  log('\n下一步：使用代码提交 workflow 生成 commit message。')
  log('\n---')
  log('## 🎉 工作流完成！')
  log('**文档**: `' + dp + '`')
}
