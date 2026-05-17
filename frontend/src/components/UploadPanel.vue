<template>
  <div class="input-panel">
    <el-upload
      drag
      :auto-upload="false"
      :show-file-list="true"
      :limit="1"
      accept=".zip"
      :on-change="handleChange"
    >
      <el-icon class="upload-icon"><UploadFilled /></el-icon>
      <div class="upload-title">拖拽或选择 zip 项目</div>
      <template #tip>
        <div class="upload-tip">支持 Vue3 / TypeScript 前端项目，自动忽略 node_modules、dist、.git。</div>
      </template>
    </el-upload>
    <el-button class="full-button" type="primary" :loading="loading" :disabled="!selectedFile" @click="submit">
      开始分析
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { UploadFilled } from '@element-plus/icons-vue'
import type { UploadFile } from 'element-plus'
import { ref } from 'vue'

// 上传组件只维护当前选中的 zip 文件。
defineProps<{ loading: boolean }>()
const emit = defineEmits<{ upload: [file: File] }>()
const selectedFile = ref<File | null>(null)

function handleChange(file: UploadFile) {
  selectedFile.value = file.raw || null
}

function submit() {
  if (selectedFile.value) {
    emit('upload', selectedFile.value)
  }
}
</script>

