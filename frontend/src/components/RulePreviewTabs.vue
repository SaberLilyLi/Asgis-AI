<template>
  <el-card shadow="never" class="panel-card rule-card">
    <template #header>
      <div class="card-header">
        <span>规则文件预览</span>
        <el-button :icon="CopyDocument" :disabled="!currentContent" @click="copyCurrent">复制</el-button>
      </div>
    </template>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="rules.md" name="rules_md" />
      <el-tab-pane label="development-flow.md" name="development_flow_md" />
      <el-tab-pane label=".clinerules" name="cline_rules" />
      <el-tab-pane label="cursor-rules.md" name="cursor_rules" />
    </el-tabs>
    <pre v-if="currentContent" :key="previewKey" class="rule-preview">{{ currentContent }}</pre>
    <el-empty v-else description="分析成功后展示 4 个规则文件" />
  </el-card>
</template>

<script setup lang="ts">
import { CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, ref, watch } from 'vue'
import type { TaskResult } from '../types/task'

type RuleFileKey = keyof TaskResult['files']

const props = defineProps<{ result: TaskResult | null }>()
const activeTab = ref<RuleFileKey>('rules_md')
const fileKeys: RuleFileKey[] = ['rules_md', 'development_flow_md', 'cline_rules', 'cursor_rules']
const currentContent = computed(() => props.result?.files?.[activeTab.value] || '')
const previewKey = computed(() => `${props.result?.project_id || 'empty'}-${activeTab.value}`)

watch(
  () => props.result?.files,
  (files) => {
    const firstAvailable = fileKeys.find((key) => files?.[key])
    activeTab.value = firstAvailable || 'rules_md'
  },
  { immediate: true },
)

async function copyCurrent() {
  await navigator.clipboard.writeText(currentContent.value)
  ElMessage.success('已复制到剪贴板')
}
</script>
