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
        <ProjectImportPanel :loading="creating" :limits="limits" @upload="handleUpload" @git="handleGit" />
        <TaskProgressPanel :task="task" />
        <TechStackPanel :result="result" />
        <DownloadPanel :result="result" :loading="downloading" @download="handleDownload" />
      </div>

      <div class="right-column">
        <el-card shadow="never" class="panel-card">
          <template #header>结构化规则</template>
          <div v-if="result?.rules?.length" class="analysis-list">
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
                <div class="rule-chain">
                  <div class="rule-chain-metrics">
                    <span>置信度 {{ formatPercent(rule.confidence) }}</span>
                    <span>命中 {{ rule.match_count || 0 }} 次</span>
                  </div>
                  <div class="quality-grid">
                    <span :class="['quality-pill', qualityClass(rule.quality_score)]">质量 {{ formatScore(rule.quality_score) }}</span>
                    <span :class="['quality-pill', qualityClass(rule.stability_score)]">稳定 {{ formatScore(rule.stability_score) }}</span>
                    <span :class="['quality-pill', qualityClass(rule.consistency_score)]">一致 {{ formatScore(rule.consistency_score) }}</span>
                  </div>
                  <div v-if="rule.conflict_detected" class="rule-warning">
                    <strong>检测到冲突</strong>
                    <span>{{ rule.conflict_reason || '当前规则存在规范冲突，请先确认项目主流模式。' }}</span>
                  </div>
                  <div v-if="rule.recommendation" class="rule-recommendation">
                    {{ rule.recommendation }}
                  </div>
                  <div v-if="rule.matched_patterns?.length" class="evidence-files">
                    <code v-for="pattern in rule.matched_patterns" :key="`${rule.id}-pattern-${pattern}`">{{ pattern }}</code>
                  </div>
                  <div v-if="rule.evidence?.length" class="snippet-list">
                    <div v-for="item in rule.evidence" :key="`${rule.id}-${item.file}-${item.line}-${item.snippet}`" class="snippet-item">
                      <code>{{ item.file }}:{{ item.line }}</code>
                      <pre>{{ item.snippet }}</pre>
                    </div>
                  </div>
                </div>
              </div>
              <el-tag size="small" effect="plain">{{ rule.level }}</el-tag>
            </div>
          </div>
          <el-empty v-else :description="result ? '未返回结构化规则，请重新分析或检查后端结果' : '分析完成后展示 6 类结构化规则'" />
        </el-card>

        <RulePreviewTabs :result="result" :key="result?.project_id || 'empty-rules-preview'" />
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import DownloadPanel from '../components/DownloadPanel.vue'
import ProjectImportPanel from '../components/ProjectImportPanel.vue'
import RulePreviewTabs from '../components/RulePreviewTabs.vue'
import TaskProgressPanel from '../components/TaskProgressPanel.vue'
import TechStackPanel from '../components/TechStackPanel.vue'
import { createGitTask, downloadTaskPackage, getAppLimits, getTaskResult, getTaskStatus, toTaskError, uploadProjectZip } from '../api/task'
import type { AppLimits, TaskInfo, TaskResult } from '../types/task'

const taskId = ref('')
const task = ref<TaskInfo | null>(null)
const result = ref<TaskResult | null>(null)
const limits = ref<AppLimits | null>(null)
const creating = ref(false)
const downloading = ref(false)
let pollingTimer: number | undefined

function normalizeNumber(value: number | undefined | null) {
  return Number.isFinite(value) ? Number(value) : 0
}

function formatPercent(value: number | undefined | null) {
  return `${Math.round(normalizeNumber(value) * 100)}%`
}

function formatScore(score: number | undefined | null) {
  return Math.round(normalizeNumber(score))
}

function qualityClass(score: number | undefined | null) {
  const normalized = normalizeNumber(score)
  if (normalized >= 80) return 'quality-high'
  if (normalized >= 60) return 'quality-medium'
  return 'quality-low'
}

onMounted(async () => {
  try {
    limits.value = await getAppLimits()
  } catch (error) {
    const detail = toTaskError(error)
    ElMessage.warning(`读取系统限制失败：${detail.suggestion}`)
  }
})

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
