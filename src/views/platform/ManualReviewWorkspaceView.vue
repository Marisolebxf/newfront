<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

import { getReviewRecord, type ReviewRecord } from './manual-review-data'

const route = useRoute()
const sourceRecord = getReviewRecord(String(route.params.instanceId || ''))
const record = ref<ReviewRecord | undefined>(sourceRecord ? { ...sourceRecord } : undefined)
const isSupported = computed(() => Boolean(record.value))
const isHistory = computed(() => record.value?.status === '已完成')
const isEditable = computed(() => record.value?.status === '待处理')
const entityTypes = [
  { value: 'Expert', label: '专家 / 人才 / 学者' }, { value: 'Organization', label: '机构 / 企业' }, { value: 'Paper', label: '论文' },
  { value: 'Project', label: '项目' }, { value: 'Patent', label: '专利' }, { value: 'Report', label: '报告' }, { value: 'Policy', label: '政策' },
  { value: 'Event', label: '事件 / 资讯' }, { value: 'IndustryChainNode', label: '产业链节点' }, { value: 'Product', label: '产品' },
  { value: 'ResearchField', label: '研究方向' }, { value: 'Person', label: '通用人员' }, { value: 'Publication', label: '期刊 / 会议' }, { value: 'IndustryChain', label: '产业链' },
]
const expertFields = ['expert_id', 'name_zh', 'name_en', 'organization_name_zh', 'bio_zh', 'bio_en', 'paper_count', 'citation_count', 'h_index']
const organizationFields = ['org_id', 'name_zh', 'name_en', 'external_id', 'credit_code', 'org_category', 'province', 'city', 'address', 'registered_capital_value']
const paperFields = ['paper_id', 'doi', 'title_zh', 'title_en', 'publish_year', 'abstract_zh', 'abstract_en', 'keywords', 'source_type']
const patentFields = ['patent_id', 'publication_number', 'application_number', 'application_date', 'legal_status', 'ipc_main', 'cpc_main']
const relationTypes = ['HAS_RESEARCH_FIELD', 'PUBLISH', 'WORKS_AT', 'AFFILIATED_WITH', 'CO_AUTHOR', 'PARTICIPATE_IN', 'INVENT_PATENT', 'COOPERATE_WITH', 'HAS_PRODUCT', 'BELONGS_TO_CHAIN_NODE']
type MappingOption = { value: string; label: string }
type MappingRow = { source: string; sample: string; scope: string; target: string; options: MappingOption[] }
const fieldOptions = (scope: string, fields: string[]): MappingOption[] => fields.map((value) => ({ value, label: `${scope}.${value}` }))
const entityOptions: MappingOption[] = entityTypes.map((item) => ({ value: item.value, label: `${item.value}（${item.label}）` }))
const relationOptions: MappingOption[] = relationTypes.map((value) => ({ value, label: value }))
const buildMappingRows = (item?: ReviewRecord): MappingRow[] => {
  if (!item) return []
  if (item.id === 'PI-20260714-0101') return [
    { source: 'object_type', sample: 'PersonMention', scope: '标准实体', target: 'Expert', options: entityOptions },
    { source: 'person_name', sample: '张明远', scope: 'Expert', target: 'name_zh', options: fieldOptions('Expert', expertFields) },
    { source: 'employer', sample: '中国科学院自动化研究所', scope: 'Expert', target: 'organization_name_zh', options: fieldOptions('Expert', expertFields) },
  ]
  if (item.id === 'PI-20260714-0102') return [
    { source: 'corp_name', sample: '华南智能芯片有限公司', scope: 'Organization', target: 'name_zh', options: fieldOptions('Organization', organizationFields) },
    { source: 'credit_no', sample: '91440300MA5F…', scope: 'Organization', target: 'credit_code', options: fieldOptions('Organization', organizationFields) },
    { source: 'registered_capital', sample: '5000 万元', scope: 'Organization', target: 'registered_capital_value', options: fieldOptions('Organization', organizationFields) },
  ]
  if (item.type === '公共字典配置异常' || item.domain === '专利') return [
    { source: 'legal_status_raw', sample: 'substantive-review', scope: 'Patent', target: 'legal_status', options: fieldOptions('Patent', patentFields) },
  ]
  if (item.type === '关系证据不足' || item.objectType.includes('关系')) return [
    { source: 'relation_type', sample: item.sourceResult, scope: '事实关系', target: item.sourceResult.match(/[A-Z_]{3,}/)?.[0] ?? 'COOPERATE_WITH', options: relationOptions },
  ]
  if (item.type === '实体类型错误') return [
    { source: 'entity_type', sample: item.sourceResult, scope: '标准实体', target: 'Expert', options: entityOptions },
  ]
  if (item.objectType.includes('实体')) return [
    { source: 'person_name', sample: item.object.split('/')[0].trim(), scope: 'Expert', target: 'name_zh', options: fieldOptions('Expert', expertFields) },
    { source: 'organization', sample: item.domain === '人才' ? '待核对机构' : item.domain, scope: 'Expert', target: 'organization_name_zh', options: fieldOptions('Expert', expertFields) },
  ]
  if (item.type === '属性冲突') return [
    { source: 'organization', sample: item.sourceResult, scope: 'Expert', target: 'organization_name_zh', options: fieldOptions('Expert', expertFields) },
  ]
  return [
    { source: item.type === '必填缺失' ? 'title' : item.type === '枚举异常' ? 'source_type' : 'paper_id', sample: item.sourceResult, scope: 'Paper', target: item.type === '必填缺失' ? 'title_zh' : item.type === '枚举异常' ? 'source_type' : 'paper_id', options: fieldOptions('Paper', paperFields) },
  ]
}
const mappingRows = ref<MappingRow[]>(buildMappingRows(record.value))
const note = ref(record.value?.decisionNote ?? '')
const feedback = ref('')
const primaryAction = computed(() => '保存字段映射并重跑')

const backPath = computed(() => isHistory.value ? '/manual-review?tab=history' : `/manual-review?batch=${record.value?.batch ?? ''}`)
const handleReview = (action: string) => {
  if (!record.value) return
  record.value.status = '已完成'
  record.value.decision = action
  if (action === primaryAction.value) {
    record.value.sourceResult = mappingRows.value.map((item) => `${item.source} → ${item.scope}.${item.target}`).join('；')
  }
  record.value.decisionNote = note.value
  record.value.completedAt = '2026-07-15 11:08:26'
  record.value.updatedAt = '刚刚'
  feedback.value = action === '驳回上游'
    ? '处理结果已回写，该对象将返回上游节点重新处理。'
    : action.includes('重跑') || action.includes('重试')
      ? `修正结果已回写，系统已从“${record.value.node}”创建新的重跑实例。重跑状态请到任务中心查看。`
      : '处理结果已回写。'
}
</script>

<template>
  <div v-if="record && isSupported" class="review-workspace review-task-detail">
    <header class="review-workspace__head">
      <div><RouterLink :to="backPath">← 返回处理队列</RouterLink><h1>{{ isHistory ? '处理记录' : '人工审核' }}</h1><p>{{ record.id }} · {{ record.handler }}</p></div>
      <span :class="['batch-status', `is-${record.status}`]">{{ record.status }}</span>
    </header>

    <main class="review-task-body">
      <section class="issue-summary">
        <header><span>1</span><div><h2>异常诊断</h2><p>{{ record.node }} · {{ record.type }}</p></div></header>
        <div class="issue-location"><strong>{{ record.object }}</strong><span>{{ record.objectType }} · {{ record.objectId }}</span><span>{{ record.sourceTable }} / {{ record.sourceRecordId }}</span></div>
        <p class="issue-reason">{{ record.evidence }}</p>
        <p class="issue-current">当前结果：{{ record.sourceResult }}</p>
      </section>

      <section class="review-editor">
        <header><span>2</span><div><h2>字段映射配置</h2><p>{{ record.suggestion }}</p></div></header>

        <div v-if="isEditable" class="review-form">
          <div class="mapping-head"><span>来源字段</span><span>样例值</span><span>Schema 目标项</span></div>
          <div v-for="item in mappingRows" :key="item.source" class="mapping-row"><code>{{ item.source }}</code><span>{{ item.sample }}</span><select v-model="item.target"><option v-for="option in item.options" :key="option.value" :value="option.value">{{ option.label }}</option></select></div>

          <label class="wide"><span>审核备注（可选）</span><textarea v-model="note" placeholder="记录依据或补充说明" /></label>
        </div>

        <div v-else class="review-readonly-result"><strong>{{ record.decision }}</strong><p>{{ record.decisionNote }}</p><em>{{ record.completedAt }}</em></div>
      </section>

      <p v-if="feedback" class="review-feedback">{{ feedback }}</p>
    </main>

    <footer class="review-task-footer"><span>{{ isHistory ? '处理已完成' : '选定内容均来自当前 Schema v1.8' }}</span><div v-if="isEditable"><button type="button" @click="handleReview('驳回上游')">驳回上游</button><button class="primary" type="button" @click="handleReview(primaryAction)">{{ primaryAction }}</button></div></footer>
  </div>
  <div v-else class="review-not-found"><h1>该处理实例未配置详情页</h1><RouterLink to="/manual-review">返回人工审核</RouterLink></div>
</template>

<style scoped>
.review-workspace{display:flex;height:100%;min-height:0;flex-direction:column;color:#17233b}.review-workspace__head{display:flex;flex:0 0 auto;align-items:flex-end;justify-content:space-between;margin-bottom:12px}.review-workspace__head a{color:#165dff;font-size:12px;text-decoration:none}.review-workspace__head h1{margin:6px 0 2px;font-size:22px}.review-workspace__head p{margin:0;color:#6c7b93;font-size:12px}.review-workspace__head-actions{display:flex;align-items:center;gap:10px}.review-workspace__head-actions>a{height:32px;padding:0 12px;border:1px solid #bdd0ea;border-radius:6px;background:#fff;line-height:30px}.severity-badge,.batch-status,.review-detail header>em,.review-queue__list em{padding:3px 8px;border-radius:99px;background:#eef2f7;color:#596a83;font-size:11px;font-style:normal}.severity-badge.is-严重{background:#fee4e2;color:#d92d20}.severity-badge.is-警告{background:#fff3d8;color:#dc6803}.severity-badge.is-提示{background:#eaf2ff;color:#175cd3}.is-待处理{background:#fff0e8!important;color:#c4320a!important}.is-处理中{background:#eaf2ff!important;color:#175cd3!important}.is-已完成{background:#e9f8ef!important;color:#067647!important}.batch-overview{display:grid;flex:0 0 auto;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:12px}.batch-overview article{display:grid;gap:5px;padding:12px 15px;border:1px solid #bdd7ff;border-radius:8px;background:#fff}.batch-overview span{color:#687791;font-size:11px}.batch-overview strong{font-size:21px}.batch-overview em{overflow:hidden;color:#8491a5;font-size:10px;font-style:normal;text-overflow:ellipsis;white-space:nowrap}.severity-explain{display:grid;flex:0 0 auto;grid-template-columns:120px minmax(260px,1fr) minmax(420px,1.4fr);align-items:center;gap:16px;margin-bottom:12px;padding:10px 14px;border:1px solid #b8d2f5;border-radius:7px;background:#f6faff}.severity-explain>div{display:flex;align-items:center;gap:9px}.severity-explain span,.severity-explain small{color:#6a7890;font-size:10px}.severity-explain strong{font-size:14px}.severity-explain p{margin:0;color:#354760;font-size:11px}.severity-explain.is-严重{border-color:#f5b8b3;background:#fff5f4}.severity-explain.is-严重 strong{color:#d92d20}.severity-explain.is-警告{border-color:#f3d08a;background:#fffaf0}.severity-explain.is-警告 strong{color:#dc6803}.severity-explain.is-提示 strong{color:#175cd3}.danger{color:#d92d20}.running{color:#165dff}.success{color:#079455}.review-master-detail{display:grid;flex:1;min-height:0;grid-template-columns:minmax(330px,38%) minmax(0,62%);overflow:hidden;border:1px solid #bdd7ff;border-radius:9px;background:#fff;box-shadow:0 12px 28px rgba(48,105,194,.1)}.review-queue{display:flex;min-height:0;border-right:1px solid #dce8f8;flex-direction:column;background:#f8fbff}.review-queue>header{display:flex;align-items:center;justify-content:space-between;padding:14px;border-bottom:1px solid #dce8f8}.review-queue h2{margin:0;font-size:16px}.review-queue header p{margin:3px 0 0;color:#75849a;font-size:10px}.review-queue header>b{color:#165dff;font-size:11px}.review-queue__filter{display:grid;grid-template-columns:1fr 110px;gap:8px;padding:10px;border-bottom:1px solid #e2eaf5}.review-queue__filter input,.review-queue__filter select{min-width:0;height:32px;padding:0 9px;border:1px solid #bdd0ea;border-radius:5px;background:#fff;color:#344861}.review-queue__list{flex:1;min-height:0;overflow:auto;padding:8px}.review-queue__list button{display:grid;width:100%;gap:5px;margin-bottom:7px;padding:11px;border:1px solid transparent;border-radius:7px;background:#fff;color:#263650;text-align:left;cursor:pointer}.review-queue__list button:hover,.review-queue__list button.active{border-color:#165dff;box-shadow:0 0 0 2px rgba(22,93,255,.08)}.review-queue__list button>span{display:flex;align-items:center;justify-content:space-between}.review-queue__list button b{color:#165dff;font-size:11px}.review-queue__list button strong{font-size:13px}.review-queue__list button p{margin:0;color:#63738c;font-size:11px}.review-queue__list button small{color:#8a96a8;font-size:10px}.review-detail{display:flex;min-width:0;min-height:0;flex-direction:column}.review-detail>header{display:flex;align-items:flex-start;justify-content:space-between;padding:16px 18px;border-bottom:1px solid #dce8f8}.review-detail header span{color:#165dff;font-size:10px}.review-detail h2{margin:5px 0 3px;font-size:19px}.review-detail header p{margin:0;color:#75849a;font-size:11px}.review-detail__body{flex:1;min-height:0;overflow:auto;padding:14px}.review-detail__body section,.review-compare article{padding:14px;border:1px solid #dce8f8;border-radius:7px;background:#fbfdff}.review-detail__body h3{margin:0 0 8px;font-size:14px}.decision-result p,.review-compare p,.review-evidence p{margin:0;color:#61708a;font-size:11px;line-height:19px}.review-compare{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0}.review-compare span,.review-evidence span{display:block;margin-bottom:8px;color:#718098;font-size:10px}.review-compare strong,.review-evidence strong{display:block;font-size:12px;line-height:19px}.review-compare em{display:block;margin-top:10px;color:#d92d20;font-size:10px;font-style:normal}.review-compare textarea{box-sizing:border-box;width:100%;min-height:72px;margin-bottom:7px;padding:9px;border:1px solid #bdd0ea;border-radius:5px;color:#263650;font:12px/18px inherit;resize:vertical}.review-evidence>div{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.review-evidence article{padding:10px;border:1px solid #e1e9f4;border-radius:6px;background:#fff}.review-feedback{padding:9px 11px;border:1px solid #a6f4c5;border-radius:6px;background:#ecfdf3;color:#067647;font-size:11px}.review-detail>footer{display:flex;align-items:center;justify-content:space-between;padding:11px 14px;border-top:1px solid #dce8f8;background:#fff}.review-detail>footer span{color:#718098;font-size:10px}.review-detail>footer div{display:flex;gap:8px}.review-detail>footer button{height:32px;padding:0 12px;border:1px solid #bdd0ea;border-radius:5px;background:#fff;color:#40516d;cursor:pointer}.review-detail>footer .primary{border-color:#165dff;background:#165dff;color:#fff}.review-not-found{padding:40px;text-align:center}.review-not-found a{color:#165dff}@media(max-width:1100px){.batch-overview{grid-template-columns:repeat(2,1fr)}.severity-explain{grid-template-columns:110px 1fr}.severity-explain small{grid-column:1/-1}.review-master-detail{grid-template-columns:320px minmax(0,1fr)}.review-evidence>div{grid-template-columns:1fr}}@media(max-width:760px){.severity-explain{grid-template-columns:1fr}.severity-explain small{grid-column:auto}.review-master-detail{display:block;overflow:auto}.review-queue{max-height:340px;border-right:0;border-bottom:1px solid #dce8f8}.review-detail{min-height:700px}.review-compare{grid-template-columns:1fr}}
.instance-link{display:inline-block;margin-top:6px;color:#165dff;font-size:10px;text-decoration:none}
.review-task-detail{overflow:hidden}.review-object-card{display:flex;flex:0 0 auto;align-items:center;justify-content:space-between;margin-bottom:10px;padding:14px 18px;border:1px solid #bdd7ff;border-radius:8px;background:linear-gradient(135deg,#fff,#f3f8ff)}.review-object-card span{color:#718098;font-size:10px}.review-object-card h2{margin:5px 0 3px;font-size:19px}.review-object-card p{margin:0;color:#6d7c93;font-size:11px}.review-object-card em{padding:4px 10px;border-radius:99px;background:#fff0e8;color:#c4320a;font-size:11px;font-style:normal}.review-meta-grid{display:grid;flex:0 0 auto;grid-template-columns:.7fr 1.2fr 1.5fr .7fr .55fr;margin-bottom:10px;overflow:hidden;border:1px solid #c5daf7;border-radius:8px;background:#fff}.review-meta-grid article{display:grid;gap:5px;padding:11px 14px;border-right:1px solid #e1eaf5}.review-meta-grid article:last-child{border-right:0}.review-meta-grid span{color:#78869b;font-size:9px}.review-meta-grid strong{color:#344861;font-size:10px;line-height:16px}.review-task-body{flex:1;min-height:0;overflow:auto;padding:14px;border:1px solid #bdd7ff;border-radius:8px;background:rgba(255,255,255,.95)}.review-task-body>section,.review-task-body .review-compare article{padding:14px;border:1px solid #dce8f8;border-radius:7px;background:#fbfdff}.review-task-body h3{margin:0 0 8px;font-size:14px}.decision-result p,.review-task-body .review-compare p,.review-task-body .review-evidence p{margin:0;color:#61708a;font-size:11px;line-height:19px}.decision-options{margin-bottom:10px}.decision-options>div{display:flex;gap:8px}.decision-options label{padding:8px 12px;border:1px solid #d4dfed;border-radius:6px;background:#fff;color:#52647f;font-size:11px;cursor:pointer}.decision-options label.active{border-color:#165dff;background:#eef5ff;color:#165dff}.decision-options input{margin-right:6px}.decision-options p{margin:9px 0 0;color:#718098;font-size:10px}.review-history{margin-top:10px}.review-history ol{margin:0;padding:0;list-style:none}.review-history li{display:grid;grid-template-columns:12px minmax(0,1fr) 150px;gap:10px;padding:9px 0;border-bottom:1px solid #e8eef6}.review-history li:last-child{border-bottom:0}.review-history i{width:8px;height:8px;margin-top:4px;border-radius:50%;background:#165dff;box-shadow:0 0 0 3px #eaf2ff}.review-history strong{font-size:11px}.review-history p{margin:3px 0 0;color:#718098;font-size:10px}.review-history time{color:#8290a7;font-size:10px;text-align:right}.review-task-footer{display:flex;flex:0 0 auto;align-items:center;justify-content:space-between;margin-top:10px;padding:11px 14px;border:1px solid #dce8f8;border-radius:7px;background:#fff}.review-task-footer>span{color:#718098;font-size:10px}.review-task-footer>div{display:flex;gap:8px}.review-task-footer button{height:32px;padding:0 12px;border:1px solid #bdd0ea;border-radius:5px;background:#fff;color:#40516d;cursor:pointer}.review-task-footer button.primary{border-color:#165dff;background:#165dff;color:#fff}@media(max-width:1000px){.review-meta-grid{grid-template-columns:repeat(2,1fr)}.review-meta-grid article{border-bottom:1px solid #e1eaf5}.decision-options>div{flex-wrap:wrap}}
.review-progress-panel{flex:0 0 auto;margin-bottom:10px;overflow:hidden;border:1px solid #b8d2f5;border-radius:8px;background:#fff}.review-progress-panel>header{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border-bottom:1px solid #dce8f8;background:#f4f8ff}.review-progress-panel h2{margin:0;font-size:14px}.review-progress-panel header p{margin:3px 0 0;color:#718098;font-size:10px}.review-progress-panel header>span{padding:3px 9px;border-radius:99px;background:#eaf2ff;color:#175cd3;font-size:10px}.review-progress-panel>div{display:grid;grid-template-columns:.8fr .9fr 1.4fr 1.1fr 1fr}.review-progress-panel article{display:grid;gap:5px;padding:10px 13px;border-right:1px solid #e1eaf5}.review-progress-panel article:last-child{border-right:0}.review-progress-panel article span{color:#78869b;font-size:9px}.review-progress-panel article strong{color:#344861;font-size:10px;line-height:16px}@media(max-width:1000px){.review-progress-panel>div{grid-template-columns:repeat(2,1fr)}}
.review-meta-grid{grid-template-columns:.65fr 1.1fr 1.35fr .65fr 1.35fr}
.severity-badge.is-P0{background:#fee4e2;color:#d92d20}.severity-badge.is-P1{background:#fff3d8;color:#b54708}.severity-badge.is-P2{background:#eaf2ff;color:#175cd3}
.issue-summary{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(280px,.6fr);gap:10px;margin-bottom:10px}.issue-summary>div{padding:12px 14px;border:1px solid #f0c7c3;border-radius:7px;background:#fff9f8}.issue-summary>div:last-child{border-color:#dce8f8;background:#fbfdff}.issue-summary span{display:block;margin-bottom:5px;color:#78869b;font-size:9px}.issue-summary strong{font-size:12px}.issue-summary p{margin:4px 0 0;color:#61708a;font-size:10px;line-height:17px}.review-editor{margin-bottom:10px;overflow:hidden}.review-editor>header{display:flex;align-items:flex-start;justify-content:space-between;margin:-14px -14px 14px;padding:12px 14px;border-bottom:1px solid #dce8f8;background:#f5f9ff}.review-editor h3{margin:0}.review-editor header p{margin:4px 0 0;color:#718098;font-size:10px}.review-editor header em{padding:3px 8px;border-radius:99px;background:#eaf2ff;color:#175cd3;font-size:9px;font-style:normal}.review-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}.review-form label{display:grid;gap:6px}.review-form label.wide{grid-column:1/-1}.review-form label>span{color:#596a83;font-size:10px}.review-form input,.review-form select,.review-form textarea{box-sizing:border-box;width:100%;min-width:0;padding:8px 9px;border:1px solid #bdd0ea;border-radius:5px;background:#fff;color:#263650;font:11px/17px inherit}.review-form input,.review-form select{height:34px}.review-form input:disabled{background:#f3f6fa;color:#718098}.review-form textarea{min-height:62px;resize:vertical}.review-readonly-result{display:grid;gap:5px}.review-readonly-result strong{font-size:12px}.review-readonly-result p{margin:0;color:#61708a;font-size:10px}.review-readonly-result em{color:#8290a7;font-size:9px;font-style:normal}.review-secondary{margin-top:10px;border:1px solid #dce8f8;border-radius:7px;background:#fff}.review-secondary summary{padding:11px 13px;color:#40516d;font-size:11px;font-weight:600;cursor:pointer}.review-secondary[open] summary{border-bottom:1px solid #e5edf8}.review-secondary>.review-evidence,.review-secondary>.review-history{padding:12px}.review-secondary .review-evidence{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.review-secondary .review-evidence article{padding:10px;border:1px solid #e1e9f4;border-radius:6px;background:#fbfdff}.review-secondary .review-evidence span{display:block;margin-bottom:6px;color:#718098;font-size:9px}.review-secondary .review-evidence strong{font-size:10px;line-height:17px}.review-secondary .review-evidence p{margin:3px 0 0;color:#718098;font-size:9px}@media(max-width:900px){.issue-summary,.review-form{grid-template-columns:1fr}.review-form label.wide{grid-column:auto}.review-secondary .review-evidence{grid-template-columns:1fr}}
/* 人工审核仅保留：异常位置、修改内容和处理方式 */
.review-workspace__head{align-items:center}.review-workspace__head-actions{display:none}.review-task-body{padding:0 18px 18px;border-color:#dce8f8;background:#fff}.review-task-body>section{padding:20px 0;border:0;border-bottom:1px solid #e6edf6;border-radius:0;background:transparent}.review-task-body>section:last-of-type{border-bottom:0}.issue-summary{display:block;margin:0}.issue-summary>header,.review-editor>header{display:flex;align-items:center;justify-content:flex-start;gap:11px;margin:0 0 16px;padding:0;border:0;background:transparent}.issue-summary>header>span,.review-editor>header>span{display:grid;flex:0 0 26px;height:26px;margin:0;place-items:center;border-radius:50%;background:#165dff;color:#fff;font-size:12px;font-weight:700}.issue-summary h2,.review-editor h2{margin:0;color:#17233b;font-size:15px}.issue-summary header p,.review-editor header p{margin:3px 0 0;color:#718098;font-size:11px}.issue-summary>.issue-location{display:flex;align-items:baseline;gap:12px;padding:0;border:0;background:transparent}.issue-location strong{font-size:14px}.issue-location span{margin:0;color:#718098;font-size:10px}.issue-summary>.issue-reason{margin:12px 0 0;padding:11px 13px;border-left:3px solid #f04438;border-radius:4px;background:#fff6f5;color:#344054;font-size:12px;line-height:20px}.issue-summary>.issue-current{margin:8px 0 0;color:#667085;font-size:11px}.review-editor{margin:0;overflow:visible}.review-form{max-width:980px}.review-form input:disabled{border-color:#e1e7ef;background:#f5f7fa;color:#475467}.schema-current input{border-color:#f4c7c3!important;background:#fff7f6!important;color:#b42318!important}.schema-correct select{border-color:#84adff;background:#f5f8ff}.schema-change-preview{display:flex;grid-column:1/-1;align-items:center;gap:18px;padding:12px 14px;border:1px solid #b8d2f5;border-radius:6px;background:#f6faff}.schema-change-preview>span{color:#667085;font-size:10px}.schema-change-preview strong{font-size:12px}.schema-change-preview b{margin:0 8px;color:#165dff}.review-readonly-result{padding-left:37px}.review-feedback{margin:16px 0 0}.review-task-footer{border-color:#dce8f8;box-shadow:0 -4px 12px rgba(26,57,104,.04)}.review-task-footer button.danger-action{border-color:#f1b8b3;color:#b42318}
.mapping-head,.mapping-row{display:grid;grid-column:1/-1;grid-template-columns:180px minmax(220px,1fr) minmax(260px,1fr);align-items:center;gap:12px}.mapping-head{padding:0 10px;color:#667085;font-size:10px}.mapping-row{padding:10px;border:1px solid #e1e8f2;border-radius:6px;background:#fbfcfe}.mapping-row code{color:#175cd3;font-size:11px}.mapping-row>span{overflow:hidden;color:#475467;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.mapping-row select{height:34px;padding:0 9px;border:1px solid #bdd0ea;border-radius:5px;background:#fff;color:#263650}
@media(max-width:900px){.issue-summary>.issue-location{align-items:flex-start;flex-direction:column;gap:4px}.decision-options>div{padding-left:0}.mapping-head{display:none}.mapping-row{grid-template-columns:1fr}}
</style>
