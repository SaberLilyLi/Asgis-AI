<template>
  <el-card shadow="never" class="panel-card">
    <template #header>项目导入</template>
    <el-tabs v-model="mode" stretch>
      <el-tab-pane label="上传 ZIP" name="zip">
        <div class="input-panel">
          <el-upload
            drag
            :auto-upload="false"
            :show-file-list="true"
            :limit="1"
            accept=".zip"
            :on-change="handleFileChange"
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="upload-title">拖拽或选择 ZIP 项目</div>
            <template #tip>
              <div class="upload-tip">
                ZIP 最大 {{ limits?.max_upload_mb || 100 }}MB，压缩前建议删除 node_modules、dist、.git。
              </div>
            </template>
          </el-upload>
          <el-button class="full-button" type="primary" :loading="loading" :disabled="!selectedFile" @click="submitZip">
            开始分析
          </el-button>
        </div>
      </el-tab-pane>

      <el-tab-pane label="Git 仓库" name="git">
        <div class="input-panel">
          <el-input v-model="gitUrl" size="large" placeholder="https://github.com/org/repo 或 https://gitee.com/org/repo" clearable>
            <template #prefix>
              <el-icon><Link /></el-icon>
            </template>
          </el-input>
          <el-input v-model="accessToken" size="large" placeholder="私有仓库 Token，可选" type="password" show-password clearable>
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
          <el-alert
            :title="`Git 仓库最大 ${limits?.max_repo_mb || 200}MB，clone 超时 ${limits?.clone_timeout_seconds || 180} 秒。Token 只用于本次 clone，不写入分析结果。`"
            type="info"
            :closable="false"
            show-icon
          />
          <el-button class="full-button" type="primary" :loading="loading" :disabled="!gitUrl" @click="submitGit">
            克隆并分析
          </el-button>
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup lang="ts">
import { Link, Lock, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { ref } from 'vue'
import type { AppLimits } from '../types/task'

const props = defineProps<{ loading: boolean; limits: AppLimits | null }>()
const emit = defineEmits<{
  upload: [file: File]
  git: [payload: { gitUrl: string; accessToken?: string }]
}>()

const mode = ref<'zip' | 'git'>('zip')
const selectedFile = ref<File | null>(null)
const gitUrl = ref('')
const accessToken = ref('')

function handleFileChange(file: UploadFile) {
  const rawFile = file.raw || null
  if (rawFile && props.limits && rawFile.size > props.limits.max_upload_mb * 1024 * 1024) {
    selectedFile.value = null
    ElMessage.warning(`ZIP 文件超过 ${props.limits.max_upload_mb}MB，请精简后重新上传。`)
    return
  }
  selectedFile.value = rawFile
}

function submitZip() {
  if (!selectedFile.value) return
  if (props.limits && selectedFile.value.size > props.limits.max_upload_mb * 1024 * 1024) {
    ElMessage.warning(`ZIP 文件超过 ${props.limits.max_upload_mb}MB，请精简后重新上传。`)
    return
  }
  emit('upload', selectedFile.value)
}

function submitGit() {
  emit('git', {
    gitUrl: gitUrl.value.trim(),
    accessToken: accessToken.value.trim() || undefined,
  })
}
</script>
