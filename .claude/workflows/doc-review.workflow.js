export const meta = {
  name: 'doc-review.workflow',
  description: '文档审查（单阶段）：并行3视角审查（梦想家/实业家/批评家）→ 合并生成修改意见。',
  phases: [
    { title: '审查与合成' }
  ]
}

const REVIEW_SCHEMA = {
  type: 'object',
  required: ['perspective', 'keyFindings', 'suggestions'],
  properties: {
    perspective: { type: 'string' },
    keyFindings: { type: 'array', items: { type: 'string' }, maxItems: 5 },
    suggestions: { type: 'array', items: { type: 'string' }, maxItems: 5 }
  }
}

const SYNTH_SCHEMA = {
  type: 'object',
  required: ['summary', 'suggestions'],
  properties: {
    summary: { type: 'string' },
    suggestions: {
      type: 'array',
      items: {
        type: 'object',
        required: ['priority', 'content', 'source'],
        properties: {
          priority: { type: 'string', enum: ['P0', 'P1', 'P2'] },
          content: { type: 'string' },
          source: { type: 'string', enum: ['梦想家', '实业家', '批评家', '合并'] }
        }
      },
      maxItems: 10
    }
  }
}

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
      throw e
    }
  }
}

if (typeof args === 'string') { try { args = JSON.parse(args) } catch (e) { args = {} } }
if (!args || typeof args !== 'object') args = {}

var phaseNum = (args && args.phase) ? Number(args.phase) : null

async function main() {
  if (phaseNum !== 1) {
    log('## ⚠️ 缺少 phase 参数或 phase 不为 1')
    log('用法：{phase: 1, featureName: "xxx"}')
    return
  }
  if (!args || !args.featureName) {
    log('## ⚠️ 缺少 featureName 参数')
    return
  }
  return await runReviewPhase()
}

var result
try {
  result = await main()
} catch (e) {
  log('❌ 阶段失败: ' + (e && e.message ? e.message : String(e)))
}
return result

async function runReviewPhase() {
  phase('审查与合成')
  var fn = args.featureName
  var dp1 = 'docs/feature-' + fn + '/需求分析.md'
  var dp2 = 'docs/feature-' + fn + '/概要设计.md'

  log('## 📋 文档审查：' + fn)
  log('**审查文档**: `' + dp1 + '` + `' + dp2 + '`')

  log('\n---\n### 并行审查（3视角：梦想家/实业家/批评家）')

  var reviews = await parallel([
    function() { return callAgent(
      '你是"梦想家"审查视角，关注愿景、创新性、用户价值。\n\n请阅读以下两份文档，从梦想家视角审查：\n\n## 需求分析\n`' + dp1 + '`\n\n## 概要设计\n`' + dp2 + '`\n\n审查要点：\n- 需求是否解决真实问题？愿景是否足够大胆？\n- 有无遗漏的创新机会？设计是否过于保守？\n- 每条 keyFinding 和 suggestion 一句话（≤50字）。',
      { agentType: 'general-purpose', label: '梦想家审查', phase: '审查与合成', schema: REVIEW_SCHEMA }
    ) },
    function() { return callAgent(
      '你是"实业家"审查视角，关注可行性、实施成本、务实性。\n\n请阅读以下两份文档，从实业家视角审查：\n\n## 需求分析\n`' + dp1 + '`\n\n## 概要设计\n`' + dp2 + '`\n\n审查要点：\n- 方案是否现实可行？有无更简单做法？\n- MVP 范围是否合理？技术选型是否过重？\n- 每条 keyFinding 和 suggestion 一句话（≤50字）。',
      { agentType: 'general-purpose', label: '实业家审查', phase: '审查与合成', schema: REVIEW_SCHEMA }
    ) },
    function() { return callAgent(
      '你是"批评家"审查视角，关注风险、漏洞、边界。\n\n请阅读以下两份文档，从批评家视角审查：\n\n## 需求分析\n`' + dp1 + '`\n\n## 概要设计\n`' + dp2 + '`\n\n审查要点：\n- 哪里会出问题？哪些边界遗漏？\n- 安全/性能隐患？哪些假设可能不成立？\n- 每条 keyFinding 和 suggestion 一句话（≤50字）。',
      { agentType: 'general-purpose', label: '批评家审查', phase: '审查与合成', schema: REVIEW_SCHEMA }
    ) }
  ])

  var validReviews = reviews.filter(Boolean)
  if (validReviews.length === 0) {
    log('## ⚠️ 所有审查者均未返回结果')
    return
  }

  log('✅ 审查完成：' + validReviews.length + '/' + 3 + ' 个视角返回结果')

  log('\n---\n### 整理合并')

  var perspectiveNames = ['梦想家', '实业家', '批评家']
  var synthInput = ''
  for (var i = 0; i < reviews.length; i++) {
    if (reviews[i]) {
      synthInput += '\n## ' + perspectiveNames[i] + '审查结果\n' + JSON.stringify(reviews[i], null, 2) + '\n'
    }
  }

  var synthResult = await callAgent(
    '你是文档审查整理者。接收3个视角的审查结果，去重合并生成结构化修改意见。\n\n' + synthInput + '\n\n要求：\n1. 去重合并同类建议（多视角共同关注则标注 source 为"合并"）\n2. 按优先级 P0（严重）/P1（重要）/P2（建议）排列\n3. 总数 ≤10 条\n4. 每项注明来源视角（单一视角写视角名，多视角写"合并"）',
    { agentType: 'general-purpose', label: '整理合并', phase: '审查与合成', schema: SYNTH_SCHEMA }
  )

  if (!synthResult) {
    log('## ⚠️ 整理者未返回结果')
    return
  }

  var docPathOut = 'docs/feature-' + fn + '/文档审查.md'

  log('\n---\n### 校准优先级')

  var calibrateResult = await callAgent(
    '你是文档审查的校准师。你的职责不是再审查一遍原始文档，而是审视整理者合并的建议列表，校准其优先级和必要性。\n\n' +
    '## 整理结果\n' + JSON.stringify(synthResult, null, 2) + '\n\n' +
    '## 三视角原始审查\n' + synthInput + '\n\n' +
    '校准要点：\n' +
    '1. **优先级校准**：根据功能类型、规模和应用场景（本地工具？企业系统？实时应用？），重新评估每条建议的 P0/P1/P2 级别。批评家倾向于把一切标高、梦想家把增强项标 P1——你需要追问"在这个具体场景下，不修这条件真的会导致数据丢失或不可用吗？"\n' +
    '2. **捕捉遗漏**：审视三视角原始审查，有没有关键发现被整理者遗漏或降级了（比如验收标准自相矛盾、架构决策缺陷）？\n' +
    '3. **挑战过度建议**：哪些建议在给定项目规模下可以"不修"或"降级处理"? 标记理由。\n' +
    '4. **实质性过滤**：对保留的每条建议，逐一判断三个问题：\n' +
    '   (a) 能否在需求分析/概要设计阶段解决？若仅属于后续阶段（详细设计/实施/测试）才能验证的问题 → 直接剔除，不纳入最终输出。\n' +
    '   (b) 修了它是否会让 P2 详细设计 / P3 排期 / P4 实施做出不同的决策？若修与不修、下游产出完全相同 → 直接剔除，不纳入最终输出。\n' +
    '   (c) 能否用一句话说清具体改什么、改哪里？若模糊不可执行 → 改写或合并入其他建议，不单独成条。\n' +
    '   剔除的建议不在建议列表中，也不计入 P0/P1/P2 统计。\n' +
    '5. **输出修正后建议**：最终 ≤8 条，确保每条优先级与实际风险匹配。总体评估（1-2句）重新评估处理质量，适当校准。\n' +
    '6. 不要完全推翻整理者——只做微调和降噪。从整理者中选择真正重要的建议，调整优先级。\n' +
    '6. 用 Write 将审查结果写入 `' + docPathOut + '`（含总体评估/各视角要点/P0-P2 建议/元信息）。',
    { agentType: 'general-purpose', label: '校准师', phase: '审查与合成', schema: SYNTH_SCHEMA }
  )

  if (!calibrateResult) {
    log('## ⚠️ 校准师未返回结果')
    return
  }
  var finalResult = calibrateResult

  var p0Count = 0, p1Count = 0, totalSuggestions = 0
  var p0Items = [], p1Items = []
  if (finalResult.suggestions) {
    totalSuggestions = finalResult.suggestions.length
    for (var j = 0; j < totalSuggestions; j++) {
      var s = finalResult.suggestions[j]
      if (s.priority === 'P0') { p0Count++; p0Items.push(s) }
      else if (s.priority === 'P1') { p1Count++; p1Items.push(s) }
    }
  }

  log('\n---')
  log('## ✅ 文档审查完成')
  log('**文档**: `' + docPathOut + '`')
  log('**评估**: ' + (finalResult.summary || 'N/A'))
  log('**建议**: P0×' + p0Count + ' P1×' + p1Count + ' P2×' + (totalSuggestions - p0Count - p1Count))

  return {
    p0Count: p0Count,
    p1Count: p1Count,
    p2Count: totalSuggestions - p0Count - p1Count,
    totalSuggestions: totalSuggestions,
    p0Items: p0Items,
    p1Items: p1Items,
    summary: finalResult ? finalResult.summary : '',
    docPath: docPathOut
  }
}
