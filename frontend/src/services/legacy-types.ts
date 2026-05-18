export interface AnalysisResult {
  tech_stack: Record<string, unknown>
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
