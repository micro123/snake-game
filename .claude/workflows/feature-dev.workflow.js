export const meta = {
  name: 'feature-dev.workflow',
  description: '新功能开发（5阶段）。P1需求分析(P1+P2合并) → P2概要设计 → P3详细设计 → P4评估与排期(P5+P6合并) → P5实施',
  phases: [
    { title: '需求分析' }, { title: '概要设计' }, { title: '详细设计' },
    { title: '评估与排期' }, { title: '按计划实施' },
  ]
}

// ─── Schemas ───────────────────────────────────────────────────

const DOC_META = { documentPath: { type: 'string' }, summary: { type: 'string' } }
function addDoc(s) { return { ...s, properties: { ...s.properties, ...DOC_META } } }

const S1 = addDoc({ type:'object', required:['featureTitle','problemStatement','userStories','acceptanceCriteria'], properties:{ featureTitle:{type:'string'}, problemStatement:{type:'string'}, targetUsers:{type:'string'}, userStories:{type:'array',items:{type:'object',required:['role','want','soThat'],properties:{role:{type:'string'},want:{type:'string'},soThat:{type:'string'},priority:{type:'string',enum:['must-have','should-have','nice-to-have']}}}}, acceptanceCriteria:{type:'array',items:{type:'string'}}, scope:{type:'object',properties:{included:{type:'array',items:{type:'string'}},excluded:{type:'array',items:{type:'string'}}}}, dependencies:{type:'array',items:{type:'string'}}, assumptions:{type:'array',items:{type:'string'}} }})

const S2 = addDoc({ type:'object', required:['functionalRequirements','nonFunctionalRequirements'], properties:{ functionalRequirements:{type:'array',items:{type:'object',required:['id','description'],properties:{id:{type:'string'},description:{type:'string'},priority:{type:'string',enum:['P0','P1','P2','P3']},acceptanceCriteria:{type:'array',items:{type:'string'}}}}}, nonFunctionalRequirements:{type:'object',properties:{performance:{type:'array',items:{type:'string'}},security:{type:'array',items:{type:'string'}},usability:{type:'array',items:{type:'string'}},reliability:{type:'array',items:{type:'string'}}}}, constraints:{type:'array',items:{type:'string'}}, dataEntities:{type:'array',items:{type:'object',properties:{name:{type:'string'},fields:{type:'array',items:{type:'string'}},relationships:{type:'array',items:{type:'string'}}}}}, edgeCases:{type:'array',items:{type:'string'}}, integrationPoints:{type:'array',items:{type:'string'}} }})

const S3 = addDoc({ type:'object', required:['architecturePattern','components','techStack','designDecisions'], properties:{ architecturePattern:{type:'string'}, architectureRationale:{type:'string'}, components:{type:'array',items:{type:'object',required:['name','responsibility'],properties:{name:{type:'string'},responsibility:{type:'string'},interfaces:{type:'array',items:{type:'string'}},dependencies:{type:'array',items:{type:'string'}}}}}, techStack:{type:'object',properties:{frontend:{type:'array',items:{type:'string'}},backend:{type:'array',items:{type:'string'}},database:{type:'array',items:{type:'string'}},infrastructure:{type:'array',items:{type:'string'}},tools:{type:'array',items:{type:'string'}}}}, dataFlow:{type:'string'}, integrationPoints:{type:'array',items:{type:'object',properties:{name:{type:'string'},type:{type:'string',enum:['internal','external-api','database','message-queue','file-system']},description:{type:'string'}}}}, designDecisions:{type:'array',items:{type:'object',required:['decision','rationale'],properties:{decision:{type:'string'},rationale:{type:'string'},alternatives:{type:'array',items:{type:'string'}},tradeoffs:{type:'string'}}}} }})

const S4 = addDoc({ type:'object', required:['modules'], properties:{ modules:{type:'array',items:{type:'object',required:['name','classes'],properties:{name:{type:'string'},classes:{type:'array',items:{type:'object',properties:{name:{type:'string'},methods:{type:'array',items:{type:'string'}},properties:{type:'array',items:{type:'string'}},description:{type:'string'}}}},functions:{type:'array',items:{type:'string'}}}}}, apiEndpoints:{type:'array',items:{type:'object',required:['method','path'],properties:{method:{type:'string',enum:['GET','POST','PUT','PATCH','DELETE']},path:{type:'string'},description:{type:'string'},request:{type:'object',properties:{body:{type:'object'},params:{type:'object'},query:{type:'object'},headers:{type:'object'}}},response:{type:'object',properties:{status:{type:'integer'},body:{type:'object'}}},auth:{type:'string',enum:['none','bearer','api-key','session']}}}}, dataModels:{type:'array',items:{type:'object',required:['entity','fields'],properties:{entity:{type:'string'},fields:{type:'array',items:{type:'object',properties:{name:{type:'string'},type:{type:'string'},required:{type:'boolean'},description:{type:'string'},constraints:{type:'array',items:{type:'string'}}}}},relationships:{type:'array',items:{type:'object',properties:{entity:{type:'string'},type:{type:'string',enum:['one-to-one','one-to-many','many-to-many']},foreignKey:{type:'string'}}}}}}}, keyFlows:{type:'array',items:{type:'object',properties:{name:{type:'string'},steps:{type:'array',items:{type:'string'}},errorScenarios:{type:'array',items:{type:'string'}}}}}, errorHandling:{type:'object',properties:{strategy:{type:'string'},errorCodes:{type:'array',items:{type:'object',properties:{code:{type:'string'},httpStatus:{type:'integer'},message:{type:'string'},retryable:{type:'boolean'}}}},loggingStrategy:{type:'string'},fallbackStrategy:{type:'string'}}} }})

const S5 = addDoc({ type:'object', required:['difficultyScores','overallComplexity','risks','priority','effortEstimate'], properties:{ difficultyScores:{type:'array',items:{type:'object',required:['module','score'],properties:{module:{type:'string'},score:{type:'integer',minimum:1,maximum:5},reasoning:{type:'string'}}}}, overallComplexity:{type:'string',enum:['low','medium','high','very-high']}, complexityRationale:{type:'string'}, risks:{type:'array',items:{type:'object',required:['type','severity','description'],properties:{type:{type:'string',enum:['technical','dependency','timeline','security','performance']},severity:{type:'string',enum:['low','medium','high','critical']},description:{type:'string'},mitigation:{type:'string'}}}}, priority:{type:'string',enum:['P0','P1','P2','P3','P4']}, priorityRationale:{type:'string'}, effortEstimate:{type:'object',required:['min','max'],properties:{min:{type:'number'},max:{type:'number'},unit:{type:'string',enum:['person-day','person-week']}}}, dependencies:{type:'array',items:{type:'string'}}, suggestedApproach:{type:'string'} }})

const S6 = addDoc({ type:'object', required:['tasks','milestones','implementationOrder'], properties:{ tasks:{type:'array',items:{type:'object',required:['id','title','description','estimateHours'],properties:{id:{type:'string'},title:{type:'string'},description:{type:'string'},estimateHours:{type:'number'},dependencies:{type:'array',items:{type:'string'}},requiredSkills:{type:'array',items:{type:'string'}},module:{type:'string'},acceptanceCriteria:{type:'array',items:{type:'string'}}}}}, milestones:{type:'array',items:{type:'object',required:['name','targetTasks'],properties:{name:{type:'string'},description:{type:'string'},targetTasks:{type:'array',items:{type:'string'}}}}}, implementationOrder:{type:'array',items:{type:'object',properties:{phase:{type:'string'},taskIds:{type:'array',items:{type:'string'}},rationale:{type:'string'}}}}, riskMitigationTasks:{type:'array',items:{type:'object',properties:{risk:{type:'string'},mitigationTask:{type:'string'},timing:{type:'string',enum:['before-dev','during-dev','after-dev']}}}}, totalEffortSummary:{type:'object',properties:{totalPersonDays:{type:'number'},recommendedTeamSize:{type:'number'},estimatedCalendarDays:{type:'number'},confidenceLevel:{type:'string',enum:['high','medium','low']}}} }})

// ─── PHASES ────────────────────────────────────────────────────

var PHASES = [
  { num:1, title:'需求分析', type:'merged', agent1:'requirements-analyst', schema1:S1, agent2:'requirements-engineer', schema2:S2, doc:'需求分析.md' },
  { num:2, title:'概要设计', type:'single', agentType:'software-architect', schema:S3, doc:'概要设计.md', needed:['phase1'] },
  { num:3, title:'详细设计', type:'single', agentType:'senior-developer', schema:S4, doc:'详细设计.md', needed:['phase1','phase2'] },
  { num:4, title:'评估与排期', type:'merged', agent1:'tech-lead', schema1:S5, agent2:'project-manager', schema2:S6, doc:'评估与排期.md', needed:['phase1','phase3'] },
  { num:5, title:'按计划实施', type:'implement', agentType:'developer', doc:'按计划实施.md', needed:['phase1','phase2','phase3','phase4'] },
]

// ─── Helpers ───────────────────────────────────────────────────

function docPath(fn, doc) { return 'docs/feature-' + fn + '/' + doc }

function docInst(dp, mode) {
  if (mode === 'step1') {
    return '\n\n---\n## 文档输出\n\n完成分析后使用 Write 将结果写入 `' + dp + '`（子步骤1部分），在 `documentPath` 字段填 "' + dp + '"，在 `summary` 字段给出100字以内摘要。'
  }
  return '\n\n---\n## 文档输出\n\n完成分析后：\n1. 使用 Write 工具将完整的过程文档写入 `' + dp + '`\n   格式：Markdown，含标题(# 阶段名)、元信息(功能/阶段/角色/日期)、所有分析内容分节呈现\n2. 在返回的 `documentPath` 字段填 "' + dp + '"\n3. 在 `summary` 字段给出100字以内的摘要'
}

function buildPrompt(info, prev) {
  if (info.num === 2) {
    return '基于需求产出概要设计：\n\n## 需求分析\n' + JSON.stringify(prev.phase1, null, 2) + '\n\n输出：架构模式及理由、组件划分(职责/接口/依赖)、技术栈、数据流、集成点、设计决策(决策/理由/备选/权衡)。'
  }
  if (info.num === 3) {
    return '基于需求和概要设计产出详细设计：\n\n## 需求分析\n' + JSON.stringify(prev.phase1, null, 2) + '\n\n## 概要设计\n' + JSON.stringify(prev.phase2, null, 2) + '\n\n输出：模块设计(类名/方法/属性)、API端点(方法/路径/请求/响应/认证)、数据模型(实体/字段/类型/关系)、关键流程、错误处理。'
  }
  return ''
}

function outputNextStep(info) {
  var fn = args.featureName
  var n = info.num
  if (n >= 5) return
  var cmd = 'Workflow({scriptPath: ".claude/workflows/feature-dev.workflow.js", args: {phase: ' + (n + 1) + ', featureName: "' + fn + '"}})'
  if (n === 4) {
    log('')
    log('⚠️ **回退门禁（CLAUDE.md 规则）**：P4评估与排期完成后不得再回退到之前的步骤。如需修改请用 git revert。')
    log('⚠️ 请先阅读 `' + docPath(args.featureName, info.doc) + '` 确认后调用阶段5：')
    log('```\n' + cmd + '\n```')
  } else {
    log('')
    log('⚠️ 请先阅读 `' + docPath(args.featureName, info.doc) + '` 确认后调用阶段' + (n + 1) + '：')
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
  var dp = docPath(fn, info.doc)

  // Generic needed validation
  var needed = info.needed || []
  for (var ni = 0; ni < needed.length; ni++) {
    if (!prev[needed[ni]]) { log('## ⚠️ 缺少 ' + needed[ni]); return }
  }

  // Phase-specific setup
  var prompt1, prompt2
  if (info.num === 1) {
    var desc = args.featureDescription || '请根据项目上下文推断'
    prompt1 = '将功能描述转化为结构化需求定义：\n\n功能描述：' + desc + '\n\n输出：功能标题、问题陈述、目标用户、用户故事(As a...I want...So that...格式/优先级)、验收标准、范围边界(包含/不包含)、外部依赖、假设条件。'
    prompt2 = '基于需求定义撰写规格文档：\n\n## 需求定义\n{STEP1_OUTPUT}\n\n输出：功能需求(FR-001格式/优先级P0-P3/验收标准)、非功能需求(性能/安全/可用性/可靠性)、约束、数据实体、边界情况、集成点。'
  } else if (info.num === 4) {
    prompt1 = '基于需求和详细设计评估：\n\n## 需求分析\n' + JSON.stringify(prev.phase1, null, 2) + '\n\n## 详细设计\n' + JSON.stringify(prev.phase3, null, 2) + '\n\n输出：模块难度(1-5/理由)、整体复杂度、风险(类型/严重度/缓解)、优先级(P0-P4)、预估工时(最少-最多人天)、依赖、实施策略。'
    prompt2 = '基于需求、设计和评估排期：\n\n## 需求\n' + JSON.stringify(prev.phase1, null, 2) + '\n\n## 详细设计\n' + JSON.stringify(prev.phase3, null, 2) + '\n\n## 评估\n{STEP1_OUTPUT}\n\n输出：任务列表(T-001/标题/描述/工时/依赖/技能/模块/验收)、里程碑、实施顺序、风险缓解、总工时摘要。'
  }

  // Sub-step 1 (no file write — merge step writes the combined doc)
  log('---\n### 子步骤1：' + info.agent1)
  var r1 = await callAgent(prompt1 + fb + '\n\n---\n## 输出\n\n只返回结构化结果，**不要 Write 文件**（合并文档由后续步骤统一写入）。在 `documentPath` 字段填 "' + dp + '"，在 `summary` 字段给出100字以内摘要。', {agentType: info.agent1, phase: info.title, schema: info.schema1})
  if (!r1) { log('## ⚠️ 子步骤1未返回结果'); return }
  log('  ✅ 子步骤1完成: ' + (r1.summary || 'N/A'))

  // Sub-step 2 (receives sub-step 1 output)
  log('\n### 子步骤2：' + info.agent2)
  var step2Prompt = prompt2.replace('{STEP1_OUTPUT}', JSON.stringify(r1, null, 2))
  var r2 = await callAgent(step2Prompt + fb, {agentType: info.agent2, phase: info.title, schema: info.schema2})
  if (!r2) { log('## ⚠️ 子步骤2未返回结果'); return }
  log('  ✅ 子步骤2完成: ' + (r2.summary || 'N/A'))

  // Merge into one document
  log('\n### 子步骤3：合并文档')
  await callAgent(
    '将以下两部分分析合并为一份完整的过程文档写入 `' + dp + '`：\n\n## 第一部分\n' + JSON.stringify(r1, null, 2) + '\n\n## 第二部分\n' + JSON.stringify(r2, null, 2) + '\n\n格式：Markdown，含标题(# ' + info.title + ')、元信息(功能/' + fn + '/阶段/' + info.title + '/角色/' + info.agent1 + ' + ' + info.agent2 + '/日期)，所有内容分节呈现。',
    {agentType: info.agent2, phase: info.title}
  )

  log('\n## ✅ 阶段' + info.num + '完成：' + info.title)
  log('**文档**: `' + dp + '`')

  await writeState('feature', fn, info.num, {step1: r1, step2: r2})

  outputNextStep(info)
}

async function runSinglePhase(info) {
  phase(info.title)
  var fn = args.featureName, prev = await loadState('feature', fn, info.needed || [])
  var fb = args.feedback ? '\n\n⚠️ 用户反馈：' + args.feedback : ''
  var dp = docPath(fn, info.doc)

  var needed = info.needed || []
  for (var i = 0; i < needed.length; i++) {
    if (!prev[needed[i]]) { log('## ⚠️ 缺少 ' + needed[i]); return }
  }

  var prompt = buildPrompt(info, prev) + fb + docInst(dp, 'full')
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

  var p1 = prev.phase1, p4 = prev.phase4
  var p4tasks = (p4.step2 && p4.step2.tasks) || p4.tasks || []
  var p4order = (p4.step2 && p4.step2.implementationOrder) || p4.implementationOrder
  var dp = docPath(fn, '按计划实施.md')

  log('## 🔨 阶段5：按计划实施')
  log('**功能**: ' + ((p1.step1 && p1.step1.featureTitle) || (p1.featureTitle) || 'N/A') + ' | **任务数**: ' + p4tasks.length)

  if (fb) log(fb)

  var log_lines = ['# 按计划实施\n', '**功能**: ' + ((p1.step1 && p1.step1.featureTitle) || (p1.featureTitle) || 'N/A'), '**架构**: ' + ((prev.phase3 && prev.phase3.architecturePattern) || 'N/A'), '']
  if (p4tasks.length) {
    log_lines.push('## 任务清单\n')
    for (var i = 0; i < p4tasks.length; i++) {
      var t = p4tasks[i]
      log_lines.push('- **' + t.id + '** ' + t.title + ' (' + t.estimateHours + 'h)' + (t.dependencies && t.dependencies.length ? ' ← ' + t.dependencies.join(', ') : ''))
    }
    log_lines.push('')
  }

  if (p4order) {
    for (var j = 0; j < p4order.length; j++) {
      var ip = p4order[j]
      log('\n---\n### 📦 ' + ip.phase)
      if (ip.rationale) log(ip.rationale)
      log_lines.push('## ' + ip.phase + '\n')
      if (ip.rationale) log_lines.push(ip.rationale + '\n')

      var ptasks = p4tasks.filter(function(t) { return (ip.taskIds || []).indexOf(t.id) >= 0 })
      var total = ptasks.length
      for (var k = 0; k < ptasks.length; k++) {
        var task = ptasks[k]
        log('📦 进度 ' + (k + 1) + '/' + total + ' — ' + task.id + ' ' + task.title)
        log('\n#### 🔧 ' + task.id + ': ' + task.title + ' (' + task.estimateHours + 'h)')
        var tr = await callAgent(
          '实施任务：\n\n任务 ' + task.id + ': ' + task.title + '\n描述: ' + task.description + '\n工时: ' + task.estimateHours + 'h\n模块: ' + (task.module || 'N/A') + '\n验收: ' + (task.acceptanceCriteria ? task.acceptanceCriteria.join('; ') : 'N/A') + '\n\n## 需求\n' + JSON.stringify(p1, null, 2) + '\n\n## 详细设计\n' + JSON.stringify(prev.phase3, null, 2) + '\n\n请：1.阅读现有代码 2.修改/创建文件 3.编写测试（若项目有测试框架） 4.输出变更摘要',
          {agentType: 'developer', phase: '按计划实施'}
        )
        var trSummary = (tr && tr.summary) ? tr.summary : (tr ? JSON.stringify(tr) : 'N/A')
        log('✅ **' + task.id + '** ' + task.title + ' → ' + trSummary)
        log_lines.push('### ' + task.id + ' ' + task.title + '\n\n' + trSummary + '\n')
      }
    }
  } else if (p4tasks.length) {
    var total2 = p4tasks.length
    for (var m = 0; m < p4tasks.length; m++) {
      var t2 = p4tasks[m]
      log('📦 进度 ' + (m + 1) + '/' + total2 + ' — ' + t2.id + ' ' + t2.title)
      log('\n#### 🔧 ' + t2.id + ': ' + t2.title + ' (' + t2.estimateHours + 'h)')
      var tr2 = await callAgent(
        '实施任务 ' + t2.id + ': ' + t2.title + '\n描述: ' + t2.description + '\n工时: ' + t2.estimateHours + 'h\n模块: ' + (t2.module || 'N/A') + '\n\n产出文件变更和代码。3.编写测试（若项目有测试框架）',
        {agentType: 'developer', phase: '按计划实施'}
      )
      var tr2Summary = (tr2 && tr2.summary) ? tr2.summary : (tr2 ? JSON.stringify(tr2) : 'N/A')
      log('✅ **' + t2.id + '** ' + t2.title + ' → ' + tr2Summary)
      log_lines.push('### ' + t2.id + ' ' + t2.title + '\n\n' + tr2Summary + '\n')
    }
  }

  // ─── Write implementing doc ────────────────────────────────
  log('\n---\n### 写入实施文档')
  await callAgent(
    '将以下实施记录写入 `' + dp + '`：\n\n' + log_lines.join('\n') + '\n\n使用 Write 工具写入文件，末尾附验证检查清单。',
    {agentType: 'developer', label: '文档写入: 阶段5', phase: '按计划实施'}
  )

  // ─── Verification ─────────────────────────────────────────
  log('\n---')
  log('## 🔍 验收')
  var verifyResult = await callAgent(
    '你是开发工程师。验收实施结果：\n1. 检查所有文件变更是否完整、正确\n2. 运行测试确保通过\n3. 对照验收标准逐项确认\n4. `verification` 字段输出验收结果摘要\n5. `passed` 字段输出 true（通过）或 false（不通过）',
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
