<template>
  <div class="input-panel">
    <el-input v-model="gitUrl" size="large" placeholder="https://github.com/org/repo 或 https://gitee.com/org/repo" clearable>
      <template #prefix>
        <el-icon><Link /></el-icon>
      </template>
    </el-input>
    <el-input
      v-model="accessToken"
      size="large"
      placeholder="私有仓库 Token，可选"
      type="password"
      show-password
      clearable
    >
      <template #prefix>
        <el-icon><Lock /></el-icon>
      </template>
    </el-input>
    <el-alert
      title="支持 GitHub / Gitee HTTPS 仓库。Token 只用于本次 clone，不写入本地分析结果。"
      type="info"
      :closable="false"
      show-icon
    />
    <el-button class="full-button" type="primary" :loading="loading" :disabled="!gitUrl" @click="submit">
      克隆并分析
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { Link, Lock } from '@element-plus/icons-vue'
import { ref } from 'vue'

// 仓库组件负责收集 GitHub / Gitee URL 和可选 Token。
defineProps<{ loading: boolean }>()
const emit = defineEmits<{ analyze: [payload: { gitUrl: string; accessToken?: string }] }>()
const gitUrl = ref('')
const accessToken = ref('')

function submit() {
  emit('analyze', {
    gitUrl: gitUrl.value.trim(),
    accessToken: accessToken.value.trim() || undefined,
  })
}
</script>

