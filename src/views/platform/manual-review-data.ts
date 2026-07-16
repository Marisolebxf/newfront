export type ReviewStatus = '待处理' | '已完成'
export type ReviewPriority = 'P0' | 'P1' | 'P2'

export type ReviewBatch = {
  id: string
  module: string
  node: string
  domain: string
  total: number
  pending: number
  completed: number
  handler: string
  status: ReviewStatus
  severity: '高风险' | '中风险' | '低风险'
  severityReason: string
  updatedAt: string
  reason: string
  taskPath: string
  dataWindow: string
}

export type ReviewRecord = {
  id: string
  batch: string
  module: string
  node: string
  type: string
  domain: string
  objectType: string
  objectId: string
  object: string
  ruleId: string
  evidence: string
  score: string
  handler: string
  status: ReviewStatus
  updatedAt: string
  sourceResult: string
  suggestion: string
  sourceTable: string
  sourceRecordId: string
  decision?: string
  decisionNote?: string
  completedAt?: string
}

export const reviewBatches: ReviewBatch[] = [
  {
    id: 'UPD-20260714', module: '数据更新', node: '实体与关系异常处理', domain: '论文 / 人才 / 企业',
    total: 711, pending: 711, completed: 0, handler: '王审核 / 李质量', status: '待处理', severity: '高风险', severityReason: '公共流程异常已阻断，待修正后恢复', updatedAt: '07-14 10:42',
    reason: '实体冲突、关系证据不足和数据质量异常', taskPath: '/tasks?module=图谱构建&batch=UPD-20260714', dataWindow: '2026-07-13 02:00—2026-07-14 02:00',
  },
  {
    id: 'UPD-20260713', module: '数据更新', node: '实体与关系异常处理', domain: '专利 / 人才',
    total: 42, pending: 0, completed: 42, handler: '陈治理', status: '已完成', severity: '中风险', severityReason: '候选对象已隔离，其他任务继续执行', updatedAt: '07-12 19:16',
    reason: '候选实体置信度低于自动入库阈值，已完成人工确认', taskPath: '/tasks?module=图谱构建&batch=UPD-20260713', dataWindow: '2026-07-12 02:00—2026-07-13 02:00',
  },
]

export const reviewRecords: ReviewRecord[] = [
  {
    id: 'PI-20260714-0101', batch: 'UPD-20260714', module: '图谱构建', node: '大模型抽取', type: '模型批量输出异常', domain: '论文',
    objectType: '流程实例', objectId: 'LLM-BATCH-20260714-01', object: '大模型抽取批次', ruleId: 'LLM-SCHEMA-FAIL-001',
    evidence: '连续 326 条输出未通过 Schema 校验', score: '', handler: '张建图', status: '待处理', updatedAt: '07-14 10:24',
    sourceResult: '当前模型抽取节点已暂停', suggestion: '检查模型、Prompt 与 Schema 版本', sourceTable: '论文成果批次', sourceRecordId: 'BATCH-0714-LLM-01',
  },
  {
    id: 'PI-20260714-0102', batch: 'UPD-20260714', module: '图谱构建', node: 'Schema 映射', type: 'Schema 批量映射失败', domain: '企业',
    objectType: '流程实例', objectId: 'SCHEMA-BATCH-20260714-02', object: 'Schema 映射批次', ruleId: 'SCHEMA-MAP-FAIL-006',
    evidence: '3 个公共字段无法映射，影响 1,284 条任务', score: '', handler: '张建图', status: '待处理', updatedAt: '07-14 10:18',
    sourceResult: 'Schema 映射节点与下游已阻断', suggestion: '修正公共字段映射后重跑批次', sourceTable: '企业基本信息表', sourceRecordId: 'BATCH-0714-SCHEMA-02',
  },
  {
    id: 'PI-20260714-0103', batch: 'UPD-20260714', module: '数据处理', node: '清洗标准化', type: '公共字典配置异常', domain: '专利',
    objectType: '流程实例', objectId: 'DICT-BATCH-20260714-03', object: '专利状态标准化批次', ruleId: 'DICT-CONFIG-FAIL-003',
    evidence: '公共字典版本错误，批量字段被映射为未知', score: '', handler: '李质量', status: '待处理', updatedAt: '07-14 10:12',
    sourceResult: '清洗标准化节点已暂停', suggestion: '回滚公共字典版本后重跑', sourceTable: '专利基本信息表', sourceRecordId: 'BATCH-0714-DICT-03',
  },
  {
    id: 'PI-20260714-0104', batch: 'UPD-20260714', module: '图谱构建', node: '实体对齐', type: '单任务执行失败', domain: '人才',
    objectType: '候选实体', objectId: 'EXPERT_TMP_20566', object: '李晓峰 / Li Xiaofeng', ruleId: 'ALIGN-RUNTIME-004',
    evidence: '当前实体对齐任务执行超时，未生成候选结果', score: '', handler: '王审核', status: '待处理', updatedAt: '07-14 10:08',
    sourceResult: '当前任务未产生输出', suggestion: '检查超时日志并重跑当前任务', sourceTable: '专家基本信息表', sourceRecordId: 'EXPERT-20566',
  },
  {
    id: 'PI-20260714-0003', batch: 'UPD-20260714', module: '图谱构建', node: '关系校验', type: '低置信度', domain: '论文',
    objectType: '候选关系', objectId: 'e40', object: '数字抽象 → 矩阵分析', ruleId: 'REL-CONFIDENCE-003',
    evidence: '主题共现与两跳路径证据不足以自动入图', score: '0.72', handler: '王审核', status: '待处理', updatedAt: '07-14 10:06',
    sourceResult: '候选关系 e40 已隔离', suggestion: '核对关系语义与来源证据后重跑', sourceTable: '实体主题关联表', sourceRecordId: 'TOPIC-DIGITAL-040',
  },
  {
    id: 'PI-20260714-0004', batch: 'UPD-20260714', module: '图谱构建', node: 'Schema 实体分类', type: '实体类型错误', domain: '人才',
    objectType: '候选实体', objectId: 'EXPERT_TMP_20418', object: '张明远 / Zhang Mingyuan', ruleId: 'ALIGN-ENTITY-017',
    evidence: '源记录包含职称、任职机构和 ORCID，应归类为“专家”，系统却映射成了“人才”', score: '0.82', handler: '王审核', status: '待处理', updatedAt: '07-13 10:24',
    sourceResult: 'Person（人才）', suggestion: '从固定实体类型列表中改为 Expert（专家）',
    sourceTable: '专家基本信息表', sourceRecordId: 'EXPERT-20418',
  },
  {
    id: 'PI-20260714-0005', batch: 'UPD-20260714', module: '图谱构建', node: '关系证据校验', type: '关系证据不足', domain: '论文',
    objectType: '候选关系', objectId: 'REL_TMP_89321', object: '华南智能芯片 → 腾讯', ruleId: 'REL-EVIDENCE-009',
    evidence: '仅命中 1 个网页来源，未达到至少 2 个独立可信来源的入库条件', score: '0.74', handler: '陈治理', status: '待处理', updatedAt: '07-13 10:31',
    sourceResult: '候选关系 COOPERATE_WITH，来源数量 1', suggestion: '补充独立来源，或保持隔离并退回抽取节点',
    sourceTable: '企业合作记录表', sourceRecordId: 'COOP-89321-A',
  },
  {
    id: 'PI-20260714-0006', batch: 'UPD-20260714', module: '图谱构建', node: '属性校验', type: '属性冲突', domain: '人才',
    objectType: '候选属性', objectId: 'ATTR_TMP_77102', object: '张明远·任职机构', ruleId: 'ATTR-TIME-012',
    evidence: '模型结果与存量任职时间段重叠，且两个来源更新时间不一致', score: '0.78', handler: '王审核', status: '待处理', updatedAt: '07-13 10:28',
    sourceResult: '自动化研究所 2023-至今 / 华南智能芯片 2022-至今', suggestion: '核对最新任职来源并补充起止时间',
    sourceTable: '专家任职经历表', sourceRecordId: 'EMPLOYMENT-77102',
  },
  {
    id: 'PI-20260714-0007', batch: 'UPD-20260714', module: '数据处理', node: '唯一性校验', type: '唯一性冲突', domain: '论文',
    objectType: '源记录', objectId: 'paper_id=P202607130089', object: '重复论文成果记录', ruleId: 'DQ-UNIQUE-003',
    evidence: '同一 paper_id 对应 3 条来源记录，需要确认主记录及字段合并策略', score: '0.69', handler: '李质量', status: '待处理', updatedAt: '07-13 10:42',
    sourceResult: '3 条记录标题一致，DOI、作者单位完整度不同', suggestion: '保留 DOI 完整记录，合并作者单位与来源字段',
    sourceTable: '论文成果表', sourceRecordId: 'P202607130089',
  },
  {
    id: 'PI-20260714-0008', batch: 'UPD-20260714', module: '数据处理', node: '必填校验', type: '必填缺失', domain: '论文',
    objectType: '源记录', objectId: 'paper_id=P202607130104', object: '论文标题为空', ruleId: 'DQ-REQUIRED-001',
    evidence: '原始记录 title 为空，但摘要与 DOI 字段完整', score: '0.91', handler: '李质量', status: '待处理', updatedAt: '07-13 10:40',
    sourceResult: 'title=null，DOI=10.2026/kg.104', suggestion: '根据 DOI 来源补全标题后重新校验',
    sourceTable: '论文成果表', sourceRecordId: 'P202607130104',
  },
  {
    id: 'PI-20260714-0009', batch: 'UPD-20260714', module: '数据处理', node: '枚举校验', type: '枚举异常', domain: '论文',
    objectType: '源记录', objectId: 'paper_id=P202607130126', object: '来源类型无法映射', ruleId: 'DQ-ENUM-027',
    evidence: 'source_type=conference-online 未命中当前标准字典', score: '0.88', handler: '李质量', status: '待处理', updatedAt: '07-13 10:38',
    sourceResult: 'conference-online', suggestion: '映射为 conference，并保留原始值用于追溯',
    sourceTable: '论文成果表', sourceRecordId: 'P202607130126',
  },
  {
    id: 'PI-20260714-0010', batch: 'UPD-20260714', module: '数据处理', node: '必填校验', type: '必填缺失', domain: '论文',
    objectType: '源记录', objectId: 'paper_id=P202607130068', object: '论文标题缺失', ruleId: 'DQ-REQUIRED-001',
    evidence: '原始标题为空，但 DOI 可匹配到可信成果记录', score: '0.93', handler: '李质量', status: '已完成', updatedAt: '07-14 09:18',
    sourceResult: '已根据 DOI 补全《知识图谱增量构建方法研究》', suggestion: '修正后重新校验通过', sourceTable: '论文成果表', sourceRecordId: 'P202607130068',
    decision: '修正后重跑并通过', decisionNote: '根据 DOI 来源补全标题，从必填校验节点重跑后通过。', completedAt: '2026-07-14 09:18:42',
  },
  {
    id: 'PI-20260714-0011', batch: 'UPD-20260714', module: '图谱构建', node: '关系证据校验', type: '关系证据不足', domain: '企业',
    objectType: '候选关系', objectId: 'REL_TMP_89106', object: '深圳先进院 → 华南智能芯片', ruleId: 'REL-EVIDENCE-009',
    evidence: '自动抽取时只命中一条项目合作记录', score: '0.76', handler: '王审核', status: '已完成', updatedAt: '07-14 09:36',
    sourceResult: '补充第二条产学研合作公告，确认 COOPERATE_WITH 关系', suggestion: '证据补全后通过', sourceTable: '企业合作记录表', sourceRecordId: 'COOP-89106-B',
    decision: '修正后重跑并通过', decisionNote: '人工补充第二独立来源，从关系证据校验节点重跑后通过。', completedAt: '2026-07-14 09:36:15',
  },
  {
    id: 'PI-20260714-0012', batch: 'UPD-20260714', module: '图谱构建', node: '实体对齐', type: '实体冲突', domain: '人才',
    objectType: '候选实体', objectId: 'EXPERT_TMP_20372', object: '周启航 / Zhou Qihang', ruleId: 'ALIGN-ENTITY-017',
    evidence: '候选实体与存量实体同名，任职机构别名未归一', score: '0.81', handler: '陈治理', status: '已完成', updatedAt: '07-14 10:02',
    sourceResult: '已归一机构别名并合并至 Expert_20372', suggestion: '机构别名确认后通过', sourceTable: '专家基本信息表', sourceRecordId: 'EXPERT-20372',
    decision: '修正后重跑并通过', decisionNote: '确认两个机构名称为同一机构别名，从实体对齐节点重跑后完成合并。', completedAt: '2026-07-14 10:02:08',
  },
  {
    id: 'PI-20260714-0013', batch: 'UPD-20260714', module: '数据处理', node: '枚举校验', type: '枚举异常', domain: '专利',
    objectType: '源记录', objectId: 'patent_id=CN2026102764', object: '专利法律状态无法映射', ruleId: 'DQ-ENUM-031',
    evidence: '原始值 substantive-review 未命中中文标准字典', score: '0.89', handler: '李质量', status: '已完成', updatedAt: '07-14 10:21',
    sourceResult: '已映射为“实质审查”并保留原始值', suggestion: '字典映射后通过', sourceTable: '专利基本信息表', sourceRecordId: 'CN2026102764',
    decision: '修正后重跑并通过', decisionNote: '确认原始值语义，补充标准枚举映射并从枚举校验节点重跑。', completedAt: '2026-07-14 10:21:47',
  },
  {
    id: 'PI-20260713-0008', batch: 'UPD-20260713', module: '图谱构建', node: '实体对齐', type: '低置信度', domain: '专利',
    objectType: '候选实体', objectId: 'EXPERT_TMP_19882', object: '陈卓 / Chen Zhuo', ruleId: 'ALIGN-CONFIDENCE-003',
    evidence: '姓名和专利发明人一致，机构别名经人工确认后完成合并', score: '0.72', handler: '陈治理', status: '已完成', updatedAt: '07-12 19:16',
    sourceResult: '已合并至 Expert_88102', suggestion: '审核完成',
    sourceTable: '专家基本信息表', sourceRecordId: 'EXPERT-19882', decision: '修正后重跑并通过', decisionNote: '已核对机构别名与专利发明人信息，从实体对齐节点重跑并合并至 Expert_88102。', completedAt: '2026-07-13 19:16:00',
  },
]

export const getReviewBatch = (batchId: string) => reviewBatches.find((item) => item.id === batchId)
export const getReviewRecords = (batchId: string) => reviewRecords.filter((item) => item.batch === batchId)
export const getReviewRecord = (instanceId: string) => reviewRecords.find((item) => item.id === instanceId)

export const getReviewConfidence = (record: ReviewRecord) => {
  if (record.module === '数据处理') return { value: '—', label: '', source: '' }
  if (!record.score) return { value: '—', label: '', source: '' }
  const score = Number(record.score)
  if (score >= 0.9) return { value: '—', label: '', source: '' }
  return {
    value: record.score,
    label: '低于阈值',
    source: '',
  }
}

export const getReviewPriority = (record: ReviewRecord): { level: ReviewPriority; reason: string; policy: string; scope: string; strategy: string } => {
  if (['模型批量输出异常', 'Schema 批量映射失败', '公共字典配置异常'].includes(record.type)) {
    return { level: 'P0', reason: '影响公共处理流程', policy: 'REVIEW-PRIORITY-v1.1', scope: '高风险', strategy: '当前节点及下游已阻断' }
  }
  const common = { level: 'P1' as const, policy: 'REVIEW-PRIORITY-v1.1', scope: '中风险', strategy: '隔离当前任务，其他任务继续执行；修正后从当前节点重跑' }
  if (record.type === '实体冲突') return { ...common, reason: '单个候选实体合并冲突，当前结果已隔离' }
  if (record.type === '关系证据不足') return { ...common, reason: '单个候选关系证据不足，未进入生产图谱' }
  if (record.type === '属性冲突') return { ...common, reason: '单个对象的关键属性冲突，需人工确认' }
  if (record.type === '唯一性冲突') return { ...common, reason: '当前记录可能重复或丢失，但不影响其他任务' }
  if (record.type === '必填缺失') return { ...common, reason: '当前记录必填值缺失，补全后可重跑恢复' }
  if (record.type === '枚举异常') return { ...common, reason: '当前字段无法映射，原始值已保留' }
  return { ...common, reason: '当前异常结果已隔离，未进入下游' }
}
