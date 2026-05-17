import axios from 'axios'

// 后端 API 基础地址，可通过 VITE_API_BASE_URL 覆盖。
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

export interface AnalysisResult {
  tech_stack: Record<string, string>
  stats: Record<string, unknown>
  patterns: Record<string, any>
  recommendations: string[]
}

export interface RulesResponse {
  rules_markdown: string
  development_flow: string
  cline_rules: string
  cursor_rules: string
}

export interface ProjectStatus {
  project_id: string
  status: 'queued' | 'running' | 'success' | 'failed'
  stage: string
  progress: number
  message: string
  code?: string
  suggestion?: string
  error?: string
  analysis?: AnalysisResult
  updated_at?: string
}

// 上传 zip 项目并触发分析。
export async function uploadProject(file: File): Promise<AnalyzeResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<AnalyzeResponse>('/upload_project', formData)
  return data
}

// 提交 GitHub 仓库地址并触发分析。
export async function analyzeRepo(gitUrl: string, accessToken?: string): Promise<AnalyzeResponse> {
  const { data } = await api.post<AnalyzeResponse>('/analyze_repo', { git_url: gitUrl, access_token: accessToken })
  return data
}

// 根据 project_id 生成 rules.md、.clinerules、cursor-rules.md。
export async function generateRules(projectId: string): Promise<RulesResponse> {
  const { data } = await api.post<RulesResponse>('/generate_rules', { project_id: projectId })
  return data
}

// 轮询项目分析状态，用于展示 clone、扫描、分析等阶段进度。
export async function getProjectStatus(projectId: string): Promise<ProjectStatus> {
  const { data } = await api.get<ProjectStatus>(`/project_status/${projectId}`)
  return data
}

// 下载全部规则文件 zip 包。
export async function downloadRulesPackage(projectId: string): Promise<Blob> {
  const { data } = await api.get(`/download_rules_package/${projectId}`, { responseType: 'blob' })
  return data
}
