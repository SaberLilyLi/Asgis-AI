<template>
  <main class="app-shell">
    <section class="hero-band">
      <div>
        <p class="eyebrow">Asgis AI</p>
        <h1>工程规范分析助手</h1>
        <p class="subtitle">上传 ZIP 或输入 Git 仓库地址，自动识别前端工程模式，并生成 Cursor / Cline 可用的 AI Coding Rules。</p>
      </div>
      <el-tag v-if="taskId" type="success">Task ID: {{ taskId }}</el-tag>
    </section>

    <section class="workspace-grid">
      <div class="left-column">
        <ProjectImportPanel :loading="creating" @upload="handleUpload" @git="handleGit" />
        <TaskProgressPanel :task="task" />
        <TechStackPanel :result="result" />
        <DownloadPanel :result="result" :loading="downloading" @download="handleDownload" />
      </div>

      <div class="right-column">
        <el-card shadow="never" class="panel-card">
          <template #header>结构化规则</template>
          <div v-if="result" class="analysis-list">
            <div v-for="rule in result.rules" :key="rule.id" class="analysis-item">
              <div>
                <strong>{{ rule.category }}：{{ rule.title }}</strong>
                <p>{{ rule.content }}</p>
                <div class="rule-evidence">
                  <span>证据文件</span>
                  <div v-if="rule.evidence_files?.length" class="evidence-files">
                    <code v-for="file in rule.evidence_files" :key="`${rule.id}-${file}`">{{ file }}</code>
                  </div>
                  <em v-else>未识别到明确证据，需参考项目已有模式</em>
                </div>
              </div>
              <el-tag size="small" effect="plain">{{ rule.level }}</el-tag>
            </div>
          </div>
          <el-empty v-else description="分析完成后展示 6 类结构化规则" />
        </el-card>

        <RulePreviewTabs :result="result" />
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onBeforeUnmount, ref } from 'vue'
import DownloadPanel from '../components/DownloadPanel.vue'
import ProjectImportPanel from '../components/ProjectImportPanel.vue'
import RulePreviewTabs from '../components/RulePreviewTabs.vue'
import TaskProgressPanel from '../components/TaskProgressPanel.vue'
import TechStackPanel from '../components/TechStackPanel.vue'
import { createGitTask, downloadTaskPackage, getTaskResult, getTaskStatus, toTaskError, uploadProjectZip } from '../api/task'
import type { TaskInfo, TaskResult } from '../types/task'

const taskId = ref('')
const task = ref<TaskInfo | null>(null)
const result = ref<TaskResult | null>(null)
const creating = ref(false)
const downloading = ref(false)
let pollingTimer: number | undefined

async function handleUpload(file: File) {
  await createTask(() => uploadProjectZip(file))
}

async function handleGit(payload: { gitUrl: string; accessToken?: string }) {
  await createTask(() => createGitTask({ git_url: payload.gitUrl, access_token: payload.accessToken }))
}

async function createTask(action: () => Promise<{ task_id: string }>) {
  stopPolling()
  creating.value = true
  task.value = null
  result.value = null
  try {
    const created = await action()
    taskId.value = created.task_id
    ElMessage.success('分析任务已创建')
    await pollTask(created.task_id)
    pollingTimer = window.setInterval(() => {
      void pollTask(created.task_id)
    }, 1200)
  } catch (error) {
    const detail = toTaskError(error)
    ElMessage.error(`${detail.message}：${detail.suggestion}`)
    creating.value = false
  }
}

async function pollTask(id: string) {
  try {
    const current = await getTaskStatus(id)
    task.value = current
    if (current.status === 'success') {
      stopPolling()
      creating.value = false
      result.value = await getTaskResult(id)
      ElMessage.success('工程规范分析完成')
    }
    if (current.status === 'failed') {
      stopPolling()
      creating.value = false
      ElMessage.error(current.error_message || current.message)
    }
  } catch (error) {
    const detail = toTaskError(error)
    stopPolling()
    creating.value = false
    ElMessage.error(`${detail.message}：${detail.suggestion}`)
  }
}

async function handleDownload() {
  if (!taskId.value || !result.value) return
  downloading.value = true
  try {
    const blob = await downloadTaskPackage(taskId.value)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `asgis-rules-${result.value.project_name}-${taskId.value}.zip`
    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    const detail = toTaskError(error)
    ElMessage.error(`${detail.message}：${detail.suggestion}`)
  } finally {
    downloading.value = false
  }
}

function stopPolling() {
  if (pollingTimer) {
    window.clearInterval(pollingTimer)
    pollingTimer = undefined
  }
}

onBeforeUnmount(stopPolling)
</script>
