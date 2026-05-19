import axios from 'axios'
import type { AppLimits, TaskCreateResponse, TaskErrorDetail, TaskInfo, TaskResult } from '../types/task'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001',
  timeout: 120000,
})

export interface GitTaskPayload {
  git_url: string
  access_token?: string
}

export async function uploadProjectZip(file: File): Promise<TaskCreateResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<TaskCreateResponse>('/api/tasks/upload', formData)
  return data
}

export async function createGitTask(payload: GitTaskPayload): Promise<TaskCreateResponse> {
  const { data } = await api.post<TaskCreateResponse>('/api/tasks/git', payload)
  return data
}

export async function getTaskStatus(taskId: string): Promise<TaskInfo> {
  const { data } = await api.get<TaskInfo>(`/api/tasks/${taskId}`)
  return data
}

export async function getTaskResult(taskId: string): Promise<TaskResult> {
  const { data } = await api.get<TaskResult>(`/api/tasks/${taskId}/result`)
  return normalizeTaskResult(data)
}

export async function downloadTaskPackage(taskId: string): Promise<Blob> {
  const { data } = await api.get(`/api/tasks/${taskId}/download`, { responseType: 'blob' })
  return data
}

export async function getAppLimits(): Promise<AppLimits> {
  const { data } = await api.get<AppLimits>('/api/config/limits')
  return data
}

function normalizeTaskResult(result: TaskResult): TaskResult {
  return {
    ...result,
    rules: (result.rules || []).map((rule) => ({
      ...rule,
      evidence: rule.evidence || [],
      matched_patterns: rule.matched_patterns || [],
      match_count: rule.match_count || 0,
      confidence: rule.confidence || 0,
      quality_score: rule.quality_score || 0,
      stability_score: rule.stability_score || 0,
      consistency_score: rule.consistency_score || 0,
      conflict_detected: rule.conflict_detected || false,
      conflict_reason: rule.conflict_reason || null,
      recommendation: rule.recommendation || '',
      evidence_files: rule.evidence_files || [],
    })),
    files: {
      rules_md: result.files?.rules_md || '',
      development_flow_md: result.files?.development_flow_md || '',
      cline_rules: result.files?.cline_rules || '',
      cursor_rules: result.files?.cursor_rules || '',
    },
  }
}

export function toTaskError(error: any): TaskErrorDetail {
  const detail = error?.response?.data?.detail
  if (detail && typeof detail === 'object') {
    return {
      code: detail.code || 'UNKNOWN_ERROR',
      message: detail.message || '请求失败',
      suggestion: detail.suggestion || '请稍后重试。',
    }
  }
  return {
    code: 'UNKNOWN_ERROR',
    message: detail?.message || detail || '请求失败',
    suggestion: '请稍后重试。',
  }
}
