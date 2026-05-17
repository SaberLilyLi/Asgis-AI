<template>
  <el-card shadow="never" class="panel-card">
    <template #header>项目统计</template>
    <div v-if="analysis" class="metric-grid">
      <div class="metric">
        <span>文件数</span>
        <strong>{{ analysis.stats.file_count || 0 }}</strong>
      </div>
      <div class="metric">
        <span>代码行数</span>
        <strong>{{ analysis.stats.line_count || 0 }}</strong>
      </div>
      <div class="metric">
        <span>Vue 文件</span>
        <strong>{{ analysis.stats.vue_files || 0 }}</strong>
      </div>
      <div class="metric">
        <span>React 文件</span>
        <strong>{{ analysis.stats.react_files || 0 }}</strong>
      </div>
      <div class="metric">
        <span>小程序文件</span>
        <strong>{{ analysis.stats.miniapp_files || 0 }}</strong>
      </div>
      <div class="metric">
        <span>TS 文件</span>
        <strong>{{ analysis.stats.typescript_files || 0 }}</strong>
      </div>
    </div>
    <el-empty v-else description="暂无统计数据" />
  </el-card>
</template>

<script setup lang="ts">
import type { AnalysisResult } from '../services/api'

// 展示扫描得到的项目基础统计。
defineProps<{ analysis: AnalysisResult | null }>()
</script>

