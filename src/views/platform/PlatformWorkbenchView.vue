<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import KgDetailModal, { type DetailModalPayload } from '../../components/kg-detail-modal.vue'
import KgGraphCanvas from '../../components/kg-graph-canvas.vue'
import { useToast } from '../../composables/use-toast'
import {
  queryGraphPreset,
  relationCategoryMap,
  type GraphEdgeData,
  type GraphNodeData,
} from '../../data/graph-presets'

type PlatformTab = 'overview' | 'processing' | 'construction' | 'query' | 'service'
type ServiceField = {
  name: string
  type: string
  required?: boolean
  description: string
}
type ServiceModule = {
  key: string
  title: string
  endpoint: string
  method: 'POST'
  requestFields: ServiceField[]
  responseFields: ServiceField[]
  requestExample: Record<string, string | number | boolean | string[]>
  responseExample: { data: Record<string, unknown> }
  resultRows: Array<{ label: string; value: string }>
  evidence: string[]
}

const commonResponseFields: ServiceField[] = [
  { name: 'code', type: 'number', description: '服务状态码' },
  { name: 'message', type: 'string', description: '服务返回信息' },
  { name: 'data', type: 'object', description: '结构化业务结果、图谱节点关系和证据链' },
  { name: 'confidence', type: 'number', description: '综合置信度' },
  { name: 'evidence', type: 'array', description: '支撑本次结果的数据来源和证据' },
]

const modules: ServiceModule[] = [
  {
    key: 'expert-direct',
    title: '科技专家/人才直接关系',
    endpoint: '/api/v1/kg-service/expert-direct-relation',
    method: 'POST',
    requestFields: [
      { name: 'source_expert_id', type: 'string', required: true, description: '第一个专家唯一标识' },
      { name: 'target_expert_id', type: 'string', required: false, description: '第二个专家唯一标识' },
      { name: 'relation_scene', type: 'string', required: false, description: '交互场景筛选条件' },
      { name: 'start_time', type: 'string', required: false, description: '关系起始时间' },
    ],
    responseFields: commonResponseFields,
    requestExample: { source_expert_id: 'E10001', target_expert_id: 'E10002', relation_scene: '科研合作', start_time: '2020-01' },
    responseExample: { data: { relation_type: '论文合作', relation_count: 12, scenario: '科研合作', confidence: 0.94 } },
    resultRows: [{ label: '直接关系', value: '12' }, { label: '关系类型', value: '4' }, { label: '关联成果', value: '18' }, { label: '最高置信度', value: '0.94' }],
    evidence: ['共同发表论文 4 篇，作者列表和单位信息一致。', '共同参与项目 3 项，项目角色存在协作链路。', '关系发生时间、场景和成果均已结构化记录。'],
  },
  {
    key: 'node-indirect',
    title: '科技单节点间接关系',
    endpoint: '/api/v1/kg-service/node-indirect-relation',
    method: 'POST',
    requestFields: [
      { name: 'core_node_id', type: 'string', required: true, description: '核心专家或人才节点 ID' },
      { name: 'relation_types', type: 'array', required: false, description: '间接关系类型' },
      { name: 'path_depth', type: 'number', required: false, description: '路径分析深度' },
      { name: 'min_strength', type: 'number', required: false, description: '最小关联强度阈值' },
    ],
    responseFields: commonResponseFields,
    requestExample: { core_node_id: 'E10001', relation_types: ['学术关联', '机构关联'], path_depth: 2, min_strength: 0.65 },
    responseExample: { data: { indirect_nodes: 36, paths: 58, average_strength: 0.76 } },
    resultRows: [{ label: '间接节点', value: '36' }, { label: '路径数量', value: '58' }, { label: '关系类型', value: '4' }, { label: '平均强度', value: '0.76' }],
    evidence: ['路径：张明远 -> 李佳宁 -> 专家C。', '路径深度为 2，命中学术关联和机构关联。', '每条间接关系均返回传递路径和强度。'],
  },
  {
    key: 'two-point-achievement',
    title: '科技两点合作成果',
    endpoint: '/api/v1/kg-service/two-point-achievements',
    method: 'POST',
    requestFields: [
      { name: 'source_expert_id', type: 'string', required: true, description: '第一个专家唯一标识' },
      { name: 'target_expert_id', type: 'string', required: true, description: '第二个专家唯一标识' },
      { name: 'achievement_type', type: 'string', required: false, description: '成果类型' },
      { name: 'time_range', type: 'string', required: false, description: '成果时间范围' },
    ],
    responseFields: commonResponseFields,
    requestExample: { source_expert_id: 'E10001', target_expert_id: 'E10002', achievement_type: '论文/专利/项目', time_range: '2020-2026' },
    responseExample: { data: { papers: 8, patents: 3, projects: 2, contribution: '共同算法模型' } },
    resultRows: [{ label: '合作论文', value: '8' }, { label: '合作专利', value: '3' }, { label: '共同项目', value: '2' }, { label: '价值评分', value: '91' }],
    evidence: ['按论文、专利、项目分类统计合作成果。', '标注完成时间、所属领域和奖项评价。', '输出核心贡献和合作模式。'],
  },
  {
    key: 'expert-colleague',
    title: '科技专家同事关系',
    endpoint: '/api/v1/kg-service/expert-colleague-relation',
    method: 'POST',
    requestFields: [
      { name: 'expert_id', type: 'string', required: true, description: '专家唯一标识' },
      { name: 'organization', type: 'string', required: false, description: '任职机构筛选' },
      { name: 'department', type: 'string', required: false, description: '部门或团队筛选' },
      { name: 'overlap_period', type: 'string', required: false, description: '任职重叠时间' },
    ],
    responseFields: commonResponseFields,
    requestExample: { expert_id: 'E10001', organization: '中国科学院自动化研究所', department: '智能系统实验室', overlap_period: '2018-2022' },
    responseExample: { data: { colleagues: 18, teams: 4, overlap_years: 4, achievements: 6 } },
    resultRows: [{ label: '同事关系', value: '18' }, { label: '共同团队', value: '4' }, { label: '重叠年限', value: '4' }, { label: '期间成果', value: '6' }],
    evidence: ['任职时间存在重叠，机构层级匹配到同一实验室。', '标注共同工作内容和协作场景。', '关联同事期间产生的合作成果。'],
  },
  {
    key: 'expert-alumni',
    title: '科技专家校友关系',
    endpoint: '/api/v1/kg-service/expert-alumni-relation',
    method: 'POST',
    requestFields: [
      { name: 'expert_id', type: 'string', required: true, description: '专家唯一标识' },
      { name: 'school', type: 'string', required: false, description: '院校筛选条件' },
      { name: 'education_stage', type: 'string', required: false, description: '教育阶段筛选' },
      { name: 'major', type: 'string', required: false, description: '专业或院系筛选' },
    ],
    responseFields: commonResponseFields,
    requestExample: { expert_id: 'E10001', school: '北京大学', education_stage: '博士', major: '计算机科学' },
    responseExample: { data: { alumni: 26, dimensions: ['同校', '同院系', '同导师'], interactions: 9 } },
    resultRows: [{ label: '校友数量', value: '26' }, { label: '关系维度', value: '3' }, { label: '学术互动', value: '9' }, { label: '最高置信度', value: '0.89' }],
    evidence: ['基于教育经历匹配校友关系。', '细分同校、同院系、同导师等关联维度。', '关联后续学术交流与合作互动。'],
  },
  {
    key: 'paper-cooperation',
    title: '科技专家论文合作关系',
    endpoint: '/api/v1/kg-service/paper-cooperation-relation',
    method: 'POST',
    requestFields: [
      { name: 'expert_id', type: 'string', required: true, description: '专家唯一标识' },
      { name: 'coauthor_id', type: 'string', required: false, description: '合作者唯一标识' },
      { name: 'topic', type: 'string', required: false, description: '论文主题筛选' },
      { name: 'venue_level', type: 'string', required: false, description: '期刊或会议级别' },
    ],
    responseFields: commonResponseFields,
    requestExample: { expert_id: 'E10001', coauthor_id: 'E10002', topic: '人工智能', venue_level: 'A类会议' },
    responseExample: { data: { papers: 14, citations: 1260, stable_team: true, topics: ['人工智能', '先进计算'] } },
    resultRows: [{ label: '合作论文', value: '14' }, { label: '总被引', value: '1260' }, { label: '研究方向', value: '5' }, { label: '核心人员', value: '7' }],
    evidence: ['提取作者列表、作者单位、发表时间和论文主题。', '统计期刊会议级别和被引情况。', '识别长期稳定合作团队和核心合作人员。'],
  },
  {
    key: 'enterprise-relation',
    title: '重点关注科技企业关系',
    endpoint: '/api/v1/kg-service/key-enterprise-relation',
    method: 'POST',
    requestFields: [
      { name: 'expert_id', type: 'string', required: true, description: '专家唯一标识' },
      { name: 'enterprise_name', type: 'string', required: false, description: '企业名称筛选' },
      { name: 'role_type', type: 'string', required: false, description: '专家企业角色' },
      { name: 'industry', type: 'string', required: false, description: '企业行业方向' },
    ],
    responseFields: commonResponseFields,
    requestExample: { expert_id: 'E10001', enterprise_name: '华南智能芯片', role_type: '顾问/股东/合作方', industry: '集成电路' },
    responseExample: { data: { enterprises: 9, roles: 4, cooperation_fields: ['芯片设计', '智能制造'] } },
    resultRows: [{ label: '关联企业', value: '9' }, { label: '角色类型', value: '4' }, { label: '合作领域', value: '6' }, { label: '经营风险', value: '2' }],
    evidence: ['标注专家在企业中的角色、合作领域、合作时间和模式。', '关联企业行业地位、技术方向与经营状况。', '支持产业界资源对接分析。'],
  },
  {
    key: 'industry-chain-event',
    title: '科技产业链点TOP-N事件关系',
    endpoint: '/api/v1/kg-service/industry-node-top-events',
    method: 'POST',
    requestFields: [
      { name: 'chain_node_id', type: 'string', required: true, description: '产业链节点标识' },
      { name: 'top_n', type: 'number', required: false, description: '返回事件数量' },
      { name: 'event_type', type: 'string', required: false, description: '事件类型筛选' },
      { name: 'time_range', type: 'string', required: false, description: '事件时间范围' },
    ],
    responseFields: commonResponseFields,
    requestExample: { chain_node_id: 'IC-CHIP-DESIGN', top_n: 10, event_type: '投融资/政策/风险', time_range: '2025-2026' },
    responseExample: { data: { events: 10, experts: 18, enterprises: 24, risk_level: '中' } },
    resultRows: [{ label: 'TOP事件', value: '10' }, { label: '关联专家', value: '18' }, { label: '关联企业', value: '24' }, { label: '风险等级', value: '中' }],
    evidence: ['按影响力评估筛选产业链节点 TOP-N 事件。', '构建事件与专家、企业、人才的关联关系。', '分析产业链影响和后续发展趋势。'],
  },
  {
    key: 'industry-chain-panorama',
    title: '科技产业链全景图',
    endpoint: '/api/v1/kg-service/industry-chain-panorama',
    method: 'POST',
    requestFields: [
      { name: 'chain_id', type: 'string', required: true, description: '产业链标识' },
      { name: 'layer_depth', type: 'number', required: false, description: '层级展开深度' },
      { name: 'relation_filter', type: 'array', required: false, description: '关系筛选条件' },
      { name: 'include_events', type: 'boolean', required: false, description: '是否包含事件' },
    ],
    responseFields: commonResponseFields,
    requestExample: { chain_id: 'AI-COMPUTING', layer_depth: 3, relation_filter: ['技术', '企业', '专家'], include_events: true },
    responseExample: { data: { nodes: 186, relations: 420, key_technologies: 22, key_enterprises: 48 } },
    resultRows: [{ label: '产业节点', value: '186' }, { label: '链路关系', value: '420' }, { label: '关键技术', value: '22' }, { label: '重点企业', value: '48' }],
    evidence: ['整合产业链实体、关系、事件数据。', '展示核心节点、关联关系和数据流向。', '支持层级展开、关系筛选和动态更新。'],
  },
]

const props = defineProps<{
  initialTab?: PlatformTab
  initialServiceKey?: string
}>()

const activeTab = ref<PlatformTab>(props.initialTab ?? 'overview')
const activeServiceKey = ref(props.initialServiceKey ?? modules[0]?.key ?? '')
const activeBuildTab = ref<'entity' | 'relation' | 'property' | 'rule'>('entity')
const activeServiceMode = ref<'test' | 'api'>('test')
const selectedQueryType = ref('全部图谱')
const queryKeyword = ref('张明远')
const queryRelationFilter = ref('全部关系')
const queryEntityConfidence = ref('>= 0.75')
const queryRelationConfidence = ref('>= 0.75')
const queryApplied = ref(true)
const buildSearchKeyword = ref('')
const buildStatusFilter = ref('全部')
const buildDomainFilter = ref('全部数据域')
const buildSourceBatch = ref('全部批次')
const processingSourceFilter = ref('MySQL')
const processingStrategy = ref('每日 02:00 自动增量')
const processingMode = ref('定时增量')
const isActionLoading = ref(false)
const selectedGraphNodeId = ref<string | null>('core')
const selectedGraphEdgeId = ref<string | null>(null)
const queryDetailMode = ref<'summary' | 'entity' | 'relation'>('summary')
const detailModalOpen = ref(false)
const detailModalPayload = ref<DetailModalPayload | null>(null)
const traceModalOpen = ref(false)
const preserveBuildFilters = ref(false)
const buildAuditContext = ref<{ title: string; batch: string } | null>(null)

const { showToast } = useToast()

const activeService = computed(() => modules.find((item) => item.key === activeServiceKey.value) ?? modules[0])
const activeRequestJson = computed(() => JSON.stringify(activeService.value.requestExample, null, 2))
const activeResponseJson = computed(() => JSON.stringify({
  code: 0,
  message: 'success',
  data: activeService.value.responseExample.data ?? activeService.value.responseExample,
}, null, 2))
const activeRequestEntries = computed(() =>
  activeService.value.requestFields.map((field) => ({
    label: field.description,
    key: field.name,
    required: field.required ?? false,
    value: Array.isArray(activeService.value.requestExample[field.name])
      ? (activeService.value.requestExample[field.name] as string[]).join(', ')
      : String(activeService.value.requestExample[field.name] ?? '-'),
  })),
)
const serviceConsoleStats = computed(() => [
  { label: '服务标识', value: activeService.value.key },
  { label: '请求方法', value: activeService.value.method },
  { label: '接口路径', value: activeService.value.endpoint },
  { label: '参数数量', value: String(activeService.value.requestFields.length) },
])
const serviceCallLogs = computed(() => [
  { time: '10:30:12', level: 'SUCCESS', message: `已完成 ${activeService.value.title} 调用，返回 code=0。` },
  { time: '10:30:11', level: 'INFO', message: `请求参数已标准化，准备发送到 ${activeService.value.endpoint}。` },
  { time: '10:30:09', level: 'INFO', message: `命中服务路由 ${activeService.value.key}，开始装配请求体。` },
])

watch(
  () => props.initialTab,
  (tab) => {
    if (tab) {
      activeTab.value = tab
    }
  },
)

watch(
  () => props.initialServiceKey,
  (serviceKey) => {
    if (serviceKey) {
      activeServiceKey.value = serviceKey
    }
  },
)

const metrics = [
  { label: '实体总量', value: '1.28 亿', hint: '+18,426 今日新增', tone: 'blue' },
  { label: '关系总量', value: '6.42 亿', hint: '+92,318 今日新增', tone: 'green' },
  { label: '接入数据源', value: '42', hint: '论文 / 项目 / 企业 / 机构', tone: 'purple' },
  { label: '待人工审核', value: '326', hint: '低置信度与冲突数据', tone: 'orange' },
]

const mysqlSourceRows = [
  { name: 'expert_mysql', table: 'expert_profile', domain: '专家人才库', frequency: '每日 02:00', latest: '2026-07-09 02:04', status: '正常' },
  { name: 'paper_mysql', table: 'paper_record', domain: '论文成果库', frequency: '每日 02:00', latest: '2026-07-09 02:08', status: '正常' },
  { name: 'project_mysql', table: 'project_info', domain: '项目专利库', frequency: '每日 02:00', latest: '2026-07-09 02:11', status: '正常' },
  { name: 'enterprise_mysql', table: 'enterprise_profile', domain: '企业工商库', frequency: '每日 02:00', latest: '2026-07-08 23:40', status: '待检查' },
]

const dataProcessingSteps = [
  { name: '连接源库', status: '完成', desc: '校验 MySQL 连接、源表结构和增量游标' },
  { name: '检查更新', status: '完成', desc: '按 last_update_time 识别新增与变更记录' },
  { name: '清洗标准化', status: '完成', desc: '统一日期、枚举、空值、编码和字段命名' },
  { name: '质量校验', status: '运行中', desc: '检查必填、重复、异常值和来源批次' },
  { name: '写入标准表', status: '待生成', desc: '写入处理后的标准库表，供图谱构建使用' },
]

const processingTaskRows = [
  { batch: 'DP-20260709-0200', source: 'expert_mysql.expert_profile / paper_mysql.paper_record', domain: '专家人才库 / 论文成果库', type: '定时增量', time: '2026-07-09 02:00', input: '12,438', target: 'kg_stage.std_expert_profile, kg_stage.std_paper_record', status: '完成', progress: 100 },
  { batch: 'DP-20260708-1405', source: 'enterprise_mysql.enterprise_profile', domain: '企业工商库', type: '手动更新', time: '2026-07-08 14:05', input: '486', target: 'kg_stage.std_enterprise_profile', status: '完成', progress: 100 },
  { batch: 'DP-20260708-0200', source: 'project_mysql.project_info', domain: '项目专利库', type: '定时增量', time: '2026-07-08 02:00', input: '3,261', target: 'kg_stage.std_project_patent', status: '完成', progress: 100 },
  { batch: 'DP-20260709-URGENT', source: 'enterprise_mysql.enterprise_profile', domain: '企业工商库', type: '紧急更新', time: '待执行', input: '-', target: '待写入', status: '排队', progress: 12 },
]

const processingSourceOptions = ['MySQL']
const processingStrategyOptions = ['每日 02:00 自动增量', '每 6 小时检查更新', '仅手动触发', '紧急任务优先']
const processingModeOptions = ['定时增量', '手动更新', '紧急更新']

const filteredMysqlSourceRows = computed(() => mysqlSourceRows)

const filteredProcessingTaskRows = computed(() => processingTaskRows)

const buildPipelineSteps = [
  { name: '读取结构化数据', count: '12,604 条', status: '完成', desc: '从 kg_stage 标准表读取专家、论文、企业、项目等记录' },
  { name: '字段映射入 Schema', count: '7 类实体', status: '完成', desc: '字段映射到统一实体、属性和关系类型' },
  { name: '实体对齐与属性生成', count: '3,261 个实体 / 1,203 项属性', status: '处理中', desc: '基于 ID、名称、机构和成果证据做消歧与属性更新' },
  { name: '关系生成与证据校验', count: '8,942 条关系', status: '处理中', desc: '生成合作、任职、产业事件等候选关系并计算置信度' },
  { name: '结果入库与人工审核', count: '326 条待审', status: '待审核', desc: '高置信度自动入库，低置信度和冲突对象进入人工队列' },
]


const entityDistribution = [
  { label: '专家/人才', schema: 'Expert', count: '4,286 万', ratio: 34, tone: 'expert' },
  { label: '机构/企业', schema: 'Organization', count: '2,164 万', ratio: 17, tone: 'org' },
  { label: '论文成果', schema: 'Paper', count: '2,931 万', ratio: 23, tone: 'paper' },
  { label: '项目/专利', schema: 'Project / Patent', count: '1,438 万', ratio: 11, tone: 'project' },
  { label: '政策/事件', schema: 'Policy / Event', count: '812 万', ratio: 6, tone: 'event' },
  { label: '产业链节点', schema: 'IndustryChainNode', count: '641 万', ratio: 5, tone: 'chain' },
  { label: '产品/技术领域', schema: 'Product / ResearchField', count: '492 万', ratio: 4, tone: 'field' },
]

const relationDistribution = [
  { label: '发表/引用/成果', schema: 'PUBLISH / CITES / OUTPUT', count: '2.04 亿', ratio: 32 },
  { label: '任职/就读/作者单位', schema: 'WORKS_AT / STUDY_AT / AFFILIATED_WITH', count: '1.28 亿', ratio: 20 },
  { label: '项目/专利参与', schema: 'LEAD_PROJECT / INVENT_PATENT', count: '1.16 亿', ratio: 18 },
  { label: '企业/产品/事件', schema: 'HAS_PRODUCT / HAS_EVENT', count: '0.92 亿', ratio: 14 },
  { label: '产业链上下游', schema: 'PARENT_OF / UPSTREAM_DOWNSTREAM', count: '0.58 亿', ratio: 9 },
  { label: '业务推理关系', schema: 'DIRECT / INDIRECT / CO_AUTHOR', count: '0.44 亿', ratio: 7 },
]

const pipeline = [
  { name: '数据接入', count: '12,438 条', status: '完成', desc: '多源数据读取与批次登记' },
  { name: '清洗标准化', count: '11,982 条', status: '完成', desc: '字段归一与缺失校验' },
  { name: '实体关系抽取', count: '8,942 条', status: '运行中', desc: '规则与大模型联合抽取' },
  { name: '比对消歧', count: '1,203 条', status: '运行中', desc: '与存量图谱比对合并' },
  { name: '置信度审核', count: '326 条', status: '待审核', desc: '低置信度进入人工队列' },
  { name: '入库服务调用', count: '7,604 条', status: '排队', desc: '写入图库并开放查询' },
]

const taskRows = [
  { batch: 'KG-INC-20260706-01', source: '论文库增量', domain: '论文成果库', stage: '关系抽取', status: '运行中', progress: 72, entities: '3,261', relations: '8,942', properties: '1,203', autoStored: '10,638', conflicts: '41', quality: '0.88', next: '处理 41 条低置信度实体与关系' },
  { batch: 'KG-INC-20260706-02', source: '企业工商库', domain: '企业工商库', stage: '人工审核', status: '待审核', progress: 58, entities: '486', relations: '1,280', properties: '214', autoStored: '1,894', conflicts: '86', quality: '0.76', next: '确认工商字段冲突与企业合作证据' },
  { batch: 'KG-FULL-20260705-08', source: '专家人才库', domain: '专家人才库', stage: '图谱入库', status: '完成', progress: 100, entities: '18,420', relations: '62,117', properties: '6,410', autoStored: '86,947', conflicts: '0', quality: '0.94', next: '已完成入库，可进入查询服务' },
]
const selectedProcessingTaskBatch = ref(taskRows[0]?.batch ?? '')
const selectedProcessingTask = computed(() => (
  taskRows.find((row) => row.batch === selectedProcessingTaskBatch.value) ?? taskRows[0]
))

const entityRows = [
  { name: '张明远', type: '科技专家', domain: '论文成果库', match: '张明远 / Zhang Mingyuan', score: '0.92', action: '建议合并', status: '待审核', reason: '实体冲突', batch: 'KG-INC-20260706-01', auditTitle: '实体重复疑似冲突' },
  { name: '先进计算实验室', type: '机构团队', domain: '论文成果库', match: '先进计算与智能系统实验室', score: '0.87', action: '待人工确认', status: '待审核', reason: '实体冲突', batch: 'KG-INC-20260706-01', auditTitle: '实体重复疑似冲突' },
  { name: '华南智能芯片有限公司', type: '科技企业', domain: '企业工商库', match: '无高相似候选', score: '0.31', action: '创建新实体', status: '冲突数据', reason: '低置信度', batch: 'KG-INC-20260706-02', auditTitle: '新增实体待确认' },
]

const relationRows = [
  { source: '张明远', target: '李佳宁', relation: '论文合作', domain: '专家人才库', evidence: '共同发表论文 4 篇', confidence: '0.94', status: '自动入库', reason: '已通过', batch: 'KG-FULL-20260705-08', auditTitle: '论文合作自动通过' },
  { source: '华南智能芯片', target: '腾讯', relation: '企业合作', domain: '企业工商库', evidence: '单一网页来源，缺少工商交叉验证', confidence: '0.74', status: '待审核', reason: '证据不足', batch: 'KG-INC-20260706-01', auditTitle: '关系证据不足' },
  { source: '张明远', target: '王青', relation: '校友关系', domain: '专家人才库', evidence: '同校同院系，时间重叠 2 年', confidence: '0.78', status: '待审核', reason: '低置信度', batch: 'KG-INC-20260706-02', auditTitle: '校友关系低置信度' },
  { source: '李佳宁', target: '湾区智能制造联盟', relation: '产业事件参与', domain: '产业链事件库', evidence: 'TOP-N 事件报道与项目名单', confidence: '0.71', status: '待审核', reason: '证据不足', batch: 'KG-FULL-20260705-08', auditTitle: '产业链事件共现' },
]

const propertyRows = [
  { object: '张明远', property: '论文数量', domain: '论文成果库', oldValue: '128', newValue: '132', rule: '动态属性自动更新', status: '待审核', reason: '属性冲突', batch: 'KG-INC-20260706-02', auditTitle: '属性来源不一致' },
  { object: '李佳宁', property: '被引次数', domain: '论文成果库', oldValue: '3,421', newValue: '3,568', rule: '超过阈值自动入库', status: '自动入库', reason: '已通过', batch: 'KG-FULL-20260705-08', auditTitle: '高置信度属性更新' },
  { object: '某科技企业', property: '经营状态', domain: '企业工商库', oldValue: '存续', newValue: '注销风险', rule: '冲突数据进入审核', status: '冲突数据', reason: '属性冲突', batch: 'KG-INC-20260706-02', auditTitle: '属性来源不一致' },
]

const ruleRows = [
  { name: '专家姓名别名消歧规则', type: '实体消歧', method: '字段映射 + 相似度算法', threshold: '0.86', status: '启用' },
  { name: '论文作者合作关系抽取', type: '关系抽取', method: '作者列表位置 + 单位校验', threshold: '0.90', status: '启用' },
  { name: '企业关联角色识别', type: '属性/关系识别', method: '正则 + 页面字段定位 + 人工确认', threshold: '0.80', status: '调试中' },
]

const queryTypes = ['全部图谱', '专家人才子图', '科研成果子图', '机构企业子图', '产业链事件子图', '入库候选子图']
const relationFilters = ['全部关系', '直接关系', '间接关系', '同事', '校友', '论文合作', '企业关联', '产业事件']
const confidenceOptions = ['不限', '>= 0.60', '>= 0.75', '>= 0.85', '>= 0.90']
const queryScopeDescriptions: Record<string, string> = {
  全部图谱: '按统一 Schema 汇总专家、机构、成果、项目、企业、事件和产业链节点。',
  专家人才子图: '围绕 Expert / Person 节点展开教育、任职、成果、合作与社交关系。',
  科研成果子图: '围绕 Paper / Patent / Project / Achievement 展示成果产出和引用链路。',
  机构企业子图: '围绕 Organization / Product 展示任职、工商、产品、项目和专家关联。',
  产业链事件子图: '围绕 IndustryChainNode / Event 展示产业环节、TOP-N 事件和影响关系。',
  入库候选子图: '展示候选实体、候选关系、规则命中和人工审核状态。',
}

const entityLegendItems = [
  { label: '专家/人才', schema: 'Expert', tone: 'expert' },
  { label: '机构/企业', schema: 'Organization', tone: 'org' },
  { label: '论文成果', schema: 'Paper', tone: 'paper' },
  { label: '项目/专利', schema: 'Project / Patent', tone: 'project' },
  { label: '政策/事件', schema: 'Policy / Event', tone: 'event' },
  { label: '产业链节点', schema: 'IndustryChainNode', tone: 'chain' },
  { label: '产品/技术领域', schema: 'Product / ResearchField', tone: 'field' },
]

const graphEntitySummary = computed(() => {
  return Array.from(new Set(queryGraphPreset.nodes.map((node) => node.entityType))).join(' · ')
})

const queryGraphStats = computed(() => `${queryGraphPreset.nodes.length} 个节点 / ${queryGraphPreset.edges.length} 条关系`)

const selectedQueryScopeDescription = computed(() => (
  queryScopeDescriptions[selectedQueryType.value] ?? queryScopeDescriptions.全部图谱
))

const querySummary = computed(() => {
  if (!queryApplied.value) return '输入关键词后展示专家、企业、论文、机构、项目和事件的一张综合图'
  return `${selectedQueryType.value} / ${queryKeyword.value} / ${queryRelationFilter.value}`
})

const queryActiveCategories = computed(() => {
  if (!queryApplied.value || queryRelationFilter.value === '全部关系') return null
  return relationCategoryMap[queryRelationFilter.value] ?? [queryRelationFilter.value]
})

const selectedQueryNode = computed(() => {
  return (
    queryGraphPreset.nodes.find((node) => node.id === selectedGraphNodeId.value) ??
    queryGraphPreset.nodes[0]
  )
})

const selectedQueryEdge = computed(() => {
  return (
    queryGraphPreset.edges.find((edge) => edge.id === selectedGraphEdgeId.value) ??
    queryGraphPreset.edges[0]
  )
})

const selectedQueryEdgeNodes = computed(() => ({
  from: queryGraphPreset.nodes.find((node) => node.id === selectedQueryEdge.value.from),
  to: queryGraphPreset.nodes.find((node) => node.id === selectedQueryEdge.value.to),
}))

const selectedQueryRelationConfidence = computed(() => {
  const from = selectedQueryEdgeNodes.value.from
  const to = selectedQueryEdgeNodes.value.to
  if (!from || !to) return '0.00'
  const categoryWeight: Record<string, number> = {
    论文合作: 0.03,
    同事: 0.01,
    企业关联: -0.02,
    产业事件: -0.04,
    直接关系: 0.02,
    间接关系: -0.05,
  }
  const baseConfidence = (from.confidence + to.confidence) / 2
  const confidence = Math.min(0.99, Math.max(0.6, baseConfidence + (categoryWeight[selectedQueryEdge.value.category] ?? 0)))
  return confidence.toFixed(2)
})

const selectedQueryEdgeRows = computed(() => {
  const from = selectedQueryEdgeNodes.value.from
  const to = selectedQueryEdgeNodes.value.to
  if (!from || !to) return []
  return [
    ['源实体', `${from.label} / ${from.entityType}`] as const,
    ['目标实体', `${to.label} / ${to.entityType}`] as const,
    ['关系类型', selectedQueryEdge.value.label] as const,
    ['关系分类', selectedQueryEdge.value.category] as const,
    ['关系置信度', selectedQueryRelationConfidence.value] as const,
    ['来源说明', from.evidence[0] ?? to.evidence[0] ?? '来自图谱关系来源聚合'] as const,
  ]
})

const selectedQueryNodeRows = computed(() => [
  ['实体名称', selectedQueryNode.value.label] as const,
  ['实体类型', selectedQueryNode.value.entityType] as const,
  ['关系数', selectedQueryNode.value.relations] as const,
  ['实体置信度', selectedQueryNode.value.confidence.toFixed(2)] as const,
  ['判断依据', '实体对齐、名称消歧、类型归一、多源交叉校验'] as const,
  ['数据来源', '专家库 / 论文库 / 项目库 / 工商库'] as const,
  ['更新时间', '2026-07-06 10:30'] as const,
])

const buildBatchOptions = ['全部批次', 'KG-INC-20260706-01', 'KG-INC-20260706-02', 'KG-FULL-20260705-08']
const buildDomainOptions = ['全部数据域', '专家人才库', '论文成果库', '企业工商库', '产业链事件库']

function matchesBuildFilters(keywordFields: string[], status: string, batch: string, domain: string) {
  const keyword = buildSearchKeyword.value.trim()
  const keywordMatch = !keyword || keywordFields.some((field) => field.includes(keyword))
  const statusMatch = buildStatusFilter.value === '全部' || buildStatusFilter.value === status
  const domainMatch = buildDomainFilter.value === '全部数据域' || buildDomainFilter.value === domain
  const batchMatch = buildSourceBatch.value === '全部批次' || buildSourceBatch.value === batch
  return keywordMatch && statusMatch && domainMatch && batchMatch
}

const filteredEntityRows = computed(() => {
  return entityRows.filter((row) =>
    matchesBuildFilters([row.name, row.type, row.domain, row.match, row.reason, row.auditTitle], row.status, row.batch, row.domain),
  )
})

const filteredRelationRows = computed(() => {
  return relationRows.filter((row) =>
    matchesBuildFilters([row.source, row.target, row.relation, row.domain, row.reason, row.evidence, row.auditTitle], row.status, row.batch, row.domain),
  )
})

const filteredPropertyRows = computed(() => {
  return propertyRows.filter((row) =>
    matchesBuildFilters([row.object, row.property, row.domain, row.reason, row.rule, row.auditTitle], row.status, row.batch, row.domain),
  )
})

const buildResultCount = computed(() => {
  if (activeBuildTab.value === 'entity') return filteredEntityRows.value.length
  if (activeBuildTab.value === 'relation') return filteredRelationRows.value.length
  if (activeBuildTab.value === 'property') return filteredPropertyRows.value.length
  return ruleRows.length
})

const buildResultLabel = computed(() => {
  if (activeBuildTab.value === 'entity') return '实体'
  if (activeBuildTab.value === 'relation') return '关系'
  if (activeBuildTab.value === 'property') return '属性'
  return '规则'
})

async function runWithLoading(message: string, action?: () => void) {
  isActionLoading.value = true
  await new Promise((resolve) => window.setTimeout(resolve, 420))
  action?.()
  showToast(message)
  isActionLoading.value = false
}

function openNodeDetail(node: GraphNodeData) {
  selectedGraphNodeId.value = node.id
  selectedGraphEdgeId.value = null
  queryDetailMode.value = 'entity'
}

function openEdgeDetail(edge: GraphEdgeData) {
  selectedGraphEdgeId.value = edge.id
  selectedGraphNodeId.value = null
  queryDetailMode.value = 'relation'
}

function handleQuery() {
  void runWithLoading(`查询完成：${selectedQueryType.value} / ${queryKeyword.value}`, () => {
    queryApplied.value = true
    selectedGraphNodeId.value = 'core'
    selectedGraphEdgeId.value = null
    queryDetailMode.value = 'summary'
  })
}

function handleStartTask() {
  void runWithLoading(`已创建${processingMode.value}任务：${processingSourceFilter.value} / ${processingStrategy.value}`)
}

function handleExecuteService() {
  void runWithLoading(`${activeService.value.title} 调用成功，已刷新请求与响应结果`)
}

function handleCopyEndpoint() {
  void navigator.clipboard.writeText(`${activeService.value.method} ${activeService.value.endpoint}`)
  showToast('接口信息已复制到剪贴板', 'info')
}

function handleBuildSearch() {
  showToast(`已筛选 ${buildResultCount.value} 条${buildResultLabel.value}记录`, 'info')
}

function handleAuditAction(itemTitle: string, action: string) {
  showToast(`${itemTitle}：${action}已提交`)
}

function handleRowDetail(name: string) {
  detailModalPayload.value = {
    title: name,
    entityType: activeBuildTab.value === 'entity' ? '图谱对象' : '治理对象',
    relations: '待关联关系 2',
    confidence: '0.86',
    updatedAt: '2026-07-06 10:30',
    evidence: ['记录来自最新增量批次 KG-INC-20260706-01。', '审核通过后将写入图谱。'],
  }
  detailModalOpen.value = true
}

watch(activeServiceKey, () => {
  selectedGraphNodeId.value = 'core'
})

watch(activeBuildTab, () => {
  if (preserveBuildFilters.value) {
    preserveBuildFilters.value = false
    return
  }
  buildSearchKeyword.value = ''
  buildStatusFilter.value = '全部'
  buildDomainFilter.value = '全部数据域'
  buildSourceBatch.value = '全部批次'
  buildAuditContext.value = null
})

const pageMeta = computed(() => {
  const map: Record<PlatformTab, { title: string; subtitle: string; statLabel?: string; statValue?: string }> = {
    overview: {
      title: '亿级科技知识图谱平台',
      subtitle: '统一呈现接入、构建、治理、查询与业务服务运行态',
    },
    processing: {
      title: '数据处理与结构化输出',
      subtitle: '从 MySQL 源库定时同步数据，完成格式整理、清洗校验，并输出标准结构化数据集',
    },
    construction: {
      title: '图谱构建与治理',
      subtitle: '基于数据处理后的结构化结果，完成实体对齐、关系验证、属性更新、规则回写与图谱入库',
    },
    query: {
      title: '综合图谱查询',
      subtitle: '专家、企业、机构、论文、项目和事件在一张图中联动展示',
    },
    service: {
      title: activeService.value.title,
      subtitle: '按独立业务模块调用底层图谱能力，查看请求、响应与证据结果',
    },
  }
  return map[activeTab.value]
})

</script>

<template>
  <div class="platform-page">
    <header v-if="activeTab === 'overview'" class="platform-hero">
      <div class="platform-hero__main">
        <h1>{{ pageMeta.title }}</h1>
        <p class="platform-hero__subtitle">{{ pageMeta.subtitle }}</p>
      </div>
    </header>

    <header v-else class="platform-page-head">
      <div>
        <h1>{{ pageMeta.title }}</h1>
        <p>{{ pageMeta.subtitle }}</p>
      </div>
    </header>

    <main v-if="activeTab === 'overview'" class="platform-content platform-overview">
      <section class="platform-metrics" aria-label="平台指标">
        <article v-for="item in metrics" :key="item.label" :class="['platform-metric', `is-${item.tone}`]">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <em>{{ item.hint }}</em>
        </article>
      </section>

      <section class="kg-panel platform-pipeline-panel">
        <div class="kg-panel__header">
          <h2 class="kg-panel__title">数据到图谱处理闭环</h2>
          <span>近 24 小时</span>
        </div>
        <div class="platform-pipeline">
          <article v-for="item in pipeline" :key="item.name" class="platform-pipeline__step">
            <div>
              <strong>{{ item.name }}</strong>
              <span>{{ item.status }}</span>
            </div>
            <p>{{ item.desc }}</p>
            <em>{{ item.count }}</em>
          </article>
        </div>
      </section>

      <section class="platform-overview-grid">
        <div class="kg-panel platform-schema-panel">
          <div class="kg-panel__header">
            <h2 class="kg-panel__title">标准实体类型分布</h2>
            <span>统一 Schema</span>
          </div>
          <div class="platform-schema-list">
            <article v-for="item in entityDistribution" :key="item.schema" :class="`is-${item.tone}`">
              <i></i>
              <div>
                <strong>{{ item.label }}</strong>
                <span>{{ item.schema }}</span>
              </div>
              <em>{{ item.count }}</em>
              <b><span :style="{ width: `${item.ratio}%` }"></span></b>
            </article>
          </div>
        </div>

        <div class="kg-panel platform-relation-panel">
          <div class="kg-panel__header">
            <h2 class="kg-panel__title">标准关系类型分布</h2>
            <span>事实关系 + 推理关系</span>
          </div>
          <div class="platform-relation-list">
            <article v-for="item in relationDistribution" :key="item.schema">
              <div>
                <strong>{{ item.label }}</strong>
                <span>{{ item.schema }}</span>
              </div>
              <em>{{ item.count }}</em>
              <b><span :style="{ width: `${item.ratio}%` }"></span></b>
            </article>
          </div>
        </div>

      </section>
    </main>

    <main v-else-if="activeTab === 'processing'" class="platform-content platform-processing">
      <section class="kg-panel platform-source-panel">
        <div class="kg-panel__header">
          <h2 class="kg-panel__title">MySQL 数据源与更新策略</h2>
          <span>选择数据来源、源库表和更新策略后创建处理批次</span>
        </div>
        <div class="platform-processing-controls">
          <label>
            <span>数据来源</span>
            <select v-model="processingSourceFilter">
              <option v-for="item in processingSourceOptions" :key="item">{{ item }}</option>
            </select>
          </label>
          <label>
            <span>更新策略</span>
            <select v-model="processingStrategy">
              <option v-for="item in processingStrategyOptions" :key="item">{{ item }}</option>
            </select>
          </label>
          <label>
            <span>任务类型</span>
            <select v-model="processingMode">
              <option v-for="item in processingModeOptions" :key="item">{{ item }}</option>
            </select>
          </label>
          <button class="kg-button" type="button" :disabled="isActionLoading" @click="handleStartTask">立即更新</button>
        </div>

        <table class="platform-table">
          <thead>
            <tr><th>连接名</th><th>源表</th><th>业务域</th><th>检查频率</th><th>最近更新时间</th><th>状态</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredMysqlSourceRows" :key="`${row.name}-${row.table}`">
              <td>{{ row.name }}</td>
              <td>{{ row.table }}</td>
              <td>{{ row.domain }}</td>
              <td>{{ row.frequency }}</td>
              <td>{{ row.latest }}</td>
              <td><span class="platform-status">{{ row.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="kg-panel platform-cleaning-flow">
        <div class="kg-panel__header">
          <h2 class="kg-panel__title">数据处理流程</h2>
          <span>从源库同步到标准结构化库表</span>
        </div>
        <div class="platform-cleaning-steps">
          <article v-for="(item, index) in dataProcessingSteps" :key="item.name">
            <i>{{ index + 1 }}</i>
            <div>
              <strong>{{ item.name }}</strong>
              <p>{{ item.desc }}</p>
            </div>
            <span>{{ item.status }}</span>
          </article>
        </div>
      </section>

      <section class="kg-panel platform-task-list">
        <div class="kg-panel__header">
          <h2 class="kg-panel__title">数据处理任务队列</h2>
          <span>记录定时任务和手动更新任务</span>
        </div>
        <table class="platform-table platform-progress-table">
          <thead>
            <tr><th>处理批次</th><th>源库表</th><th>任务类型</th><th>触发时间</th><th>输入记录</th><th>进度</th><th>目标库表</th><th>状态</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredProcessingTaskRows" :key="row.batch">
              <td>{{ row.batch }}</td>
              <td>{{ row.source }}</td>
              <td>{{ row.type }}</td>
              <td>{{ row.time }}</td>
              <td>{{ row.input }}</td>
              <td>
                <div class="platform-progress-cell">
                  <b><i :style="{ width: `${row.progress}%` }" /></b>
                  <span>{{ row.progress }}%</span>
                </div>
              </td>
              <td>{{ row.target }}</td>
              <td><span class="platform-status">{{ row.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </section>
    </main>

    <main v-else-if="activeTab === 'construction'" class="platform-content platform-construction">
      <section class="kg-panel platform-build-pipeline">
        <div class="kg-panel__header">
          <h2 class="kg-panel__title">结构化数据建图过程</h2>
          <span>从标准表读取、Schema 映射、实体关系生成，到自动入库与人工审核</span>
        </div>
        <div class="platform-build-pipeline__body">
          <article v-for="(item, index) in buildPipelineSteps" :key="item.name">
            <i>{{ index + 1 }}</i>
            <div>
              <span>{{ item.name }}</span>
              <strong>{{ item.count }}</strong>
              <p>{{ item.desc }}</p>
            </div>
            <em>{{ item.status }}</em>
          </article>
        </div>
      </section>

      <section class="kg-panel platform-build-progress platform-build-progress--list">
        <div class="kg-panel__header">
          <h2 class="kg-panel__title">构建任务进度</h2>
          <span>展示结构化数据进入建图后的处理进度、候选规模和人工审核数量</span>
        </div>
        <table class="platform-table platform-progress-table">
          <thead>
            <tr><th>构建批次</th><th>数据域</th><th>当前阶段</th><th>实体</th><th>关系</th><th>属性</th><th>进度</th><th>待人工审核</th><th>状态</th></tr>
          </thead>
          <tbody>
            <tr
              v-for="row in taskRows"
              :key="row.batch"
              :class="{ 'is-active': row.batch === selectedProcessingTask.batch }"
              @click="selectedProcessingTaskBatch = row.batch"
            >
              <td>{{ row.batch }}</td>
              <td>{{ row.domain }}</td>
              <td>{{ row.stage }}</td>
              <td>{{ row.entities }}</td>
              <td>{{ row.relations }}</td>
              <td>{{ row.properties }}</td>
              <td>
                <div class="platform-progress-cell">
                  <b><i :style="{ width: `${row.progress}%` }" /></b>
                  <span>{{ row.progress }}%</span>
                </div>
              </td>
              <td>{{ row.conflicts }}</td>
              <td><span class="platform-status">{{ row.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="kg-panel platform-build">
        <div class="kg-panel__header">
          <h2 class="kg-panel__title">人工审核对象</h2>
          <div class="platform-segmented">
            <button type="button" :class="{ 'is-active': activeBuildTab === 'entity' }" @click="activeBuildTab = 'entity'">实体</button>
            <button type="button" :class="{ 'is-active': activeBuildTab === 'relation' }" @click="activeBuildTab = 'relation'">关系</button>
            <button type="button" :class="{ 'is-active': activeBuildTab === 'property' }" @click="activeBuildTab = 'property'">属性</button>
            <button type="button" :class="{ 'is-active': activeBuildTab === 'rule' }" @click="activeBuildTab = 'rule'">规则</button>
          </div>
        </div>

        <div class="platform-manual-toolbar">
          <span>筛选支持按对象名称、关系/属性关键词、数据域、处理状态和来源批次定位待处理对象。</span>
        </div>

        <div class="platform-manage-filter">
          <label>
            <span>名称 / 关键词</span>
            <input v-model="buildSearchKeyword" placeholder="张明远 / 企业合作 / 论文数量" />
          </label>
          <label>
            <span>数据域</span>
            <select v-model="buildDomainFilter">
              <option v-for="item in buildDomainOptions" :key="item">{{ item }}</option>
            </select>
          </label>
          <label>
            <span>数据状态</span>
            <select v-model="buildStatusFilter">
              <option>全部</option>
              <option>待审核</option>
              <option>自动入库</option>
              <option>冲突数据</option>
            </select>
          </label>
          <label>
            <span>来源批次</span>
            <select v-model="buildSourceBatch">
              <option v-for="item in buildBatchOptions" :key="item">{{ item }}</option>
            </select>
          </label>
          <button type="button" @click="handleBuildSearch">查询</button>
        </div>

        <div class="platform-build-context">
          <strong v-if="buildAuditContext">来自人工审核：{{ buildAuditContext.title }}</strong>
          <strong v-else>当前人工审核对象</strong>
          <span>
            {{ buildDomainFilter }}
            / {{ buildSourceBatch === '全部批次' ? '全部批次' : buildSourceBatch }}
            / {{ buildStatusFilter }}
            / {{ buildResultCount }} 条{{ buildResultLabel }}
          </span>
        </div>

        <table v-if="activeBuildTab === 'entity'" class="platform-table">
          <thead><tr><th>新识别实体</th><th>类型</th><th>数据域</th><th>候选匹配</th><th>相似度</th><th>审核原因</th><th>建议操作</th><th>人工操作</th></tr></thead>
          <tbody>
            <tr v-for="row in filteredEntityRows" :key="row.name">
              <td>{{ row.name }}</td><td>{{ row.type }}</td><td>{{ row.domain }}</td><td>{{ row.match }}</td><td>{{ row.score }}</td><td>{{ row.reason }}</td><td>{{ row.action }}</td>
              <td>
                <div class="platform-row-actions">
                  <button type="button" @click="handleRowDetail(row.name)">查看</button>
                  <button type="button" @click="showToast(`${row.name} 已进入编辑态`, 'info')">编辑</button>
                  <button type="button" @click="handleAuditAction(row.name, '合并')">合并</button>
                  <button type="button" @click="showToast(`${row.name} 已驳回`, 'warning')">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <table v-else-if="activeBuildTab === 'relation'" class="platform-table">
          <thead><tr><th>源实体</th><th>目标实体</th><th>关系类型</th><th>数据域</th><th>证据</th><th>置信度</th><th>审核原因</th><th>状态</th><th>人工操作</th></tr></thead>
          <tbody>
            <tr v-for="row in filteredRelationRows" :key="`${row.source}-${row.target}-${row.relation}`">
              <td>{{ row.source }}</td><td>{{ row.target }}</td><td>{{ row.relation }}</td><td>{{ row.domain }}</td><td>{{ row.evidence }}</td><td>{{ row.confidence }}</td><td>{{ row.reason }}</td><td>{{ row.status }}</td>
              <td>
                <div class="platform-row-actions">
                  <button type="button" @click="handleRowDetail(`${row.source}-${row.target}`)">查看</button>
                  <button type="button" @click="showToast('关系记录已进入编辑态', 'info')">编辑</button>
                  <button type="button" @click="handleAuditAction(`${row.source}-${row.target}`, '审核')">审核</button>
                  <button type="button" @click="showToast('关系记录已删除', 'warning')">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <table v-else-if="activeBuildTab === 'property'" class="platform-table">
          <thead><tr><th>对象</th><th>动态属性</th><th>数据域</th><th>原值</th><th>新值</th><th>审核原因</th><th>处理规则</th><th>人工操作</th></tr></thead>
          <tbody>
            <tr v-for="row in filteredPropertyRows" :key="`${row.object}-${row.property}`">
              <td>{{ row.object }}</td><td>{{ row.property }}</td><td>{{ row.domain }}</td><td>{{ row.oldValue }}</td><td>{{ row.newValue }}</td><td>{{ row.reason }}</td><td>{{ row.rule }}</td>
              <td>
                <div class="platform-row-actions">
                  <button type="button" @click="handleRowDetail(row.object)">查看</button>
                  <button type="button" @click="showToast('属性记录已进入编辑态', 'info')">编辑</button>
                  <button type="button" @click="showToast(`${row.property} 已回滚至 ${row.oldValue}`, 'info')">回滚</button>
                  <button type="button" @click="showToast('属性记录已删除', 'warning')">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <table v-else class="platform-table">
          <thead><tr><th>规则名称</th><th>规则类型</th><th>配置方式</th><th>阈值</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="row in ruleRows" :key="row.name">
              <td>{{ row.name }}</td><td>{{ row.type }}</td><td>{{ row.method }}</td><td>{{ row.threshold }}</td><td>{{ row.status }}</td>
              <td>
                <div class="platform-row-actions">
                  <button type="button" @click="handleRowDetail(row.name)">查看</button>
                  <button type="button" @click="showToast('规则配置已进入编辑态', 'info')">编辑</button>
                  <button type="button" @click="showToast(`${row.name} 已停用`, 'warning')">停用</button>
                  <button type="button" @click="showToast('规则已删除', 'warning')">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </main>

    <main v-else-if="activeTab === 'query'" class="platform-content platform-query">
      <section class="kg-panel platform-query-form">
        <div class="kg-panel__header">
          <h2 class="kg-panel__title">统一图查询入口</h2>
          <button class="kg-button" type="button" :disabled="isActionLoading" @click="handleQuery">查询</button>
        </div>
        <div class="platform-form-grid">
          <label>
            <span>图谱范围</span>
            <select v-model="selectedQueryType">
              <option v-for="item in queryTypes" :key="item">{{ item }}</option>
            </select>
          </label>
          <label>
            <span>关键词</span>
            <input v-model="queryKeyword" />
          </label>
          <label>
            <span>关系类型</span>
            <select v-model="queryRelationFilter">
              <option v-for="item in relationFilters" :key="item">{{ item }}</option>
            </select>
          </label>
          <label>
            <span>实体置信度</span>
            <select v-model="queryEntityConfidence">
              <option v-for="item in confidenceOptions" :key="`entity-${item}`">{{ item }}</option>
            </select>
          </label>
          <label>
            <span>关系置信度</span>
            <select v-model="queryRelationConfidence">
              <option v-for="item in confidenceOptions" :key="`relation-${item}`">{{ item }}</option>
            </select>
          </label>
        </div>
      </section>

      <section class="kg-panel platform-query-graph">
        <div class="kg-panel__header">
          <h2 class="kg-panel__title">综合图谱展示</h2>
          <span>{{ querySummary }} · {{ queryGraphStats }}</span>
        </div>
        <div class="platform-graph-legend" aria-label="实体类型图例">
          <span
            v-for="item in entityLegendItems"
            :key="item.schema"
            :class="['platform-graph-legend__item', `is-${item.tone}`]"
            :title="item.schema"
          >
            <i />
            {{ item.label }}
          </span>
        </div>
        <KgGraphCanvas
          :nodes="queryGraphPreset.nodes"
          :edges="queryGraphPreset.edges"
          :active-categories="queryActiveCategories"
          :selected-node-id="selectedGraphNodeId"
          :selected-edge-id="selectedGraphEdgeId"
          aria-label="图谱查询结果"
          @select-node="openNodeDetail"
          @select-edge="openEdgeDetail"
        />
      </section>

      <aside class="kg-panel platform-detail">
        <div class="kg-panel__header">
          <h2 class="kg-panel__title">
            {{ queryDetailMode === 'relation' ? '关系结构化结果' : queryDetailMode === 'entity' ? '实体结构化结果' : '查询结果摘要' }}
          </h2>
          <div class="platform-detail__tabs" aria-label="图谱详情类型">
            <button :class="{ 'is-active': queryDetailMode === 'summary' }" type="button" @click="queryDetailMode = 'summary'">摘要</button>
            <button :class="{ 'is-active': queryDetailMode === 'entity' }" type="button" @click="queryDetailMode = 'entity'">实体</button>
            <button :class="{ 'is-active': queryDetailMode === 'relation' }" type="button" @click="queryDetailMode = 'relation'">关系</button>
          </div>
        </div>
        <div v-if="queryDetailMode === 'summary'" class="platform-detail__body">
          <dl>
            <div><dt>图谱范围</dt><dd>{{ selectedQueryScopeDescription }}</dd></div>
            <div><dt>覆盖实体</dt><dd>{{ graphEntitySummary }}</dd></div>
            <div><dt>查询条件</dt><dd>{{ querySummary }}</dd></div>
            <div><dt>图谱规模</dt><dd>{{ queryGraphStats }}</dd></div>
            <div><dt>关系筛选</dt><dd>{{ queryRelationFilter }}</dd></div>
            <div><dt>实体置信度</dt><dd>{{ queryEntityConfidence }}</dd></div>
            <div><dt>关系置信度</dt><dd>{{ queryRelationConfidence }}</dd></div>
          </dl>
          <div class="platform-evidence">
            <strong>操作提示</strong>
            <ul>
              <li>点击实体节点查看实体属性、命中关系与来源信息。</li>
              <li>点击关系线查看两端实体之间的关系类型、置信度与来源说明。</li>
              <li>实体置信度衡量节点对齐、消歧和类型归一可信度；关系置信度衡量关系识别或推理可信度。</li>
            </ul>
          </div>
        </div>
        <div v-else-if="queryDetailMode === 'entity'" class="platform-detail__body">
          <dl>
            <div v-for="([label, value], index) in selectedQueryNodeRows" :key="`${label}-${index}`">
              <dt>{{ label }}</dt>
              <dd>{{ value }}</dd>
            </div>
          </dl>
          <div v-if="selectedQueryNode.evidence.length" class="platform-evidence">
            <strong>实体置信度说明</strong>
            <ul>
              <li>实体已经入图展示，置信度不是“是否存在”，而是该节点是否可靠合并到标准实体的评分。</li>
              <li v-for="(line, index) in selectedQueryNode.evidence.slice(0, 3)" :key="index">{{ line }}</li>
            </ul>
          </div>
        </div>
        <div v-else class="platform-detail__body">
          <dl>
            <div v-for="([label, value], index) in selectedQueryEdgeRows" :key="`${label}-${index}`">
              <dt>{{ label }}</dt>
              <dd>{{ value }}</dd>
            </div>
          </dl>
          <div class="platform-evidence">
            <strong>多关系展示策略</strong>
            <ul>
              <li>图谱画布保持一条关系线承载当前主关系，避免多条线重叠。</li>
              <li>完整关系、来源说明和置信度在右侧详情中展开。</li>
            </ul>
          </div>
        </div>
      </aside>
    </main>

    <main v-else :class="['platform-content', 'platform-service', { 'platform-service--api': activeServiceMode === 'api' }]">
      <section class="kg-panel platform-service-console">
        <div class="platform-service-console__top">
          <div class="platform-service-tabs">
            <button type="button" :class="{ 'is-active': activeServiceMode === 'test' }" @click="activeServiceMode = 'test'">
              服务调用
            </button>
            <button type="button" :class="{ 'is-active': activeServiceMode === 'api' }" @click="activeServiceMode = 'api'">
              接口文档
            </button>
          </div>
        </div>

        <div class="platform-service-console__body">
          <label>
            <span>当前模块</span>
            <input :value="activeService.title" readonly />
          </label>
          <template v-if="activeServiceMode === 'test'">
            <label v-for="field in activeService.requestFields.slice(0, 3)" :key="field.name">
              <span>{{ field.name }}</span>
              <input :value="activeService.requestExample[field.name] ?? ''" />
            </label>
          </template>
          <template v-else>
            <label>
            <span>接口路径</span>
            <input :value="activeService.endpoint" readonly />
            </label>
            <label>
            <span>请求方法</span>
            <input :value="activeService.method" readonly />
            </label>
          </template>
          <div class="platform-service-console__actions">
            <button v-if="activeServiceMode === 'test'" type="button" :disabled="isActionLoading" @click="handleExecuteService">
              执行调用
            </button>
            <button v-else type="button" @click="handleCopyEndpoint">复制接口</button>
          </div>
        </div>
      </section>

      <template v-if="activeServiceMode === 'test'">
        <section class="kg-panel platform-service-run">
          <div class="kg-panel__header">
            <h2 class="kg-panel__title">调用结果概览</h2>
            <span>{{ activeService.title }} / {{ activeService.method }}</span>
          </div>
          <div class="platform-service-run__body">
            <div class="platform-service-summary">
              <div v-for="item in serviceConsoleStats" :key="item.label">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
            <div class="platform-service-request">
              <strong>请求摘要</strong>
              <dl>
                <div v-for="item in activeRequestEntries" :key="item.key">
                  <dt>{{ item.label }}</dt>
                  <dd>
                    <span>{{ item.value }}</span>
                    <em v-if="item.required">必填</em>
                  </dd>
                </div>
              </dl>
            </div>
            <div class="platform-result-grid">
              <div v-for="row in activeService.resultRows" :key="row.label">
                <span>{{ row.label }}</span>
                <strong>{{ row.value }}</strong>
              </div>
            </div>
            <dl class="platform-service-info">
              <div><dt>命中服务</dt><dd>{{ activeService.title }}</dd></div>
              <div><dt>状态码</dt><dd>0 / success</dd></div>
              <div><dt>更新时间</dt><dd>2026-07-06 10:30</dd></div>
            </dl>
          </div>
        </section>

        <aside class="kg-panel platform-service-debug">
          <div class="kg-panel__header">
            <h2 class="kg-panel__title">请求与响应</h2>
          </div>
          <div class="platform-service-debug__body">
            <div class="platform-service-payload">
              <strong>请求体</strong>
              <pre>{{ activeRequestJson }}</pre>
            </div>
            <div class="platform-service-payload">
              <strong>响应体</strong>
              <pre>{{ activeResponseJson }}</pre>
            </div>
            <div class="platform-evidence">
              <strong>结果依据</strong>
              <ul>
                <li v-for="(line, index) in activeService.evidence.slice(0, 3)" :key="index">{{ line }}</li>
              </ul>
            </div>
            <div class="platform-service-log">
              <strong>调用日志</strong>
              <ul>
                <li v-for="item in serviceCallLogs" :key="`${item.time}-${item.message}`">
                  <span>{{ item.time }}</span>
                  <b>{{ item.level }}</b>
                  <p>{{ item.message }}</p>
                </li>
              </ul>
            </div>
          </div>
        </aside>
      </template>

      <template v-else>
        <section class="kg-panel platform-api-doc">
          <div class="kg-panel__header">
            <h2 class="kg-panel__title">开发者接口文档</h2>
            <span>{{ activeService.method }} {{ activeService.endpoint }}</span>
          </div>
          <div class="platform-api-doc__grid">
            <article>
              <h3>请求参数</h3>
              <table class="platform-table">
                <thead><tr><th>字段名</th><th>类型</th><th>必填</th><th>说明</th></tr></thead>
                <tbody>
                  <tr v-for="field in activeService.requestFields.slice(0, 6)" :key="field.name">
                    <td>{{ field.name }}</td>
                    <td>{{ field.type }}</td>
                    <td>{{ field.required ?? '否' }}</td>
                    <td>{{ field.description }}</td>
                  </tr>
                </tbody>
              </table>
            </article>
            <article>
              <h3>返回字段</h3>
              <table class="platform-table">
                <thead><tr><th>字段名</th><th>类型</th><th>说明</th></tr></thead>
                <tbody>
                  <tr v-for="field in activeService.responseFields" :key="field.name">
                    <td>{{ field.name }}</td>
                    <td>{{ field.type }}</td>
                    <td>{{ field.description }}</td>
                  </tr>
                </tbody>
              </table>
            </article>
          </div>
          <div class="platform-api-examples">
            <article>
              <h3>请求示例</h3>
              <pre>{{ activeRequestJson }}</pre>
            </article>
            <article>
              <h3>响应示例</h3>
              <pre>{{ activeResponseJson }}</pre>
            </article>
          </div>
          <div class="platform-code-sample">
            <div>
              <strong>代码示例</strong>
              <span>Python</span>
              <span>Node.js</span>
              <span>cURL</span>
            </div>
            <pre>import requests

url = "https://api.example.com{{ activeService.endpoint }}"
payload = {{ activeRequestJson }}
response = requests.post(url, json=payload)
print(response.json())</pre>
          </div>
        </section>
      </template>
    </main>

    <KgDetailModal
      :open="detailModalOpen"
      :payload="detailModalPayload"
      @close="detailModalOpen = false"
    />

    <div v-if="traceModalOpen" class="platform-modal-mask" @click.self="traceModalOpen = false">
      <section class="kg-panel platform-trace-modal" role="dialog" aria-modal="true">
        <div class="kg-panel__header">
          <h2 class="kg-panel__title">执行过程追踪</h2>
          <span>{{ selectedProcessingTask.batch }} / {{ selectedProcessingTask.stage }}</span>
          <button class="platform-modal-close" type="button" @click="traceModalOpen = false">关闭</button>
        </div>
        <div class="platform-timeline">
          <article v-for="item in pipeline" :key="item.name">
            <i></i>
            <div>
              <strong>{{ item.name }}</strong>
              <p>{{ item.desc }}</p>
            </div>
            <span>{{ item.count }}</span>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.platform-page {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 18px;
  height: 100%;
  min-width: 0;
  color: var(--text-primary);
  font-size: 17px;
}

.platform-hero {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 20px;
  min-height: 108px;
  padding: 26px 32px;
  border: 1px solid rgba(132, 178, 246, 0.86);
  border-radius: 12px;
  background:
    linear-gradient(135deg, rgba(216, 235, 255, 0.98) 0%, rgba(237, 247, 255, 0.98) 48%, rgba(211, 242, 255, 0.94) 100%),
    #e5f1ff;
  box-shadow:
    0 16px 34px rgba(48, 105, 194, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.96);
}

.platform-hero::before {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(22, 93, 255, 0.075) 1px, transparent 1px),
    linear-gradient(rgba(22, 93, 255, 0.075) 1px, transparent 1px);
  background-size: 34px 34px;
  mask-image: linear-gradient(90deg, rgba(0, 0, 0, 0.62), transparent 72%);
  pointer-events: none;
  content: "";
}

.platform-hero > * {
  position: relative;
}

.platform-hero h1 {
  margin: 0;
  color: #10264c;
  font-size: 34px;
  line-height: 44px;
  font-weight: 700;
}

.platform-hero__main {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.platform-hero__subtitle {
  margin: 0;
  color: #4b6288;
  font-size: 18px;
  line-height: 28px;
}

.platform-page-head {
  display: flex;
  align-items: center;
  min-height: 36px;
  padding: 0 2px 2px;
}

.platform-page-head h1 {
  margin: 0;
  color: #10264c;
  font-size: 22px;
  line-height: 30px;
  font-weight: 700;
}

.platform-page-head p {
  margin: 2px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 22px;
}

.platform-content {
  min-height: 0;
  overflow: auto;
  padding-bottom: 2px;
}

.platform-overview {
  display: grid;
  grid-template-rows: auto auto auto minmax(0, 1fr);
  gap: 16px;
}

.platform-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.platform-metric {
  position: relative;
  overflow: hidden;
  display: grid;
  gap: 6px;
  min-height: 124px;
  padding: 22px;
  border: 1px solid #bed8ff;
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(239, 247, 255, 0.94)),
    #f3f8ff;
  box-shadow: 0 8px 18px rgba(48, 105, 194, 0.1);
}

.platform-metric::after {
  position: absolute;
  right: 12px;
  bottom: 10px;
  width: 52px;
  height: 3px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.18;
  content: "";
}

.platform-metric span {
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 18px;
  line-height: 26px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.platform-metric strong {
  font-size: 40px;
  line-height: 48px;
  font-weight: 700;
}

.platform-metric em {
  overflow: hidden;
  color: var(--text-tertiary);
  font-size: 16px;
  font-style: normal;
  line-height: 22px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.platform-metric.is-blue strong { color: #165dff; }
.platform-metric.is-green strong { color: #00a870; }
.platform-metric.is-purple strong { color: #722ed1; }
.platform-metric.is-orange strong { color: #ff7d00; }

.platform-pipeline-panel .kg-panel__header span,
.platform-query-graph .kg-panel__header span,
.platform-service-graph .kg-panel__header span,
.platform-processing-flow .kg-panel__header span,
.platform-config .kg-panel__header span {
  color: var(--text-tertiary);
  font-size: 16px;
}

.platform-pipeline {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
  padding: 18px;
}

.platform-pipeline__step {
  position: relative;
  display: grid;
  gap: 8px;
  min-height: 118px;
  padding: 18px;
  border: 1px solid #e0ebfb;
  border-radius: 8px;
  background:
    linear-gradient(180deg, #ffffff, #f8fbff);
}

.platform-pipeline__step:not(:last-child)::after {
  position: absolute;
  top: 50%;
  right: -10px;
  width: 10px;
  height: 1px;
  background: #9bc2ff;
  content: "";
}

.platform-pipeline__step div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.platform-pipeline__step strong {
  font-size: 18px;
  line-height: 26px;
}

.platform-pipeline__step div span,
.platform-status {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  background: var(--primary-subtle);
  color: var(--primary);
  font-size: 15px;
  white-space: nowrap;
}

.platform-pipeline__step p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 16px;
  line-height: 24px;
}

.platform-pipeline__step em {
  color: var(--text-primary);
  font-size: 22px;
  font-style: normal;
  font-weight: 600;
}

.platform-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: auto;
}

.platform-table th,
.platform-table td {
  height: 42px;
  min-width: 110px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  color: var(--text-primary);
  font-size: 14px;
  line-height: 22px;
  text-align: left;
  overflow-wrap: anywhere;
}

.platform-table th {
  background: linear-gradient(180deg, #eef5ff, #f8fbff);
  color: var(--text-secondary);
  font-weight: 600;
}

.platform-table td {
  background: rgba(255, 255, 255, 0.54);
}

.platform-table tbody tr {
  transition: background 0.16s ease;
}

.platform-table tbody tr:hover {
  background: #f8fbff;
}

.platform-table tbody tr.platform-task-row--active td {
  background: #eef5ff;
}

.platform-icon-action {
  height: 28px;
  padding: 0 8px;
  border: 1px solid #bdd7ff;
  border-radius: var(--radius-sm);
  background: #fff;
  color: var(--primary);
  font-size: 13px;
  cursor: pointer;
}

.platform-icon-action:hover {
  background: var(--primary-subtle);
}

.platform-build-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
  padding: 12px 14px;
  border-top: 1px solid var(--border);
  background:
    linear-gradient(90deg, rgba(22, 93, 255, 0.06), rgba(20, 184, 166, 0.04)),
    #fbfdff;
  color: var(--text-tertiary);
  font-size: 12px;
  line-height: 18px;
}

.platform-processing {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  grid-template-rows: auto auto minmax(520px, 1fr);
  gap: 16px;
  padding: 14px;
  border: 1px solid rgba(191, 215, 250, 0.96);
  border-radius: 12px;
  background:
    linear-gradient(180deg, rgba(245, 250, 255, 0.98), rgba(232, 242, 255, 0.86)),
    #eef5ff;
  box-shadow:
    0 14px 30px rgba(48, 105, 194, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.92);
  align-content: start;
}

.platform-cleaning-input {
  grid-column: 1 / -1;
}

.platform-source-panel {
  grid-column: 1 / -1;
  min-height: 258px;
  overflow: auto;
}

.platform-processing-overview {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.platform-processing-overview article {
  position: relative;
  overflow: hidden;
  min-height: 118px;
  padding: 18px 20px;
  border: 1px solid #bdd7ff;
  border-radius: 10px;
  background:
    linear-gradient(135deg, rgba(22, 93, 255, 0.1), rgba(20, 184, 166, 0.05)),
    rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 22px rgba(48, 105, 194, 0.08);
}

.platform-processing-overview article::after {
  position: absolute;
  right: -20px;
  bottom: -26px;
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: rgba(22, 93, 255, 0.08);
  content: "";
}

.platform-processing-overview span {
  display: inline-flex;
  margin-bottom: 10px;
  padding: 2px 9px;
  border-radius: 999px;
  background: #eef5ff;
  color: var(--primary);
  font-size: 14px;
}

.platform-processing-overview strong {
  display: block;
  color: #10264c;
  font-size: 22px;
  line-height: 30px;
}

.platform-processing-overview p {
  max-width: 94%;
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 24px;
}

.platform-cleaning-editor {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 14px;
  padding: 16px;
}

.platform-cleaning-editor textarea {
  width: 100%;
  min-height: 172px;
  resize: vertical;
  padding: 14px 16px;
  border: 1px solid var(--border-strong);
  border-radius: 8px;
  background: #fff;
  color: var(--text-primary);
  font-family: inherit;
  font-size: 16px;
  line-height: 28px;
}

.platform-cleaning-options {
  display: grid;
  gap: 12px;
  align-content: start;
}

.platform-cleaning-options label {
  display: grid;
  gap: 6px;
}

.platform-cleaning-options span {
  color: var(--text-secondary);
  font-size: 14px;
}

.platform-cleaning-options input,
.platform-cleaning-options select {
  width: 100%;
  height: 36px;
  padding: 0 10px;
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  background: #fff;
  color: var(--text-primary);
  font-size: 14px;
}

.platform-processing-controls {
  display: grid;
  grid-template-columns: repeat(3, minmax(180px, 1fr)) auto;
  align-items: end;
  gap: 10px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  background: rgba(248, 251, 255, 0.72);
}

.platform-processing-controls label {
  display: grid;
  gap: 5px;
  min-width: 0;
}

.platform-processing-controls span {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 18px;
}

.platform-processing-controls select {
  width: 100%;
  height: 32px;
  padding: 0 9px;
  border: 1px solid #bdd7ff;
  border-radius: 6px;
  background: #fff;
  color: var(--text-primary);
  font-size: 13px;
}

.platform-cleaning-flow {
  grid-column: 1 / -1;
}

.platform-cleaning-steps {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 18px;
  padding: 16px;
}

.platform-cleaning-steps article {
  position: relative;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  grid-template-rows: auto auto;
  gap: 8px 12px;
  align-items: start;
  min-height: 118px;
  padding: 14px;
  border: 1px solid #dce9ff;
  border-radius: 8px;
  background: linear-gradient(145deg, #fff, #f6fbff);
}

.platform-cleaning-steps article:not(:last-child)::after {
  position: absolute;
  top: 50%;
  right: -17px;
  width: 16px;
  height: 2px;
  background: #9cc3ff;
  content: "";
}

.platform-cleaning-steps article:not(:last-child)::before {
  position: absolute;
  top: calc(50% - 4px);
  right: -18px;
  width: 0;
  height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-left: 7px solid #9cc3ff;
  content: "";
}

.platform-cleaning-steps i {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  font-size: 15px;
  font-style: normal;
  font-weight: 700;
  box-shadow: 0 0 0 5px rgba(22, 93, 255, 0.12);
}

.platform-cleaning-steps strong {
  font-size: 17px;
  line-height: 24px;
}

.platform-cleaning-steps p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 22px;
}

.platform-cleaning-steps span {
  grid-column: 2;
  justify-self: start;
  padding: 2px 8px;
  border-radius: 999px;
  background: #eef5ff;
  color: var(--primary);
  font-size: 13px;
  white-space: nowrap;
}

.platform-cleaning-result {
  grid-column: 1;
  min-height: 0;
  overflow: auto;
}

.platform-cleaning-relations {
  grid-column: 2;
  min-height: 0;
}

.platform-cleaning-relation-list {
  display: grid;
  gap: 12px;
  padding: 14px;
}

.platform-cleaning-relation-list article {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid #e2ebf8;
  border-radius: 8px;
  background: #fbfdff;
}

.platform-cleaning-relation-list article div {
  display: grid;
  gap: 4px;
}

.platform-cleaning-relation-list strong {
  color: var(--text-primary);
  font-size: 15px;
  line-height: 22px;
}

.platform-cleaning-relation-list span {
  color: var(--primary);
  font-size: 13px;
  line-height: 20px;
}

.platform-cleaning-relation-list em {
  color: var(--text-secondary);
  font-size: 13px;
  font-style: normal;
}

.platform-task-list {
  min-height: 0;
  overflow: auto;
}

.platform-processing > .platform-task-list {
  grid-column: 1 / -1;
  min-height: 520px;
}

.platform-processing > .platform-task-list .platform-table th,
.platform-processing > .platform-task-list .platform-table td {
  height: 56px;
  padding: 13px 18px;
  font-size: 16px;
  line-height: 24px;
}

.platform-processing > .platform-task-list .platform-table th {
  font-size: 15px;
}

.platform-processing > .platform-task-list .platform-status {
  min-height: 26px;
  padding: 0 11px;
  font-size: 15px;
}

.platform-review {
  display: grid;
  grid-template-rows: auto 1fr;
  align-content: start;
}

.platform-config {
  grid-column: 1 / -1;
}

.platform-discovery {
  grid-column: 1 / -1;
}

.platform-gates {
  grid-column: 1 / -1;
}

.platform-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
  padding: 12px 14px;
}

.platform-form-grid label {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.platform-form-grid span {
  color: var(--text-secondary);
  font-size: 14px;
}

.platform-form-grid input,
.platform-form-grid select {
  width: 100%;
  height: 32px;
  min-width: 0;
  padding: 0 10px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background: #fff;
  color: var(--text-primary);
  font-size: 14px;
}

.platform-timeline {
  display: grid;
  gap: 10px;
  padding: 14px;
  align-content: start;
}

.platform-timeline article {
  display: grid;
  grid-template-columns: 22px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border: 1px solid #e2ebf8;
  border-radius: 8px;
  background: #fbfdff;
}

.platform-timeline i {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--primary);
  box-shadow: 0 0 0 5px rgba(22, 93, 255, 0.12);
}

.platform-timeline strong,
.platform-timeline p {
  margin: 0;
}

.platform-timeline strong {
  font-size: 14px;
}

.platform-timeline p {
  color: var(--text-secondary);
  font-size: 13px;
}

.platform-timeline span {
  color: var(--primary);
  font-weight: 600;
}

.platform-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(16, 38, 76, 0.28);
}

.platform-trace-modal {
  width: min(760px, 100%);
  max-height: min(720px, calc(100vh - 48px));
  display: grid;
  grid-template-rows: auto 1fr;
  overflow: hidden;
}

.platform-modal-close {
  height: 28px;
  padding: 0 10px;
  border: 1px solid #bdd7ff;
  border-radius: var(--radius-sm);
  background: #fff;
  color: var(--primary);
  cursor: pointer;
}

.platform-review__body {
  display: grid;
  gap: 12px;
  padding: 14px;
  align-content: start;
}

.platform-review article {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid #e8edf6;
  border-radius: var(--radius-lg);
  background: #fbfdff;
}

.platform-review__item {
  cursor: pointer;
  transition: border-color 0.16s ease, background 0.16s ease;
}

.platform-review__item:hover,
.platform-review__item:focus-visible {
  outline: 0;
  border-color: #bdd7ff;
  background: #f3f8ff;
}

.platform-review strong,
.platform-review p {
  margin: 0;
}

.platform-review p {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 20px;
}

.platform-review div div {
  display: flex;
  gap: 8px;
}

.platform-review button {
  height: 28px;
  padding: 0 10px;
  border: 1px solid #bdd7ff;
  border-radius: var(--radius-sm);
  background: #fff;
  color: var(--primary);
  cursor: pointer;
}

.platform-discovery__grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  padding: 14px;
}

.platform-discovery__grid article {
  display: grid;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid #e2ebf8;
  border-radius: 8px;
  background: #fbfdff;
}

.platform-discovery__grid article div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.platform-discovery__grid span {
  color: var(--text-secondary);
  font-size: 13px;
}

.platform-discovery__grid strong {
  color: var(--primary);
  font-size: 20px;
  line-height: 24px;
}

.platform-discovery__grid p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 18px;
}

.platform-gates__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  padding: 12px 14px;
}

.platform-gates__grid article {
  display: grid;
  gap: 6px;
  padding: 12px;
  border: 1px solid #dfeafe;
  border-radius: 8px;
  background: linear-gradient(135deg, #f8fbff, #fff);
}

.platform-gates__grid span {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 20px;
}

.platform-gates__grid strong {
  color: var(--primary);
  font-size: 24px;
  line-height: 28px;
}

.platform-gates__grid p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 18px;
}

.platform-overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.platform-schema-list,
.platform-relation-list {
  display: grid;
  gap: 12px;
  padding: 20px;
}

.platform-schema-list article,
.platform-relation-list article {
  display: grid;
  grid-template-columns: 14px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  min-height: 56px;
  padding: 12px 14px;
  border: 1px solid #e2ebf8;
  border-radius: 6px;
  background: #fbfdff;
}

.platform-relation-list article {
  grid-template-columns: minmax(0, 1fr) auto;
}

.platform-schema-list i {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #4080ff;
  box-shadow: 0 0 0 4px rgba(64, 128, 255, 0.1);
}

.platform-schema-list article.is-expert i { background: #1e8ff3; box-shadow: 0 0 0 4px rgba(30, 143, 243, 0.1); }
.platform-schema-list article.is-org i { background: #48c914; box-shadow: 0 0 0 4px rgba(72, 201, 20, 0.1); }
.platform-schema-list article.is-paper i { background: #762bd7; box-shadow: 0 0 0 4px rgba(118, 43, 215, 0.1); }
.platform-schema-list article.is-project i { background: #ffad17; box-shadow: 0 0 0 4px rgba(255, 173, 23, 0.13); }
.platform-schema-list article.is-event i { background: #eb2aa3; box-shadow: 0 0 0 4px rgba(235, 42, 163, 0.1); }
.platform-schema-list article.is-chain i { background: #14b8a6; box-shadow: 0 0 0 4px rgba(20, 184, 166, 0.11); }
.platform-schema-list article.is-field i { background: #2f6bff; box-shadow: 0 0 0 4px rgba(47, 107, 255, 0.1); }

.platform-schema-list div,
.platform-relation-list div {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.platform-schema-list strong,
.platform-relation-list strong {
  overflow: hidden;
  font-size: 17px;
  line-height: 25px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.platform-schema-list span,
.platform-relation-list span {
  overflow: hidden;
  color: var(--text-tertiary);
  font-size: 14px;
  line-height: 20px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.platform-schema-list em,
.platform-relation-list em {
  color: var(--text-secondary);
  font-size: 15px;
  font-style: normal;
  white-space: nowrap;
}

.platform-schema-list b,
.platform-relation-list b {
  grid-column: 2 / -1;
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: #e8f1ff;
}

.platform-relation-list b {
  grid-column: 1 / -1;
}

.platform-schema-list b span,
.platform-relation-list b span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(180deg, #14b8a6, #165dff);
}

.platform-construction {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  grid-template-rows: auto auto minmax(620px, 1fr);
  gap: 16px;
  min-height: 0;
  align-items: stretch;
}

.platform-build-results {
  grid-column: 1 / -1;
}

.platform-build-progress {
  grid-column: 1 / -1;
  min-height: 236px;
  overflow: auto;
}

.platform-build-progress--list .platform-table tr {
  cursor: pointer;
}

.platform-build-progress--list .platform-table tr.is-active td {
  background: #eef5ff;
}

.platform-progress-cell {
  display: grid;
  grid-template-columns: minmax(80px, 1fr) auto;
  align-items: center;
  gap: 8px;
  min-width: 140px;
}

.platform-progress-cell b {
  overflow: hidden;
  height: 8px;
  border-radius: 999px;
  background: #dce9ff;
}

.platform-progress-cell i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #165dff, #22d3ee);
}

.platform-progress-cell span {
  color: var(--primary);
  font-size: 12px;
  font-weight: 600;
  line-height: 18px;
}

.platform-build-results__body,
.platform-audit-reasons {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  padding: 14px;
}

.platform-build-results__body {
  padding-bottom: 6px;
}

.platform-audit-reasons {
  padding-top: 6px;
}

.platform-build-results__body article,
.platform-audit-reasons article {
  position: relative;
  overflow: hidden;
  min-height: 86px;
  padding: 14px 16px;
  border: 1px solid #dce9ff;
  border-radius: 9px;
  background: linear-gradient(145deg, rgba(255,255,255,0.96), rgba(240,247,255,0.9));
}

.platform-build-results__body article::after {
  position: absolute;
  right: -18px;
  bottom: -18px;
  width: 58px;
  height: 58px;
  border-radius: 50%;
  background: rgba(22, 93, 255, 0.1);
  content: "";
}

.platform-build-results__body article.is-success::after {
  background: rgba(22, 163, 74, 0.12);
}

.platform-build-results__body article.is-warning::after {
  background: rgba(245, 158, 11, 0.16);
}

.platform-build-results__body span,
.platform-audit-reasons span {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 20px;
}

.platform-build-results__body strong,
.platform-audit-reasons strong {
  display: block;
  margin-top: 4px;
  color: var(--primary);
  font-size: 24px;
  line-height: 32px;
}

.platform-audit-reasons strong {
  color: var(--warning);
}

.platform-build-results__body p,
.platform-audit-reasons p {
  margin: 6px 0 0;
  color: var(--text-tertiary);
  font-size: 12px;
  line-height: 18px;
}

.platform-construction-kpis {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.platform-construction-kpis article {
  min-height: 102px;
  padding: 18px 20px;
  border: 1px solid #bdd7ff;
  border-radius: 10px;
  background:
    linear-gradient(135deg, rgba(255,255,255,0.96), rgba(238,247,255,0.9));
  box-shadow: 0 10px 22px rgba(48, 105, 194, 0.08);
}

.platform-construction-kpis span {
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 22px;
}

.platform-construction-kpis strong {
  display: block;
  margin-top: 8px;
  color: var(--primary);
  font-size: 32px;
  line-height: 40px;
}

.platform-construction-kpis p {
  margin: 6px 0 0;
  color: var(--text-tertiary);
  font-size: 14px;
  line-height: 20px;
}

.platform-build-pipeline {
  grid-column: 1 / -1;
}

.platform-build-pipeline__body {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
  padding: 16px;
}

.platform-build-pipeline__body article {
  position: relative;
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 10px;
  min-height: 126px;
  padding: 16px;
  border: 1px solid #dce9ff;
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(244, 249, 255, 0.9));
}

.platform-build-pipeline__body article:not(:last-child)::after {
  position: absolute;
  top: 50%;
  right: -15px;
  width: 14px;
  height: 2px;
  background: #9cc3ff;
  content: "";
}

.platform-build-pipeline__body i {
  display: inline-grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  font-size: 14px;
  font-style: normal;
  font-weight: 700;
}

.platform-build-pipeline__body span,
.platform-schema-mapping__body span {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 22px;
}

.platform-build-pipeline__body strong {
  display: block;
  margin-top: 6px;
  color: var(--primary);
  font-size: 24px;
  line-height: 32px;
}

.platform-build-pipeline__body em {
  grid-column: 2;
  justify-self: start;
  padding: 2px 8px;
  border-radius: 999px;
  background: #eef5ff;
  color: var(--primary);
  font-size: 12px;
  font-style: normal;
}

.platform-build-pipeline__body p,
.platform-schema-mapping__body p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 22px;
}

.platform-schema-mapping {
  min-height: 0;
}

.platform-schema-mapping__body {
  display: grid;
  gap: 10px;
  padding: 12px;
}

.platform-schema-mapping__body article {
  padding: 12px;
  border: 1px solid #dce9ff;
  border-radius: 8px;
  background: #fbfdff;
}

.platform-schema-mapping__body strong {
  display: block;
  margin-top: 6px;
  color: #10264c;
  font-size: 18px;
  line-height: 26px;
}

.platform-batch-list,
.platform-build-rules__body {
  display: grid;
  gap: 10px;
  padding: 12px;
}

.platform-batch-list article,
.platform-build-rules__body article {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid #dce9ff;
  border-radius: 8px;
  background: #fbfdff;
}

.platform-batch-list article.is-active {
  border-color: #84b2f6;
  background: #eef5ff;
}

.platform-batch-list article > button:first-child {
  justify-self: start;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--primary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.platform-batch-list article > span,
.platform-build-rules__body span {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 20px;
}

.platform-batch-list dl {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
}

.platform-batch-list dl div {
  display: grid;
  gap: 2px;
}

.platform-batch-list dt,
.platform-batch-list dd {
  margin: 0;
  font-size: 12px;
}

.platform-batch-list dt {
  color: var(--text-tertiary);
}

.platform-batch-list dd {
  color: var(--text-primary);
  font-weight: 600;
}

.platform-batch-list__next {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 18px;
}

.platform-build-rules__body strong {
  color: #10264c;
  font-size: 17px;
  line-height: 24px;
}

.platform-build-rules__body p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 20px;
}

.platform-build,
.platform-graph-summary {
  min-height: 0;
  height: 100%;
}

.platform-build {
  grid-column: 1;
  grid-row: 3;
  min-height: 620px;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.platform-graph-summary {
  display: grid;
  align-content: start;
  gap: 12px;
  padding-bottom: 14px;
}

.platform-graph-summary__hint {
  margin: -4px 14px 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 18px;
}

.platform-build-footer {
  margin-top: auto;
}

.platform-segmented {
  display: inline-flex;
  gap: 4px;
  padding: 3px;
  border: 1px solid rgba(125, 211, 252, 0.42);
  border-radius: 999px;
  background: rgba(232, 241, 255, 0.92);
}

.platform-segmented button {
  height: 28px;
  padding: 0 14px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}

.platform-segmented button.is-active {
  background: linear-gradient(135deg, #165dff, #22d3ee);
  color: #fff;
  box-shadow: 0 6px 16px rgba(22, 93, 255, 0.26);
}

.platform-manual-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(248,251,255,0.92), rgba(240,247,255,0.8));
}

.platform-manual-toolbar button {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  height: 32px;
  padding: 0 14px;
  border: 1px solid #bdd7ff;
  border-radius: 999px;
  background: #fff;
  color: var(--primary);
  font-size: 13px;
  line-height: 1;
  cursor: pointer;
}

.platform-manual-toolbar button:first-child {
  border-color: transparent;
  background: linear-gradient(135deg, #165dff, #0ea5e9);
  color: #fff;
  box-shadow: 0 8px 18px rgba(22, 93, 255, 0.22);
}

.platform-manual-toolbar span {
  min-width: 0;
  margin-left: 6px;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 20px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.platform-manage-filter {
  display: grid;
  grid-template-columns: minmax(260px, 1.4fr) minmax(160px, 0.8fr) minmax(160px, 0.8fr) minmax(200px, 1fr) 92px;
  align-items: end;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  background: rgba(248, 251, 255, 0.72);
}

.platform-manage-filter label {
  display: grid;
  gap: 5px;
  min-width: 0;
}

.platform-manage-filter span {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 18px;
}

.platform-manage-filter input,
.platform-manage-filter select {
  width: 100%;
  height: 30px;
  min-width: 0;
  padding: 0 9px;
  border: 1px solid #bdd7ff;
  border-radius: 6px;
  background: #fff;
  color: var(--text-primary);
  font-size: 13px;
}

.platform-manage-filter button {
  height: 30px;
  padding: 0 16px;
  border: 0;
  border-radius: 6px;
  background: var(--primary);
  color: #fff;
  font-size: 13px;
  cursor: pointer;
}

.platform-build-context {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 20px;
}

.platform-build-context strong {
  color: var(--text-primary);
  font-size: 14px;
}

.platform-row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.platform-row-actions button {
  height: 24px;
  padding: 0 8px;
  border: 1px solid #bdd7ff;
  border-radius: 5px;
  background: #fff;
  color: var(--primary);
  font-size: 12px;
  line-height: 22px;
  cursor: pointer;
}

.platform-row-actions button:last-child {
  border-color: #ffd6d6;
  color: #d92d20;
  background: #fffafa;
}

.platform-impact {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 14px;
  padding-bottom: 0;
}

.platform-impact div {
  position: relative;
  overflow: hidden;
  display: grid;
  gap: 6px;
  min-height: 74px;
  padding: 10px 12px;
  border: 1px solid rgba(191, 219, 254, 0.9);
  border-radius: 8px;
  background: linear-gradient(145deg, rgba(255,255,255,0.92), rgba(236,246,255,0.88));
}

.platform-impact div::after {
  position: absolute;
  right: -14px;
  bottom: -20px;
  width: 58px;
  height: 58px;
  border-radius: 50%;
  background: rgba(22, 93, 255, 0.08);
  content: "";
}

.platform-impact span {
  color: var(--text-secondary);
  font-size: 13px;
}

.platform-impact strong {
  font-size: 24px;
  color: var(--primary);
}

.platform-rule-note {
  margin: 0 14px;
  padding: 12px;
  border: 1px solid #ffe0b2;
  border-radius: 8px;
  background: linear-gradient(135deg, #fff8ed, #fffdf8);
}

.platform-rule-note p {
  margin: 8px 0 0;
  color: #7a4a00;
  font-size: 13px;
  line-height: 20px;
}

.platform-rule-note--manual {
  border-color: #cce5d8;
  background: linear-gradient(135deg, #edfff7, #f8fffb);
}

.platform-rule-note--manual p {
  color: #12643b;
}

.platform-governance-flow {
  margin: 0 14px;
  padding: 12px;
  border: 1px solid #dce9ff;
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(247,251,255,0.88));
}

.platform-governance-flow > strong {
  display: block;
  margin-bottom: 10px;
  color: var(--text-primary);
  font-size: 14px;
}

.platform-governance-flow ol {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.platform-governance-flow li {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: 8px;
  align-items: start;
}

.platform-governance-flow li span {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #e8f1ff;
  color: var(--primary);
  font-size: 11px;
  font-weight: 600;
}

.platform-governance-flow li p {
  margin: 2px 0 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 18px;
}

.platform-query,
.platform-service {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: 12px;
}

.platform-service {
  grid-template-columns: minmax(0, 1fr) 360px;
  grid-template-rows: auto minmax(0, 1fr);
  align-items: stretch;
}

.platform-service--api {
  grid-template-columns: minmax(0, 1fr);
}

.platform-query-form,
.platform-service-console {
  grid-column: 1 / -1;
}

.platform-query {
  grid-template-columns: minmax(0, 1fr) 340px;
  grid-template-rows: auto minmax(460px, 1fr);
  align-items: stretch;
}

.platform-query-graph {
  grid-column: 1;
  grid-row: 2;
  min-height: 480px;
  overflow: hidden;
}

.platform-query-graph :deep(.kg-graph-viewport) {
  height: calc(100% - 100px);
}

.platform-graph-legend {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-start;
  gap: 8px 14px;
  min-height: 46px;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(191, 215, 250, 0.96);
  background: rgba(248, 252, 255, 0.86);
}

.platform-graph-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 20px;
  white-space: nowrap;
}

.platform-graph-legend__item i {
  display: inline-block;
  width: 13px;
  height: 13px;
  border: 2px solid #fff;
  border-radius: 50%;
  box-shadow: 0 1px 4px rgba(53, 77, 112, 0.16);
}

.platform-graph-legend__item.is-expert i { background: #1e8ff3; }
.platform-graph-legend__item.is-org i { background: #48c914; }
.platform-graph-legend__item.is-paper i { background: #762bd7; }
.platform-graph-legend__item.is-project i { background: #ffad17; }
.platform-graph-legend__item.is-event i { background: #eb2aa3; }
.platform-graph-legend__item.is-chain i { background: #14b8a6; }
.platform-graph-legend__item.is-field i { background: #2f6bff; }

.platform-query > .platform-detail {
  grid-column: 2;
  grid-row: 2;
  overflow: auto;
}

.platform-service-run,
.platform-detail,
.platform-service-debug,
.platform-api-doc {
  min-height: 0;
}

.platform-service-console {
  overflow: hidden;
}

.platform-service-console__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 42px;
  padding: 0 16px;
  border-bottom: 1px solid rgba(191, 215, 250, 0.96);
  background:
    linear-gradient(90deg, rgba(22, 93, 255, 0.08), transparent 48%),
    rgba(248, 252, 255, 0.9);
}

.platform-service-tabs {
  display: inline-flex;
  align-items: center;
  gap: 18px;
}

.platform-service-tabs button {
  position: relative;
  height: 42px;
  border: 0;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
}

.platform-service-tabs button.is-active {
  color: var(--primary);
  font-weight: 600;
}

.platform-service-tabs button.is-active::after {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  height: 2px;
  border-radius: 999px;
  background: var(--primary);
  content: "";
}

.platform-service-console__body {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) repeat(3, minmax(170px, 0.8fr)) auto;
  align-items: end;
  gap: 12px;
  padding: 12px 16px 14px;
}

.platform-service--api .platform-service-console__body {
  grid-template-columns: minmax(260px, 0.9fr) minmax(360px, 1.4fr) 140px auto;
}

.platform-service-console__body label {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.platform-service-console__body label span {
  color: var(--text-secondary);
  font-size: 12px;
}

.platform-service-console__body input,
.platform-service-console__body select {
  width: 100%;
  height: 32px;
  min-width: 0;
  padding: 0 10px;
  border: 1px solid #bdd7ff;
  border-radius: 6px;
  background: #fff;
  color: var(--text-primary);
  font-size: 13px;
}

.platform-service-console__actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.platform-service-console__actions button {
  height: 32px;
  padding: 0 14px;
  border: 1px solid #bdd7ff;
  border-radius: 6px;
  background: #fff;
  color: var(--primary);
  font-size: 13px;
  cursor: pointer;
}

.platform-service-console__actions button:last-child {
  border-color: transparent;
  background: linear-gradient(135deg, #165dff, #0ea5e9);
  color: #fff;
  box-shadow: 0 8px 18px rgba(22, 93, 255, 0.2);
}

.platform-svg {
  width: 100%;
  height: calc(100% - 45px);
  min-height: 340px;
  display: block;
  background:
    linear-gradient(#e8f1ff 1px, transparent 1px),
    linear-gradient(90deg, #e8f1ff 1px, transparent 1px),
    linear-gradient(135deg, rgba(22, 93, 255, 0.06), rgba(20, 184, 166, 0.04)),
    #fbfdff;
  background-size: 28px 28px, 28px 28px, auto, auto;
}

.platform-service-run {
  overflow: auto;
}

.platform-service-run__body,
.platform-service-debug__body {
  display: grid;
  gap: 12px;
  padding: 14px;
}

.platform-service-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.platform-service-summary div {
  display: grid;
  gap: 6px;
  min-height: 72px;
  padding: 10px 12px;
  border: 1px solid #dce9ff;
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(244, 249, 255, 0.92));
}

.platform-service-summary span {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 18px;
}

.platform-service-summary strong {
  color: var(--text-primary);
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 16px;
  line-height: 22px;
}

.platform-service-request {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid #dce9ff;
  border-radius: 8px;
  background: #fbfdff;
}

.platform-service-request strong,
.platform-service-payload strong,
.platform-service-log strong {
  color: var(--text-primary);
  font-size: 13px;
}

.platform-service-request dl {
  display: grid;
  gap: 8px;
  margin: 0;
}

.platform-service-request dl div {
  display: grid;
  grid-template-columns: 160px minmax(0, 1fr);
  gap: 10px;
  align-items: start;
  padding: 8px 0;
  border-bottom: 1px solid #eef3fb;
}

.platform-service-request dl div:last-child {
  border-bottom: 0;
}

.platform-service-request dt,
.platform-service-request dd {
  margin: 0;
  min-width: 0;
  font-size: 12px;
  line-height: 18px;
}

.platform-service-request dt {
  color: var(--text-secondary);
}

.platform-service-request dd {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
}

.platform-service-request dd em {
  padding: 1px 6px;
  border-radius: 999px;
  background: #eef5ff;
  color: var(--primary);
  font-size: 11px;
  font-style: normal;
  line-height: 18px;
}

.platform-node circle {
  fill: #21c1c3;
  stroke: #fff;
  stroke-width: 1.8;
  filter: drop-shadow(0 3px 6px rgba(53, 77, 112, 0.12));
}

.platform-node--main circle {
  fill: #1e8ff3;
  stroke: #fff;
}

.platform-node.is-expert circle { fill: #20bfc2; }
.platform-node.is-org circle { fill: #48c914; }
.platform-node.is-company circle { fill: #ffad17; }
.platform-node.is-paper circle { fill: #762bd7; }
.platform-node.is-topic circle { fill: #1f8ff1; }
.platform-node.is-project circle { fill: #eb2aa3; }
.platform-node.is-event circle { fill: var(--graph-gold, #f59e0b); }

.platform-node text {
  fill: #4f5d70;
  font-size: 12px;
  font-weight: 500;
  text-anchor: middle;
  dominant-baseline: hanging;
  transform: translateY(18px);
  paint-order: stroke;
  stroke: rgba(255, 255, 255, 0.9);
  stroke-width: 3px;
  stroke-linejoin: round;
}

.platform-node--main text {
  fill: #fff;
  font-size: 15px;
  font-weight: 600;
  dominant-baseline: middle;
  transform: none;
  stroke: transparent;
}

.platform-network-lines line,
.platform-network-line {
  stroke: #b8c1ce;
  stroke-width: 1.4;
  marker-end: url(#platform-arrow);
}

.platform-network-lines--service line {
  marker-end: url(#service-arrow);
}

.platform-network-line.is-primary { stroke: #4080ff; stroke-width: 1.8; }
.platform-network-line.is-green { stroke: #00b42a; stroke-width: 1.8; }
.platform-network-line.is-orange { stroke: #ff7d00; stroke-width: 1.8; }
.platform-network-line.is-purple { stroke: #722ed1; stroke-width: 1.8; }

.platform-detail__body {
  display: grid;
  gap: 14px;
  padding: 14px;
}

.platform-detail__tabs {
  display: inline-flex;
  flex: 0 0 auto;
  gap: 0;
  padding: 2px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.66);
}

.platform-detail__tabs button {
  height: 28px;
  padding: 0 10px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
}

.platform-detail__tabs button.is-active {
  background: var(--surface);
  color: var(--primary);
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(22, 93, 255, 0.12);
}

.platform-detail dl {
  display: grid;
  gap: 8px;
  margin: 0;
}

.platform-detail dl div {
  display: grid;
  grid-template-columns: 98px minmax(0, 1fr);
  gap: 10px;
  padding: 9px 10px;
  border-radius: 6px;
  background: #f7faff;
}

.platform-detail dt,
.platform-detail dd {
  margin: 0;
  font-size: 14px;
  line-height: 20px;
}

.platform-detail dt {
  color: var(--text-secondary);
}

.platform-detail ul,
.platform-evidence ul {
  display: grid;
  gap: 8px;
  margin: 0;
  padding-left: 18px;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 20px;
}

.platform-result-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 14px;
}

.platform-result-grid div {
  display: grid;
  gap: 6px;
  min-height: 68px;
  padding: 10px 12px;
  border: 1px solid #e2ebf8;
  border-radius: 8px;
  background: #fbfdff;
}

.platform-result-grid span {
  color: var(--text-secondary);
  font-size: 13px;
}

.platform-result-grid strong {
  color: var(--primary);
  font-size: 22px;
}

.platform-evidence {
  display: grid;
  gap: 8px;
  margin: 0 14px 14px;
  padding: 12px;
  border: 1px solid #e2ebf8;
  border-radius: 8px;
  background: #fff;
}

.platform-evidence strong {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.platform-service-info {
  display: grid;
  gap: 8px;
  margin: 0 14px 14px;
  padding: 12px;
  border: 1px solid #dce9ff;
  border-radius: 8px;
  background: #f8fbff;
}

.platform-service-info strong {
  color: var(--text-primary);
  font-size: 13px;
}

.platform-service-info dl {
  display: grid;
  gap: 8px;
  margin: 0;
}

.platform-service-info dl div {
  display: grid;
  grid-template-columns: 108px minmax(0, 1fr);
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #e2ebf8;
}

.platform-service-info dl div:last-child {
  border-bottom: 0;
}

.platform-service-info dt,
.platform-service-info dd {
  margin: 0;
  min-width: 0;
  font-size: 12px;
  line-height: 18px;
  overflow-wrap: anywhere;
}

.platform-service-info dt {
  color: var(--primary);
  font-family: "SFMono-Regular", Consolas, monospace;
}

.platform-service-info dd {
  color: var(--text-secondary);
}

.platform-service-debug {
  overflow: auto;
}

.platform-service-payload {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid #dce9ff;
  border-radius: 8px;
  background: #fbfdff;
}

.platform-service-payload pre {
  min-height: 140px;
  max-height: 220px;
  margin: 0;
  padding: 12px 14px;
  overflow: auto;
  color: #344054;
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 12px;
  line-height: 20px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  border-radius: 6px;
  background: #f3f8ff;
}

.platform-service-log {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid #dce9ff;
  border-radius: 8px;
  background: #fbfdff;
}

.platform-service-log ul {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.platform-service-log li {
  display: grid;
  grid-template-columns: 56px 56px minmax(0, 1fr);
  gap: 10px;
  align-items: start;
  padding: 10px 0;
  border-bottom: 1px solid #eef3fb;
}

.platform-service-log li:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.platform-service-log span,
.platform-service-log b,
.platform-service-log p {
  margin: 0;
  font-size: 12px;
  line-height: 18px;
}

.platform-service-log span {
  color: var(--text-tertiary);
  font-family: "SFMono-Regular", Consolas, monospace;
}

.platform-service-log b {
  color: #00a870;
}

.platform-service-log p {
  color: var(--text-secondary);
}

.platform-api-doc {
  overflow: hidden;
}

.platform-service--api .platform-api-doc {
  grid-column: 1 / -1;
  overflow: auto;
}

.platform-api-doc .kg-panel__header span {
  min-width: 0;
  overflow: hidden;
  color: var(--text-tertiary);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.platform-api-doc__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  padding: 14px;
}

.platform-api-doc__grid .platform-table {
  table-layout: auto;
}

.platform-api-doc__grid .platform-table th,
.platform-api-doc__grid .platform-table td {
  height: auto;
  min-height: 38px;
  vertical-align: top;
  white-space: normal;
}

.platform-api-doc__grid article {
  min-width: 0;
  overflow: hidden;
  border: 1px solid #dce9ff;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.72);
}

.platform-api-doc__grid h3 {
  margin: 0;
  padding: 10px 12px;
  border-bottom: 1px solid #e2ebf8;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 20px;
}

.platform-code-sample {
  margin: 0 14px 14px;
  overflow: hidden;
  border: 1px solid #dce9ff;
  border-radius: 8px;
  background: #fbfdff;
}

.platform-api-examples {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  padding: 0 14px 14px;
}

.platform-api-examples article {
  min-width: 0;
  overflow: hidden;
  border: 1px solid #dce9ff;
  border-radius: 8px;
  background: #fbfdff;
}

.platform-api-examples h3 {
  margin: 0;
  padding: 10px 12px;
  border-bottom: 1px solid #e2ebf8;
  color: var(--text-primary);
  font-size: 14px;
}

.platform-api-examples pre {
  min-height: 180px;
  max-height: 260px;
  margin: 0;
  padding: 14px 16px;
  overflow: auto;
  color: #344054;
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 12px;
  line-height: 20px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.platform-code-sample div {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid #e2ebf8;
}

.platform-code-sample strong {
  margin-right: auto;
  color: var(--text-primary);
  font-size: 14px;
}

.platform-code-sample span {
  min-width: 56px;
  padding: 4px 8px;
  border-radius: 5px;
  background: #eef5ff;
  color: var(--text-secondary);
  font-size: 12px;
  text-align: center;
}

.platform-code-sample span:first-of-type {
  background: #fff;
  color: var(--primary);
  box-shadow: inset 0 0 0 1px #bdd7ff;
}

.platform-code-sample pre {
  min-height: 180px;
  max-height: 280px;
  margin: 0;
  padding: 16px 18px;
  overflow: auto;
  color: #344054;
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 12px;
  line-height: 20px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

@media (max-width: 1500px) {
  .platform-pipeline {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .platform-pipeline__step:not(:last-child)::after {
    display: none;
  }
}

@media (max-width: 1280px) {
  .platform-service:not(.platform-service--api) {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto auto auto minmax(0, 1fr);
  }

  .platform-construction,
  .platform-processing {
    grid-template-columns: minmax(0, 1fr);
  }

  .platform-cleaning-editor {
    grid-template-columns: minmax(0, 1fr);
  }

  .platform-cleaning-relations,
  .platform-structured-output,
  .platform-construction-side,
  .platform-build {
    grid-column: 1;
  }

  .platform-cleaning-steps {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .platform-processing-overview,
  .platform-construction-kpis,
  .platform-build-results__body,
  .platform-audit-reasons,
  .platform-processing-controls,
  .platform-build-pipeline__body,
  .platform-schema-mapping__body {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .platform-graph-summary,
  .platform-detail,
  .platform-service-debug,
  .platform-review {
    max-height: 360px;
  }

  .platform-service-console__body {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .platform-service-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .platform-overview-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 980px) {
  .platform-query {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto auto auto;
  }

  .platform-query-graph,
  .platform-query > .platform-detail {
    grid-column: 1;
    grid-row: auto;
  }

  .platform-query-graph {
    min-height: 460px;
  }

  .platform-build-context {
    flex-direction: column;
    align-items: flex-start;
  }
}

.platform-link-button {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--primary);
  font: inherit;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.platform-review-summary {
  display: grid;
  gap: 6px;
  margin: 12px 12px 0;
  padding: 10px 12px;
  border: 1px solid #dce9ff;
  border-radius: 8px;
  background: #f8fbff;
}

.platform-review-summary strong {
  color: var(--text-primary);
  font-size: 13px;
  line-height: 20px;
}

.platform-review-summary p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 18px;
}

.platform-review__title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.platform-review__tag {
  flex: 0 0 auto;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  line-height: 22px;
}

.platform-review__tag.is-待审核 {
  color: var(--warning);
  background: var(--warning-subtle);
}

.platform-review__tag.is-处理中 {
  color: var(--primary);
  background: var(--primary-subtle);
}

.platform-review__tag.is-已通过 {
  color: var(--success);
  background: var(--success-subtle);
}
</style>
