<template>
  <main class="app-shell">
    <section class="hero-band">
      <div>
        <p class="eyebrow">Asgis AI</p>
        <h1>工程规范分析助手</h1>
        <p class="subtitle">扫描 Vue / React / 小程序 / uni-app 项目，抽取工程习惯，并生成可约束 Cline / Cursor 的 AI Coding Rules。</p>
      </div>
      <el-button type="primary" :loading="rulesLoading" :disabled="!canGenerateRules" @click="handleGenerateRules">
        生成 Rules
      </el-button>
    </section>

    <section class="workspace-grid">
      <div class="left-column">
        <el-card shadow="never" class="panel-card">
          <el-tabs v-model="activeMode" stretch>
            <el-tab-pane label="上传项目" name="upload">
              <UploadPanel :loading="analyzeLoading" @upload="handleUpload" />
            </el-tab-pane>
            <el-tab-pane label="Git 仓库" name="repo">
              <RepoPanel :loading="analyzeLoading" @analyze="handleRepoAnalyze" />
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="card-header">
              <span>分析进度</span>
              <el-button v-if="canRetry" size="small" @click="retryLastTask">重新分析</el-button>
            </div>
          </template>
          <div v-if="projectStatus" class="progress-panel">
            <div class="progress-header">
              <el-tag :type="statusTagType">{{ statusLabel }}</el-tag>
              <span>{{ projectStatus.message }}</span>
            </div>
            <el-steps :active="activeStep" :finish-status="stepFinishStatus" simple>
              <el-step title="提交" />
              <el-step :title="activeMode === 'repo' ? '克隆' : '解压'" />
              <el-step title="扫描" />
              <el-step title="抽取" />
              <el-step title="完成" />
            </el-steps>
            <el-progress :percentage="projectStatus.progress" :status="progressStatus" />
            <div class="stage-row">
              <span>当前阶段</span>
              <strong>{{ stageLabel }}</strong>
            </div>
            <el-alert
              v-if="projectStatus.status === 'failed'"
              :title="failureTitle"
              :description="failureDescription"
              type="error"
              :closable="false"
              show-icon
            />
          </div>
          <el-empty v-else description="提交项目后显示 clone、扫描、分析进度" />
        </el-card>

        <TechStackPanel :analysis="analysis" />
        <ProjectStats :analysis="analysis" />
        <EvidencePanel :analysis="analysis" />
      </div>

      <div class="right-column">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="card-header">
              <span>分析结果</span>
              <el-tag v-if="projectId" type="success">Project ID: {{ projectId }}</el-tag>
            </div>
          </template>
          <div v-if="analysis" class="analysis-list">
            <div v-for="item in analysis.recommendations" :key="item" class="analysis-item">{{ item }}</div>
          </div>
          <el-empty v-else description="上传项目或输入 GitHub / Gitee 仓库后开始分析" />
        </el-card>

        <RulePanel :rules="rules" :project-id="projectId" />
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onBeforeUnmount, ref } from 'vue'
import EvidencePanel from '../components/EvidencePanel.vue'
import ProjectStats from '../components/ProjectStats.vue'
import RepoPanel from '../components/RepoPanel.vue'
import RulePanel from '../components/RulePanel.vue'
import TechStackPanel from '../components/TechStackPanel.vue'
import UploadPanel from '../components/UploadPanel.vue'
import {
  analyzeRepo,
  generateRules,
  getProjectStatus,
  uploadProject,
  type AnalyzeResponse,
  type AnalysisResult,
  type ProjectStatus,
  type RulesResponse,
} from '../services/api'

const activeMode = ref<'upload' | 'repo'>('upload')
const analyzeLoading = ref(false)
const rulesLoading = ref(false)
const projectId = ref('')
const analysis = ref<AnalysisResult | null>(null)
const rules = ref<RulesResponse | null>(null)
const projectStatus = ref<ProjectStatus | null>(null)
const lastRepoPayload = ref<{ gitUrl: string; accessToken?: string } | null>(null)
const lastUploadFile = ref<File | null>(null)
let pollingTimer: number | undefined

const canGenerateRules = computed(() => Boolean(projectId.value && analysis.value && projectStatus.value?.status === 'success'))
const canRetry = computed(() => projectStatus.value?.status === 'failed' && Boolean(lastRepoPayload.value || lastUploadFile.value))
const statusLabel = computed(() => {
  const status = projectStatus.value?.status
  if (status === 'queued') return '排队中'
  if (status === 'running') return '分析中'
  if (status === 'success') return '已完成'
  if (status === 'failed') return '失败'
  return '未开始'
})
const statusTagType = computed(() => {
  if (projectStatus.value?.status === 'success') return 'success'
  if (projectStatus.value?.status === 'failed') return 'danger'
  return 'info'
})
const progressStatus = computed(() => {
  if (projectStatus.value?.status === 'success') return 'success'
  if (projectStatus.value?.status === 'failed') return 'exception'
  return undefined
})
const stepFinishStatus = computed(() => (projectStatus.value?.status === 'failed' ? 'error' : 'success'))
const activeStep = computed(() => {
  const stage = projectStatus.value?.stage
  if (stage === 'queued') return 1
  if (stage === 'cloning' || stage === 'extracting') return 2
  if (stage === 'scanning') return 3
  if (stage === 'analyzing') return 4
  if (stage === 'completed') return 5
  if (stage === 'failed') return Math.max(1, Math.ceil((projectStatus.value?.progress || 20) / 25))
  return 0
})
const stageLabel = computed(() => {
  const map: Record<string, string> = {
    queued: '等待开始',
    extracting: '解压 zip',
    cloning: '克隆仓库',
    scanning: '扫描目录',
    analyzing: '抽取规范',
    completed: '分析完成',
    failed: '分析失败',
  }
  return map[projectStatus.value?.stage || ''] || '准备中'
})
const failureTitle = computed(() => {
  const code = projectStatus.value?.code ? ` [${projectStatus.value.code}]` : ''
  return `${projectStatus.value?.message || '分析失败'}${code}`
})
const failureDescription = computed(() => projectStatus.value?.suggestion || projectStatus.value?.error || '请检查项目内容、仓库地址或网络状态后重试。')

async function handleUpload(file: File) {
  activeMode.value = 'upload'
  lastUploadFile.value = file
  lastRepoPayload.value = null
  await startAnalyzeTask(() => uploadProject(file))
}

async function handleRepoAnalyze(payload: { gitUrl: string; accessToken?: string }) {
  activeMode.value = 'repo'
  lastRepoPayload.value = payload
  lastUploadFile.value = null
  await startAnalyzeTask(() => analyzeRepo(payload.gitUrl, payload.accessToken))
}

async function retryLastTask() {
  if (lastRepoPayload.value) {
    const payload = lastRepoPayload.value
    await startAnalyzeTask(() => analyzeRepo(payload.gitUrl, payload.accessToken))
    return
  }
  if (lastUploadFile.value) {
    await startAnalyzeTask(() => uploadProject(lastUploadFile.value as File))
  }
}

async function startAnalyzeTask(createTask: () => Promise<AnalyzeResponse>) {
  stopPolling()
  analyzeLoading.value = true
  analysis.value = null
  rules.value = null
  projectStatus.value = null
  try {
    const result = await createTask()
    projectId.value = result.project_id
    ElMessage.success(result.message)
    await pollProjectStatus(result.project_id)
    pollingTimer = window.setInterval(() => {
      void pollProjectStatus(result.project_id)
    }, 1200)
  } catch (error: any) {
    analyzeLoading.value = false
    const detail = error?.response?.data?.detail
    ElMessage.error(detail?.message || detail || '分析任务创建失败')
  }
}

async function pollProjectStatus(currentProjectId: string) {
  try {
    const status = await getProjectStatus(currentProjectId)
    projectStatus.value = status
    if (status.status === 'success') {
      analysis.value = status.analysis || null
      analyzeLoading.value = false
      stopPolling()
      ElMessage.success('工程规范分析完成')
    }
    if (status.status === 'failed') {
      analyzeLoading.value = false
      stopPolling()
      ElMessage.error(status.message || '工程规范分析失败')
    }
  } catch (error: any) {
    analyzeLoading.value = false
    stopPolling()
    const detail = error?.response?.data?.detail
    ElMessage.error(detail?.message || detail || '查询分析状态失败')
  }
}

function stopPolling() {
  if (pollingTimer) {
    window.clearInterval(pollingTimer)
    pollingTimer = undefined
  }
}

async function handleGenerateRules() {
  if (!projectId.value) return
  rulesLoading.value = true
  try {
    rules.value = await generateRules(projectId.value)
    ElMessage.success('Rules 生成完成')
  } catch (error: any) {
    const detail = error?.response?.data?.detail
    ElMessage.error(detail?.message || detail || 'Rules 生成失败')
  } finally {
    rulesLoading.value = false
  }
}

onBeforeUnmount(stopPolling)
</script>
