<template>
  <el-card shadow="never" class="panel-card">
    <template #header>规范证据</template>
    <div v-if="analysis" class="evidence-list">
      <div v-for="item in evidenceItems" :key="item.title" class="evidence-item">
        <div class="evidence-title">
          <span>{{ item.title }}</span>
          <el-tag size="small" effect="plain">{{ item.files.length }}</el-tag>
        </div>
        <div v-if="item.files.length" class="evidence-files">
          <code v-for="file in item.files" :key="file">{{ file }}</code>
        </div>
        <span v-else class="empty-evidence">未识别到明确来源，新增代码需遵循项目已有模式</span>
      </div>
    </div>
    <el-empty v-else description="分析完成后展示规则来源文件" />
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AnalysisResult } from '../services/api'

const props = defineProps<{ analysis: AnalysisResult | null }>()

const evidenceItems = computed(() => {
  const patterns = props.analysis?.patterns || {}
  return [
    { title: 'API 封装依据', files: collect(patterns.api?.request_files, patterns.api?.api_files) },
    { title: '状态管理依据', files: collect(patterns.state?.pinia_files, patterns.state?.redux_files, patterns.state?.zustand_files, patterns.state?.store_files) },
    { title: '页面结构依据', files: collect(patterns.pages?.index_pages, patterns.pages?.view_files) },
    { title: '组件封装依据', files: collect(patterns.components?.base_components, patterns.components?.component_files) },
    { title: 'hooks/composables 依据', files: collect(patterns.composables?.composable_files) },
    { title: '权限逻辑依据', files: collect(patterns.permission?.permission_files) },
    { title: '小程序/uni-app 依据', files: collect(patterns.miniapp?.app_files, patterns.miniapp?.page_config_files) },
  ]
})

function collect(...groups: unknown[]): string[] {
  const result = groups.flatMap((group) => (Array.isArray(group) ? group : []))
  return Array.from(new Set(result.filter((item): item is string => typeof item === 'string'))).slice(0, 12)
}
</script>

