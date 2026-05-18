import axios from 'axios'
import type { TaskCreateResponse, TaskErrorDetail, TaskInfo, TaskResult } from '../types/task'

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
  return data
}

export async function downloadTaskPackage(taskId: string): Promise<Blob> {
  const { data } = await api.get(`/api/tasks/${taskId}/download`, { responseType: 'blob' })
  return data
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
