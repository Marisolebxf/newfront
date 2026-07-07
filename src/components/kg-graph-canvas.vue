<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import type { GraphEdgeData, GraphNodeData } from '../data/graph-presets'

const props = withDefaults(
  defineProps<{
    nodes: GraphNodeData[]
    edges: GraphEdgeData[]
    activeCategories?: string[] | null
    selectedNodeId?: string | null
    ariaLabel?: string
  }>(),
  {
    activeCategories: null,
    selectedNodeId: null,
    ariaLabel: '知识图谱',
  },
)

const emit = defineEmits<{
  selectNode: [node: GraphNodeData]
}>()

const viewBox = '0 0 760 430'
const scale = ref(1)
const panX = ref(0)
const panY = ref(0)
const isPanning = ref(false)
const panStart = ref({ x: 0, y: 0, panX: 0, panY: 0 })
const containerRef = ref<HTMLElement | null>(null)

const transform = computed(() => `translate(${panX.value} ${panY.value}) scale(${scale.value})`)

const edgeToneMap: Record<string, string> = {
  论文合作: 'is-primary',
  同事: 'is-green',
  校友: 'is-green',
  企业关联: 'is-orange',
  产业事件: 'is-purple',
  直接关系: 'is-primary',
  间接关系: 'is-purple',
}

function isEdgeActive(edge: GraphEdgeData) {
  if (!props.activeCategories?.length) return true
  return props.activeCategories.some(
    (category) => edge.category === category || edge.label.includes(category),
  )
}

function edgeClass(edge: GraphEdgeData) {
  if (!isEdgeActive(edge)) return 'platform-network-line is-dimmed'
  return `platform-network-line ${edgeToneMap[edge.category] ?? 'is-primary'}`
}

function nodeClass(node: GraphNodeData) {
  const classes = ['platform-node']
  if (node.nodeType === 'main') {
    classes.push('platform-node--main', 'is-main')
  } else {
    classes.push(`is-${node.nodeType}`)
  }
  if (props.selectedNodeId === node.id) classes.push('is-selected')
  return classes
}

function getNodeById(id: string) {
  return props.nodes.find((node) => node.id === id)
}

function getLineCoords(edge: GraphEdgeData) {
  const from = getNodeById(edge.from)
  const to = getNodeById(edge.to)
  if (!from || !to) return null
  return { x1: from.x, y1: from.y, x2: to.x, y2: to.y }
}

function handleWheel(event: WheelEvent) {
  event.preventDefault()
  const delta = event.deltaY > 0 ? -0.08 : 0.08
  scale.value = Math.min(2.2, Math.max(0.6, scale.value + delta))
}

function handlePointerDown(event: PointerEvent) {
  if ((event.target as Element).closest('.platform-node')) return
  isPanning.value = true
  panStart.value = {
    x: event.clientX,
    y: event.clientY,
    panX: panX.value,
    panY: panY.value,
  }
  containerRef.value?.setPointerCapture(event.pointerId)
}

function handlePointerMove(event: PointerEvent) {
  if (!isPanning.value) return
  panX.value = panStart.value.panX + (event.clientX - panStart.value.x)
  panY.value = panStart.value.panY + (event.clientY - panStart.value.y)
}

function handlePointerUp(event: PointerEvent) {
  isPanning.value = false
  containerRef.value?.releasePointerCapture(event.pointerId)
}

function handleNodeClick(node: GraphNodeData) {
  emit('selectNode', node)
}

function resetView() {
  scale.value = 1
  panX.value = 0
  panY.value = 0
}

onMounted(() => {
  containerRef.value?.addEventListener('wheel', handleWheel, { passive: false })
})

onUnmounted(() => {
  containerRef.value?.removeEventListener('wheel', handleWheel)
})
</script>

<template>
  <div ref="containerRef" class="kg-graph-viewport">
    <div class="kg-graph-toolbar">
      <button type="button" @click="scale = Math.min(2.2, scale + 0.15)">放大</button>
      <button type="button" @click="scale = Math.max(0.6, scale - 0.15)">缩小</button>
      <button type="button" @click="resetView">重置</button>
    </div>
    <svg
      class="kg-graph-canvas platform-svg"
      :viewBox="viewBox"
      role="img"
      :aria-label="ariaLabel"
      @pointerdown="handlePointerDown"
      @pointermove="handlePointerMove"
      @pointerup="handlePointerUp"
      @pointerleave="handlePointerUp"
    >
      <defs>
        <marker id="graph-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
          <path d="M0,0 L7,3.5 L0,7 Z" fill="#aab4c3" />
        </marker>
      </defs>
      <g :transform="transform">
        <g class="platform-network-lines">
          <line
            v-for="edge in edges"
            :key="`${edge.id}-base`"
            :x1="getLineCoords(edge)?.x1"
            :y1="getLineCoords(edge)?.y1"
            :x2="getLineCoords(edge)?.x2"
            :y2="getLineCoords(edge)?.y2"
            :class="{ 'is-dimmed': !isEdgeActive(edge) }"
          />
        </g>
        <template v-for="edge in edges" :key="edge.id">
          <line
            v-if="getLineCoords(edge)"
            :class="edgeClass(edge)"
            :x1="getLineCoords(edge)!.x1"
            :y1="getLineCoords(edge)!.y1"
            :x2="getLineCoords(edge)!.x2"
            :y2="getLineCoords(edge)!.y2"
          />
          <text
            v-if="getLineCoords(edge) && isEdgeActive(edge)"
            class="platform-edge-label"
            :x="(getLineCoords(edge)!.x1 + getLineCoords(edge)!.x2) / 2"
            :y="(getLineCoords(edge)!.y1 + getLineCoords(edge)!.y2) / 2 - 6"
          >
            {{ edge.label }}
          </text>
        </template>
        <g
          v-for="node in nodes"
          :key="node.id"
          :class="nodeClass(node)"
          :transform="`translate(${node.x} ${node.y})`"
          @click.stop="handleNodeClick(node)"
        >
          <circle :r="node.radius ?? 24" />
          <text>{{ node.label }}</text>
        </g>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.kg-graph-viewport {
  display: flex;
  flex-direction: column;
  height: calc(100% - 45px);
  min-height: 340px;
}

.kg-graph-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(191, 215, 250, 0.96);
  background: rgba(248, 252, 255, 0.92);
}

.kg-graph-toolbar button {
  height: 28px;
  padding: 0 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--primary);
  font-size: 12px;
  cursor: pointer;
}

.kg-graph-toolbar span {
  margin-left: auto;
  color: var(--text-tertiary);
  font-size: 12px;
}

.platform-svg {
  flex: 1;
  width: 100%;
  min-height: 0;
  display: block;
  cursor: grab;
  touch-action: none;
  background:
    linear-gradient(#e8f1ff 1px, transparent 1px),
    linear-gradient(90deg, #e8f1ff 1px, transparent 1px),
    linear-gradient(135deg, rgba(22, 93, 255, 0.06), rgba(20, 184, 166, 0.04)),
    #fbfdff;
  background-size: 28px 28px, 28px 28px, auto, auto;
}

.platform-svg:active {
  cursor: grabbing;
}

.platform-network-lines line {
  stroke: #c8d3e3;
  stroke-width: 1.2;
}

.platform-network-lines line.is-dimmed {
  opacity: 0.28;
}

.platform-network-line {
  stroke-width: 2.4;
  marker-end: url(#graph-arrow);
}

.platform-network-line.is-dimmed {
  opacity: 0.18;
}

.platform-network-line.is-primary { stroke: var(--graph-blue); }
.platform-network-line.is-green { stroke: var(--graph-green); }
.platform-network-line.is-orange { stroke: var(--graph-orange); }
.platform-network-line.is-purple { stroke: var(--graph-purple); }

.platform-edge-label {
  fill: var(--text-secondary);
  font-size: 11px;
  text-anchor: middle;
}

.platform-node {
  cursor: pointer;
}

.platform-node circle {
  fill: var(--node-expert, #20bfc2);
  stroke: #fff;
  stroke-width: 2;
  filter: drop-shadow(0 4px 8px rgba(53, 77, 112, 0.14));
  transition: stroke-width 0.15s ease, filter 0.15s ease;
}

.platform-node--main circle,
.platform-node.is-main circle {
  fill: var(--node-main, #1e8ff3);
}

.platform-node.is-expert circle { fill: var(--node-expert, #20bfc2); }
.platform-node.is-org circle { fill: var(--node-org, #48c914); }
.platform-node.is-company circle { fill: var(--node-company, #ffad17); }
.platform-node.is-paper circle { fill: var(--node-paper, #762bd7); }
.platform-node.is-topic circle { fill: var(--node-topic, #1f8ff1); }
.platform-node.is-project circle { fill: var(--node-project, #eb2aa3); }

.platform-node.is-selected circle {
  stroke: var(--primary);
  stroke-width: 3;
  filter: drop-shadow(0 0 0 4px rgba(22, 93, 255, 0.18));
}

.platform-node text {
  fill: #343b48;
  font-size: 13px;
  text-anchor: middle;
  dominant-baseline: hanging;
  pointer-events: none;
}

.platform-node--main text,
.platform-node.is-main text {
  fill: #fff;
  font-size: 14px;
  font-weight: 600;
  transform: translateY(-5px);
}

.platform-node:not(.platform-node--main):not(.is-main) text {
  transform: translateY(34px);
}
</style>
