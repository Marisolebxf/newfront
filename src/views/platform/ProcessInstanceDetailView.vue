<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProcessingInstance } from './update-batch-data'

type Step = { id: string; name: string; status: '成功' | '运行中' | '阻断' | '待执行'; count: string; duration: string }
type TaskState = 'blocked' | 'running' | 'success'

const route = useRoute()
const router = useRouter()
const activeTab = ref<'overview' | 'input' | 'output' | 'logs' | 'quality' | 'lineage' | 'config'>('overview')
const taskId = computed(() => String(route.params.taskId || route.params.instanceId || 'DP-20260713-0200'))
const processingInstance = computed(() => getProcessingInstance(taskId.value))
const area = computed(() => String(route.params.area || (processingInstance.value?.stage === '图谱构建' || route.query.stage === '图谱构建' ? 'construction' : 'processing')))
const isConstruction = computed(() => area.value === 'construction')

const processingSteps: Step[] = [
  { id: 'source', name: '数据接入', status: '成功', count: '12,604 条', duration: '2m 18s' },
  { id: 'incremental', name: '增量识别', status: '成功', count: '12,438 条', duration: '48s' },
  { id: 'normalize', name: '清洗标准化', status: '成功', count: '12,420 条', duration: '4m 06s' },
  { id: 'quality', name: '质量检验', status: '阻断', count: '385 条异常', duration: '1m 42s' },
  { id: 'write', name: '标准表写入', status: '待执行', count: '0 条', duration: '-' },
]

const constructionSteps: Step[] = [
  { id: 'read', name: '读取标准数据', status: '成功', count: '12,604 条', duration: '1m 12s' },
  { id: 'schema', name: 'Schema 映射', status: '成功', count: '7 类实体', duration: '36s' },
  { id: 'llm', name: '大模型抽取', status: '阻断', count: '326 条异常', duration: '8m 24s' },
  { id: 'align', name: '实体对齐消歧', status: '待执行', count: '-', duration: '-' },
  { id: 'validate', name: '规则与证据校验', status: '待执行', count: '-', duration: '-' },
  { id: 'persist', name: '图谱入库', status: '待执行', count: '-', duration: '-' },
]

const taskState = computed<TaskState>(() => {
  if (processingInstance.value) {
    return ['待人工处理', '人工处理中'].includes(processingInstance.value.status) ? 'blocked' : 'success'
  }
  if (['DP-20260713-0200', 'KG-INC-20260713-018'].includes(taskId.value)) return 'blocked'
  if (['DP-20260713-1030', 'KG-INC-20260713-016', 'KG-INC-20260712-106'].includes(taskId.value)) return 'running'
  return 'success'
})
const taskStatus = computed(() => ({ blocked: '已阻断', running: '运行中', success: '已完成' })[taskState.value])
const taskStatusHint = computed(() => ({ blocked: '异常已隔离，下游未执行', running: '按计划执行，状态持续刷新', success: '全部节点执行成功' })[taskState.value])
const sourceTable = computed(() => processingInstance.value?.sourceTable ?? String(route.query.sourceTable || (isConstruction.value ? 'kg_stage.std_graph_input' : taskState.value === 'blocked' ? 'gkx.paper_record' : taskState.value === 'running' ? 'gkx.enterprise_profile' : 'gkx.expert_profile')))
const steps = computed<Step[]>(() => {
  const base = isConstruction.value ? constructionSteps : processingSteps
  if (taskState.value === 'blocked') {
    if (!processingInstance.value) return base
    const blockedId = isConstruction.value
      ? processingInstance.value.reviewType === '实体冲突' ? 'align' : 'validate'
      : 'quality'
    const blockedIndex = base.findIndex((step) => step.id === blockedId)
    return base.map((step, index) => ({
      ...step,
      status: index < blockedIndex ? '成功' : index === blockedIndex ? '阻断' : '待执行',
      count: index === blockedIndex ? '1 条异常' : index > blockedIndex ? '-' : step.count,
      duration: index === blockedIndex ? '6s' : index > blockedIndex ? '-' : step.duration,
    }))
  }
  if (taskState.value === 'success') return base.map((step) => ({ ...step, status: '成功', count: step.count === '-' || step.count === '0 条' ? '已完成' : step.count, duration: step.duration === '-' ? '1m 08s' : step.duration }))
  const runningId = isConstruction.value ? 'align' : 'normalize'
  const runningIndex = base.findIndex((step) => step.id === runningId)
  return base.map((step, index) => ({
    ...step,
    status: index < runningIndex ? '成功' : index === runningIndex ? '运行中' : '待执行',
    count: index === runningIndex ? (isConstruction.value ? '2,418 个候选' : '1,248 条') : index > runningIndex ? '-' : step.count,
    duration: index === runningIndex ? '6m 12s' : index > runningIndex ? '-' : step.duration,
  }))
})
const selectedStepId = ref(String(route.query.step || steps.value.find((item) => item.status === '阻断')?.id || steps.value[0]?.id || ''))
const selectedStep = computed(() => steps.value.find((item) => item.id === selectedStepId.value) ?? steps.value[0]!)
const isBlocked = computed(() => selectedStep.value.status === '阻断')
const actionMessage = ref('')

const taskMeta = computed(() => {
  const abnormal = processingInstance.value ? (taskState.value === 'blocked' ? '1' : '0') : taskState.value === 'blocked' ? (isConstruction.value ? '326' : '385') : taskState.value === 'running' ? (isConstruction.value ? '42' : '0') : '0'
  const isSpecificInstance = Boolean(processingInstance.value || route.params.instanceId)
  const input = isSpecificInstance ? '1' : isConstruction.value ? (taskState.value === 'success' ? '8.69 万' : '12,604') : taskState.value === 'running' ? '1,248' : taskState.value === 'success' ? '8,426' : '12,604'
  const success = isSpecificInstance ? (taskState.value === 'blocked' ? '0' : '1') : taskState.value === 'blocked' ? (isConstruction.value ? '0' : '12,219') : taskState.value === 'running' ? (isConstruction.value ? '7,624' : '536') : input
  const version = isConstruction.value ? (taskState.value === 'success' ? 'KG-2026.07.12.008' : `KG-DRAFT-${taskId.value.slice(-3)}`) : `DATA-2026.07.13.${taskId.value.slice(-4)}`
  const snapshot = `SNAP-${taskId.value}`
  const updateTime = processingInstance.value?.processedAt ?? (taskState.value === 'running' ? '2026-07-13 10:30（进行中）' : taskState.value === 'success' ? '2026-07-12 18:42' : '2026-07-13 10:24（阻断）')
  const change = processingInstance.value?.action ?? (isConstruction.value ? '新增或更新实体、关系与动态属性' : '源数据增量识别、标准化与质量校验')
  const instanceBack = processingInstance.value ? `/tasks?module=${encodeURIComponent(processingInstance.value.stage)}&batch=${processingInstance.value.batchId}` : ''
  return isConstruction.value
    ? { title: '图谱构建任务实例', back: instanceBack || '/tasks?module=图谱构建', domain: processingInstance.value?.objectType ?? String(route.query.objectType || (taskState.value === 'running' ? '专利域' : '论文域 / 人才域')), input, success, abnormal, owner: '张建图', version, snapshot, updateTime, change }
    : { title: '数据处理任务实例', back: instanceBack || '/tasks?module=数据处理', domain: processingInstance.value?.objectType ?? (taskState.value === 'running' ? '企业域' : taskState.value === 'success' ? '人才域' : '论文域'), input, success, abnormal, owner: '李质量', version, snapshot, updateTime, change }
})

const modelDetails = [
  ['模型', 'Qwen3-32B-Instruct'], ['Prompt 版本', 'kg-extract-v2.6.1'], ['Schema 版本', 'tech-kg-schema-v1.8'],
  ['Temperature', '0.1'], ['Token 用量', '1,284,630'], ['平均耗时', '1.86s'], ['重试次数', '42'], ['调用成功率', '97.42%'],
]

const genericDetails = computed(() => [
  ['节点编号', selectedStep.value.id], ['运行状态', selectedStep.value.status], ['处理数量', selectedStep.value.count],
  ['节点耗时', selectedStep.value.duration], ['执行引擎', isConstruction.value ? 'KG Pipeline Engine 2.4' : 'Data Pipeline Engine 3.1'], ['责任人', taskMeta.value.owner],
])

const selectStep = (id: string) => {
  selectedStepId.value = id
  activeTab.value = 'overview'
  void router.replace({ query: { ...route.query, step: id } })
}

const handleTaskAction = (action: 'stop' | 'rerun') => {
  actionMessage.value = action === 'stop' ? '已提交终止请求，当前节点将在安全检查点停止。' : '已创建重跑任务，将沿用当前快照、配置和修正结果。'
}

watch(() => route.query.step, (step) => {
  if (step && steps.value.some((item) => item.id === step)) selectedStepId.value = String(step)
})

watch([area, taskId], () => {
  selectedStepId.value = String(route.query.step || steps.value.find((item) => item.status === '阻断')?.id || steps.value[0]?.id || '')
  actionMessage.value = ''
})
</script>

<template>
  <div class="detail-page">
    <header class="detail-head">
      <div>
        <RouterLink :to="taskMeta.back">← {{ processingInstance ? '返回处理队列' : '返回任务中心' }}</RouterLink>
        <h1>{{ taskMeta.title }}</h1>
        <p>{{ taskId }} · {{ taskMeta.domain }} · 责任人 {{ taskMeta.owner }}</p>
      </div>
      <div class="detail-actions">
        <button v-if="taskState === 'running'" type="button" @click="handleTaskAction('stop')">终止任务</button>
        <button class="primary" type="button" @click="handleTaskAction('rerun')">{{ taskState === 'blocked' ? '从失败节点重跑' : '重新执行' }}</button>
      </div>
    </header>

    <p v-if="actionMessage" class="detail-action-message">{{ actionMessage }}</p>
    <section class="detail-summary">
      <article><span>任务状态</span><strong :class="{ danger: taskState === 'blocked', running: taskState === 'running', success: taskState === 'success' }">{{ taskStatus }}</strong><em>{{ taskStatusHint }}</em></article>
      <article><span>{{ isConstruction ? '输入数据量' : '数据总量' }}</span><strong>{{ taskMeta.input }}</strong><em>{{ isConstruction ? '本次构建读取的标准数据' : '本次任务读取记录' }}</em></article>
      <article><span>{{ isConstruction ? '已处理数据' : '处理通过' }}</span><strong>{{ taskMeta.success }}</strong><em>{{ isConstruction ? '已完成当前构建节点处理' : '已通过清洗与校验规则' }}</em></article>
      <article><span>异常数据</span><strong :class="{ danger: Number(taskMeta.abnormal) > 0 }">{{ taskMeta.abnormal }}</strong><em>{{ taskState === 'blocked' ? '已隔离，等待人工审核' : '当前累计异常记录' }}</em></article>
    </section>

    <section class="workflow-panel">
      <div class="section-head"><div><h2>执行流程</h2><p>点击任意节点查看输入、输出、日志、质量和配置版本</p></div><span class="legend">● 成功　● 运行中　● 阻断　● 待执行</span></div>
      <div class="workflow">
        <button v-for="(step, index) in steps" :key="step.id" type="button" :class="['workflow-step', `is-${step.status}`, { 'is-active': selectedStep.id === step.id }]" @click="selectStep(step.id)">
          <i>{{ index + 1 }}</i><span><strong>{{ step.name }}</strong><em>{{ step.count }} · {{ step.duration }}</em></span><b>{{ step.status }}</b>
        </button>
      </div>
    </section>

    <section class="node-panel">
      <div class="node-title">
        <div><span>节点执行详情</span><h2>{{ selectedStep.name }}</h2><p>{{ selectedStep.id }} · {{ selectedStep.status }} · {{ selectedStep.duration }}</p></div>
        <RouterLink v-if="isBlocked" :to="processingInstance ? `/manual-review/task/${processingInstance.id}` : `/manual-review?keyword=${taskId}`">进入人工处理 →</RouterLink>
      </div>
      <nav class="detail-tabs">
        <button v-for="tab in ([['overview','运行概览'],['input','输入数据'],['output','输出结果'],['logs','运行日志'],['quality','质量校验'],['lineage','数据血缘'],['config','运行配置']] as const)" :key="tab[0]" type="button" :class="{ active: activeTab === tab[0] }" @click="activeTab = tab[0]">{{ tab[1] }}</button>
      </nav>

      <div v-if="activeTab === 'overview'" class="overview-grid">
        <article><h3>运行信息</h3><dl><div v-for="row in genericDetails" :key="row[0]"><dt>{{ row[0] }}</dt><dd>{{ row[1] }}</dd></div></dl></article>
        <article v-if="selectedStep.id === 'llm'"><h3>大模型调用</h3><dl><div v-for="row in modelDetails" :key="row[0]"><dt>{{ row[0] }}</dt><dd>{{ row[1] }}</dd></div></dl></article>
        <article :class="{ alert: isBlocked }"><h3>{{ isBlocked ? '阻断原因' : '执行结果' }}</h3><p>{{ isBlocked ? '输出结果未通过强规则检查，异常记录已隔离，下游节点未执行。' : selectedStep.status === '运行中' ? '节点正在执行，指标与日志将持续刷新。' : selectedStep.status === '待执行' ? '等待上游节点完成后自动开始。' : '节点输出结果已完成快照，可继续下游处理。' }}</p><ul v-if="isBlocked"><template v-if="processingInstance"><li>{{ processingInstance.reviewType }} 1 条</li><li>{{ processingInstance.result }}</li></template><template v-else><li>{{ isConstruction ? '结构错误 128 条' : '必填缺失 18 条' }}</li><li>{{ isConstruction ? '证据不足 156 条' : '唯一性冲突 326 条' }}</li><li>{{ isConstruction ? '低置信度 42 条' : '枚举异常 41 条' }}</li></template></ul></article>
      </div>
      <pre v-else-if="activeTab === 'input'">{
  "{{ processingInstance ? 'processing_instance_id' : 'batch_id' }}": "{{ taskId }}",
  "update_batch_id": "{{ processingInstance?.batchId ?? taskId }}",
  "source_table": "{{ sourceTable }}",
  "source_record_id": "{{ processingInstance?.sourceRecordId ?? '-' }}",
  "record_count": "{{ taskMeta.input }}",
  "schema_version": "tech-kg-schema-v1.8",
  "snapshot_time": "2026-07-13 10:18:42"
}</pre>
      <pre v-else-if="activeTab === 'output' && processingInstance">{
  "processing_instance_id": "{{ processingInstance.id }}",
  "object_id": "{{ processingInstance.objectId }}",
  "object_name": "{{ processingInstance.objectName }}",
  "action": "{{ processingInstance.action }}",
  "rule": "{{ processingInstance.rule }}",
  "result": "{{ processingInstance.result }}",
  "status": "{{ processingInstance.status }}"
}</pre>
      <pre v-else-if="activeTab === 'output' && isConstruction">{
  "entities": 3261,
  "relations": 8942,
  "properties": 1203,
  "passed": "{{ taskMeta.success }}",
  "quarantined": {{ taskMeta.abnormal }},
  "next_step": "{{ isBlocked ? '阻断，等待人工审核' : '继续执行' }}"
}</pre>
      <pre v-else-if="activeTab === 'output'">{
  "read_records": "{{ taskMeta.input }}",
  "passed_records": "{{ taskMeta.success }}",
  "quarantined_records": {{ taskMeta.abnormal }},
  "written_records": "{{ taskState === 'success' ? taskMeta.success : '待当前流程完成' }}",
  "next_step": "{{ isBlocked ? '阻断，等待人工审核' : taskState === 'running' ? '继续执行后续节点' : '数据处理完成' }}"
}</pre>
      <pre v-else-if="activeTab === 'logs'">10:18:42 INFO  节点启动，加载任务快照 {{ taskId }}
10:18:43 INFO  加载 Schema tech-kg-schema-v1.8
{{ taskState === 'blocked' ? '10:22:16 WARN  发现异常候选结果\n10:24:08 ERROR 强规则校验失败\n10:24:09 INFO  隔离异常记录，阻断下游节点\n10:24:10 INFO  已生成异常告警' : taskState === 'running' ? '10:22:16 INFO  当前节点持续处理，资源与吞吐正常\n10:24:10 INFO  已完成阶段性结果快照' : '10:22:16 INFO  所有规则校验通过\n10:24:10 INFO  任务已成功完成并生成结果快照' }}</pre>
      <div v-else-if="activeTab === 'quality'" class="quality-table"><table><thead><tr><th>规则</th><th>类型</th><th>结果</th><th>异常数</th><th>下游策略</th></tr></thead><tbody v-if="taskState === 'blocked'"><tr><td>{{ isConstruction ? 'KG-SCHEMA-014' : 'Q-001' }}</td><td>{{ isConstruction ? 'Schema 结构' : '必填完整性' }}</td><td>失败</td><td>{{ isConstruction ? '128' : '18' }}</td><td>隔离</td></tr><tr><td>{{ isConstruction ? 'KG-EVIDENCE-008' : 'Q-014' }}</td><td>{{ isConstruction ? '证据完整性' : '唯一性' }}</td><td>失败</td><td>{{ isConstruction ? '156' : '326' }}</td><td>阻断</td></tr><tr><td>{{ isConstruction ? 'KG-CONFIDENCE-003' : 'Q-027' }}</td><td>{{ isConstruction ? '置信度' : '枚举一致性' }}</td><td>警告</td><td>{{ isConstruction ? '42' : '41' }}</td><td>转人工</td></tr></tbody><tbody v-else><tr><td>BASE-CHECK-001</td><td>基础约束</td><td>通过</td><td>0</td><td>继续执行</td></tr><tr><td>EVIDENCE-008</td><td>证据完整性</td><td>{{ taskState === 'running' ? '监测中' : '通过' }}</td><td>0</td><td>继续执行</td></tr></tbody></table></div>
      <div v-else-if="activeTab === 'lineage'" class="lineage"><span>gkx 原始表</span><b>→</b><span>kg_stage 标准表</span><b>→</b><span>{{ selectedStep.name }}</span><b>→</b><span>KG 候选层</span><b>→</b><span>图数据库</span></div>
      <div v-else class="quality-table"><table><thead><tr><th>配置项</th><th>当前值 / 版本</th><th>发布人</th><th>发布时间</th></tr></thead><tbody><tr><td>Pipeline Definition</td><td>pipeline-2.4.8</td><td>张建图</td><td>2026-07-12 18:30</td></tr><tr><td>Schema</td><td>tech-kg-schema-v1.8</td><td>李质量</td><td>2026-07-11 14:06</td></tr><tr><td>Prompt Template</td><td>kg-extract-v2.6.1</td><td>王算法</td><td>2026-07-13 09:20</td></tr><tr v-if="isConstruction"><td>目标图谱版本</td><td>{{ taskMeta.version }}</td><td>系统生成</td><td>{{ taskMeta.updateTime }}</td></tr><tr v-if="isConstruction"><td>恢复快照</td><td>{{ taskMeta.snapshot }}</td><td>系统生成</td><td>任务启动时</td></tr></tbody></table></div>
    </section>
  </div>
</template>

<style scoped>
.detail-page{height:100%;overflow:auto;padding-bottom:16px;color:#17233b}.detail-head{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:14px}.detail-head a{color:#165dff;font-size:13px;text-decoration:none}.detail-head h1{margin:7px 0 2px;font-size:22px}.detail-head p{margin:0;color:#66758f;font-size:13px}.detail-actions{display:flex;gap:8px}.detail-actions button{height:34px;padding:0 14px;border:1px solid #bdd0ea;border-radius:6px;background:#fff;color:#40516d;cursor:pointer}.detail-actions .primary{border-color:#165dff;background:#165dff;color:#fff}.detail-actions .rollback{border-color:#f6b9b4;color:#b42318}.detail-action-message{margin:-3px 0 12px;padding:9px 12px;border:1px solid #b2ccff;border-radius:6px;background:#f0f5ff;color:#344f7a;font-size:12px}.rollback-confirm,.update-error-banner{display:flex;align-items:center;gap:10px;margin-bottom:12px;padding:12px 14px;border:1px solid #f6c7c2;border-radius:7px;background:#fff7f6}.rollback-confirm>div,.update-error-banner>div{flex:1}.rollback-confirm strong,.update-error-banner strong{color:#912018;font-size:12px}.rollback-confirm p,.update-error-banner p{margin:3px 0 0;color:#77504c;font-size:10px}.rollback-confirm button{height:30px;padding:0 11px;border:1px solid #d4dfed;border-radius:5px;background:#fff;color:#52647d;font-size:10px;cursor:pointer}.rollback-confirm .danger-button{border-color:#d92d20;background:#d92d20;color:#fff}.update-error-banner>i{display:grid;place-items:center;width:27px;height:27px;border-radius:50%;background:#fee4e2;color:#d92d20;font-style:normal;font-weight:700}.update-error-banner>a{color:#d92d20;font-size:10px;text-decoration:none}.detail-summary{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin-bottom:14px}.detail-summary article{display:grid;gap:5px;padding:15px 17px;border:1px solid #bdd7ff;border-radius:8px;background:#fff}.detail-summary span{color:#65738b;font-size:12px}.detail-summary strong{font-size:22px}.detail-summary .version-value{overflow:hidden;font-size:15px;text-overflow:ellipsis;white-space:nowrap}.detail-summary em{overflow:hidden;color:#8290a7;font-size:12px;font-style:normal;text-overflow:ellipsis;white-space:nowrap}.update-record-panel{margin-bottom:14px;overflow:hidden;border:1px solid #bdd7ff;border-radius:8px;background:#fff}.update-record-panel>header{display:flex;align-items:center;justify-content:space-between;padding:11px 14px;border-bottom:1px solid #dce8f8;background:#f8fbff}.update-record-panel h2{margin:0;font-size:14px}.update-record-panel header p{margin:2px 0 0;color:#77869c;font-size:10px}.update-record-panel header>span{padding:3px 8px;border-radius:99px;background:#eaf2ff;color:#165dff;font-size:9px}.update-record-panel>div{display:grid;grid-template-columns:1.1fr 1.8fr .7fr 1fr 1.2fr}.update-record-panel article{display:grid;gap:5px;padding:12px 14px;border-right:1px solid #e2eaf5}.update-record-panel article:last-child{border-right:0}.update-record-panel article span{color:#78869b;font-size:9px}.update-record-panel article strong{color:#344861;font-size:10px;line-height:16px}.danger{color:#d92d20!important}.running{color:#165dff!important}.success{color:#079455!important}.workflow-panel,.node-panel{margin-bottom:14px;border:1px solid #b9d4fb;border-radius:9px;background:rgba(255,255,255,.95);box-shadow:0 10px 24px rgba(48,105,194,.09);overflow:hidden}.section-head,.node-title{display:flex;align-items:center;justify-content:space-between;padding:13px 16px;border-bottom:1px solid #dce8f8;background:#f8fbff}.section-head h2,.node-title h2{margin:0;font-size:17px}.section-head p,.node-title p{margin:3px 0 0;color:#70809a;font-size:12px}.legend{color:#71809a;font-size:12px}.workflow{display:grid;grid-template-columns:repeat(6,minmax(150px,1fr));gap:14px;padding:16px;overflow:auto}.workflow-step{position:relative;display:grid;grid-template-columns:26px minmax(0,1fr);gap:8px;min-height:82px;padding:12px;border:1px solid #cfddf0;border-radius:7px;background:#fff;text-align:left;cursor:pointer}.workflow-step:not(:last-child)::after{position:absolute;top:40px;right:-15px;width:14px;height:2px;background:#a6bfe5;content:""}.workflow-step:hover,.workflow-step.is-active{border-color:#165dff;box-shadow:0 0 0 2px rgba(22,93,255,.1)}.workflow-step i{display:grid;place-items:center;width:24px;height:24px;border-radius:50%;background:#12b76a;color:#fff;font-style:normal}.workflow-step span{display:grid;gap:5px}.workflow-step strong{font-size:13px}.workflow-step em{color:#73829a;font-size:11px;font-style:normal}.workflow-step b{grid-column:2;color:#079455;font-size:11px}.workflow-step.is-运行中 i{background:#165dff;box-shadow:0 0 0 4px #eaf2ff}.workflow-step.is-运行中 b{color:#165dff}.workflow-step.is-阻断 i{background:#d92d20}.workflow-step.is-阻断 b{color:#d92d20}.workflow-step.is-待执行 i{background:#98a2b3}.workflow-step.is-待执行 b{color:#667085}.node-title>div>span{color:#165dff;font-size:11px}.node-title a{height:32px;padding:0 12px;border-radius:5px;background:#d92d20;color:#fff;font-size:12px;line-height:32px;text-decoration:none}.detail-tabs{display:flex;gap:2px;padding:0 14px;border-bottom:1px solid #dce8f8}.detail-tabs button{height:42px;padding:0 13px;border:0;border-bottom:2px solid transparent;background:transparent;color:#66758f;cursor:pointer}.detail-tabs button.active{border-bottom-color:#165dff;color:#165dff;font-weight:600}.overview-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;padding:14px}.overview-grid article{padding:14px;border:1px solid #dce8f8;border-radius:7px;background:#fbfdff}.overview-grid article.alert{border-color:#fecdca;background:#fff8f7}.overview-grid h3{margin:0 0 10px;font-size:14px}.overview-grid dl{margin:0}.overview-grid dl div{display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-bottom:1px solid #eaf0f8;font-size:12px}.overview-grid dt{color:#738099}.overview-grid dd{margin:0;color:#263650;text-align:right}.overview-grid p,.overview-grid li{color:#596981;font-size:12px;line-height:20px}.node-panel>pre{min-height:260px;margin:0;padding:18px;background:#17233b;color:#d9e7ff;font:12px/22px Consolas,monospace;white-space:pre-wrap}.quality-table{padding:14px}.quality-table table{width:100%;border-collapse:collapse;font-size:12px}.quality-table th,.quality-table td{height:42px;padding:8px 12px;border-bottom:1px solid #e3ebf6;text-align:left}.quality-table th{background:#f4f8fd;color:#64738b}.lineage{display:flex;align-items:center;justify-content:center;gap:16px;min-height:220px;padding:20px;overflow:auto}.lineage span{min-width:150px;padding:18px;border:1px solid #bdd7ff;border-radius:7px;background:#f6faff;color:#254164;text-align:center}.lineage b{color:#165dff}@media(max-width:1200px){.detail-summary{grid-template-columns:repeat(2,1fr)}.update-record-panel>div{grid-template-columns:repeat(2,1fr)}.overview-grid{grid-template-columns:1fr}.workflow{grid-template-columns:repeat(3,minmax(160px,1fr))}}
.detail-summary{grid-template-columns:repeat(4,minmax(0,1fr))}
.detail-actions>a{height:34px;padding:0 14px;border:1px solid #bdd0ea;border-radius:6px;background:#fff;color:#40516d;line-height:32px;text-decoration:none}
</style>
