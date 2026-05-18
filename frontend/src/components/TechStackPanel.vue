<template>
  <el-card shadow="never" class="panel-card">
    <template #header>技术栈与统计</template>

    <div v-if="result" class="stack-list">
      <div class="stack-row" v-for="item in stackItems" :key="item.label">
        <span>{{ item.label }}</span>
        <el-tag effect="plain">{{ item.value }}</el-tag>
      </div>

      <div class="metric-grid">
        <div class="metric" v-for="item in summaryItems" :key="item.label">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>
    </div>

    <el-empty v-else description="分析完成后展示技术栈和项目统计" />
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TaskResult } from '../types/task'

const props = defineProps<{ result: TaskResult | null }>()

const stackItems = computed(() => {
  const stack = props.result?.tech_stack
  if (!stack) return []
  return [
    { label: '前端框架', value: stack.framework },
    { label: '开发语言', value: stack.language },
    { label: 'UI 组件库', value: stack.ui_library },
    { label: '状态管理', value: stack.state_manager },
    { label: '路由方案', value: stack.router },
    { label: '构建工具', value: stack.build_tool },
  ]
})

const summaryItems = computed(() => {
  const summary = props.result?.summary
  if (!summary) return []
  return [
    { label: '文件总数', value: summary.total_files },
    { label: '分析文件', value: summary.analyzed_files },
    { label: 'API 文件', value: summary.api_files },
    { label: '组件文件', value: summary.component_files },
    { label: '页面文件', value: summary.view_files },
    { label: 'Store 文件', value: summary.store_files },
  ]
})
</script>
