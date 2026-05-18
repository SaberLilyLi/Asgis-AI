export type TaskStatus = 'queued' | 'running' | 'success' | 'failed'
export type TaskStage = 'uploading' | 'cloning' | 'scanning' | 'analyzing' | 'generating' | 'packaging' | 'done' | 'error'

export interface TaskInfo {
  task_id: string
  status: TaskStatus
  stage: TaskStage
  progress: number
  message: string
  error_code: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface TechStack {
  framework: string
  language: string
  ui_library: string
  state_manager: string
  router: string
  build_tool: string
}

export interface ProjectSummary {
  total_files: number
  analyzed_files: number
  api_files: number
  component_files: number
  view_files: number
  store_files: number
}

export interface RuleItem {
  id: string
  category: string
  title: string
  description: string
  level: 'required' | 'important' | 'optional'
  content: string
  evidence_files?: string[]
}

export interface TaskResult {
  project_id: string
  project_name: string
  source_type: 'zip' | 'git'
  tech_stack: TechStack
  summary: ProjectSummary
  rules: RuleItem[]
  files: {
    rules_md: string
    development_flow_md: string
    cline_rules: string
    cursor_rules: string
  }
  download_url: string
}

export interface TaskErrorDetail {
  code: string
  message: string
  suggestion: string
}

export interface TaskCreateResponse {
  task_id: string
}
