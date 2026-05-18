<template>
  <el-card shadow="never" class="panel-card">
    <template #header>规则包下载</template>
    <div class="download-panel">
      <div>
        <strong>{{ result?.project_name || '等待分析结果' }}</strong>
        <p>下载 rules.md、development-flow.md、.clinerules、cursor-rules.md。</p>
      </div>
      <el-button type="primary" :icon="Download" :loading="loading" :disabled="!result" @click="$emit('download')">
        下载规则包
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { Download } from '@element-plus/icons-vue'
import type { TaskResult } from '../types/task'

defineProps<{ result: TaskResult | null; loading: boolean }>()
defineEmits<{ download: [] }>()
</script>
