<template>
  <el-card shadow="never" class="panel-card rule-card">
    <template #header>
      <div class="card-header">
        <span>Rules 预览</span>
        <div class="rule-actions">
          <el-button :icon="CopyDocument" :disabled="!currentContent" @click="copyCurrent">复制</el-button>
          <el-button :icon="Download" :disabled="!currentContent" @click="downloadCurrent">下载</el-button>
          <el-button :icon="Folder" :disabled="!projectId" @click="downloadPackage">全部</el-button>
        </div>
      </div>
    </template>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="rules.md" name="rules_markdown" />
      <el-tab-pane label="development-flow.md" name="development_flow" />
      <el-tab-pane label=".clinerules" name="cline_rules" />
      <el-tab-pane label="cursor-rules.md" name="cursor_rules" />
    </el-tabs>
    <div class="rule-purpose">{{ purposeMap[activeTab] }}</div>
    <pre v-if="currentContent" class="rule-preview">{{ currentContent }}</pre>
    <el-empty v-else description="生成 Rules 后在这里预览" />
  </el-card>
</template>

<script setup lang="ts">
import { CopyDocument, Download, Folder } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, ref } from 'vue'
import { downloadRulesPackage, type RulesResponse } from '../services/api'

// RulePanel 负责预览、复制和下载三类规则文件。
const props = defineProps<{ rules: RulesResponse | null; projectId?: string }>()
const activeTab = ref<keyof RulesResponse>('rules_markdown')
const fileNameMap: Record<keyof RulesResponse, string> = {
  rules_markdown: 'rules.md',
  development_flow: 'development-flow.md',
  cline_rules: '.clinerules',
  cursor_rules: 'cursor-rules.md',
}
const purposeMap: Record<keyof RulesResponse, string> = {
  rules_markdown: '团队工程规范手册：全面沉淀 API、状态、页面、组件、hooks、权限和工程组织规范。',
  development_flow: '开发流程入口：只引用规范章节，不重复具体规则，后续开发应按该流程执行。',
  cline_rules: 'Cline 执行约束：短、硬、命令式，强调修改顺序、必须遵守和禁止行为。',
  cursor_rules: 'Cursor 中文上下文规则：强调文件模式、补全边界和代码生成时的检查清单。',
}

const currentContent = computed(() => props.rules?.[activeTab.value] || '')

async function copyCurrent() {
  await navigator.clipboard.writeText(currentContent.value)
  ElMessage.success('已复制到剪贴板')
}

function downloadCurrent() {
  const blob = new Blob([currentContent.value], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileNameMap[activeTab.value]
  link.click()
  URL.revokeObjectURL(url)
}

async function downloadPackage() {
  if (!props.projectId) return
  const blob = await downloadRulesPackage(props.projectId)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `asgis-rules-${props.projectId}.zip`
  link.click()
  URL.revokeObjectURL(url)
}
</script>
