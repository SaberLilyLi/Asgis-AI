<template>
  <el-card shadow="never" class="panel-card">
    <template #header>技术栈</template>
    <div v-if="analysis" class="stack-list">
      <div v-for="(value, key) in analysis.tech_stack" :key="key" class="stack-row">
        <span>{{ labelMap[key] || key }}</span>
        <el-tag effect="plain">{{ value }}</el-tag>
      </div>
    </div>
    <el-empty v-else description="暂无技术栈识别结果" />
  </el-card>
</template>

<script setup lang="ts">
import type { AnalysisResult } from '../services/api'

// 技术栈标签映射，保持界面文案稳定。
defineProps<{ analysis: AnalysisResult | null }>()
const labelMap: Record<string, string> = {
  project_type: '项目类型',
  frontend: '前端框架',
  language: '开发语言',
  ui: 'UI 组件库',
  state: '状态管理',
  http: 'HTTP 客户端',
  build: '构建工具',
}
</script>

