<template>
  <el-card shadow="never" class="panel-card">
    <template #header>
      <div class="card-header">
        <span>分析进度</span>
        <el-tag v-if="task" :type="statusType">{{ statusLabel }}</el-tag>
      </div>
    </template>

    <div v-if="task" class="progress-panel">
      <div class="progress-header">
        <span>{{ task.message }}</span>
      </div>
      <el-steps :active="activeStep" :finish-status="task.status === 'failed' ? 'error' : 'success'" simple>
        <el-step title="导入" />
        <el-step title="扫描" />
        <el-step title="分析" />
        <el-step title="生成" />
        <el-step title="完成" />
      </el-steps>
      <el-progress :percentage="task.progress" :status="progressStatus" />
      <div class="stage-row">
        <span>当前阶段</span>
        <strong>{{ stageLabel }}</strong>
      </div>
      <el-alert
        v-if="task.status === 'failed'"
        :title="task.error_code || '分析失败'"
        :description="task.error_message || task.message"
        type="error"
        :closable="false"
        show-icon
      />
    </div>

    <el-empty v-else description="提交项目后显示任务状态和分析进度" />
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TaskInfo } from '../types/task'
import { getStageLabel, getStatusLabel } from '../utils/stageMap'

const props = defineProps<{ task: TaskInfo | null }>()

const statusLabel = computed(() => (props.task ? getStatusLabel(props.task.status) : ''))
const stageLabel = computed(() => (props.task ? getStageLabel(props.task.stage) : ''))
const statusType = computed(() => {
  if (props.task?.status === 'success') return 'success'
  if (props.task?.status === 'failed') return 'danger'
  return 'info'
})
const progressStatus = computed(() => {
  if (props.task?.status === 'success') return 'success'
  if (props.task?.status === 'failed') return 'exception'
  return undefined
})
const activeStep = computed(() => {
  const stage = props.task?.stage
  if (stage === 'uploading' || stage === 'cloning') return 1
  if (stage === 'scanning') return 2
  if (stage === 'analyzing') return 3
  if (stage === 'generating' || stage === 'packaging') return 4
  if (stage === 'done') return 5
  if (stage === 'error') return Math.max(1, Math.ceil((props.task?.progress || 20) / 25))
  return 0
})
</script>
