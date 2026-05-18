import axios from 'axios'
import {
  createGitTask,
  downloadTaskPackage,
  getTaskStatus,
  uploadProjectZip,
} from '../api/task'
import type { AnalysisResult, ProjectStatus, RulesResponse } from './legacy-types'
import type { TaskErrorDetail } from '../types/task'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001',
  timeout: 120000,
})

export interface AnalyzeResponse {
  project_id: string
  status: string
  message: string
  code?: string
}

export type { AnalysisResult, ProjectStatus, RulesResponse, TaskErrorDetail }
export { createGitTask, downloadTaskPackage, getTaskResult, getTaskStatus, toTaskError, uploadProjectZip } from '../api/task'

export async function uploadProject(file: File): Promise<AnalyzeResponse> {
  const result = await uploadProjectZip(file)
  return {
    project_id: result.task_id,
    status: 'queued',
    message: '项目已上传，正在排队分析',
  }
}

export async function analyzeRepo(gitUrl: string, accessToken?: string): Promise<AnalyzeResponse> {
  const result = await createGitTask({ git_url: gitUrl, access_token: accessToken })
  return {
    project_id: result.task_id,
    status: 'queued',
    message: '仓库分析任务已创建，正在排队分析',
  }
}

export async function generateRules(projectId: string): Promise<RulesResponse> {
  const { data } = await api.post<RulesResponse>('/generate_rules', { project_id: projectId })
  return data
}

export async function getProjectStatus(projectId: string): Promise<ProjectStatus> {
  const task = await getTaskStatus(projectId)
  return {
    project_id: task.task_id,
    status: task.status,
    stage: task.stage,
    progress: task.progress,
    message: task.message,
    code: task.error_code || undefined,
    error: task.error_message || undefined,
    updated_at: task.updated_at,
  }
}

export async function downloadRulesPackage(projectId: string): Promise<Blob> {
  return downloadTaskPackage(projectId)
}
