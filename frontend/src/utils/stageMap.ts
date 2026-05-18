import type { TaskStage, TaskStatus } from '../types/task'

const stageLabelMap: Record<TaskStage, string> = {
  uploading: '上传中',
  cloning: '克隆仓库',
  scanning: '扫描目录',
  analyzing: '分析规范',
  generating: '生成规则',
  packaging: '打包规则',
  done: '已完成',
  error: '已失败',
}

const statusLabelMap: Record<TaskStatus, string> = {
  queued: '排队中',
  running: '进行中',
  success: '已完成',
  failed: '已失败',
}

export function getStageLabel(stage: TaskStage | string): string {
  return stageLabelMap[stage as TaskStage] || '处理中'
}

export function getStatusLabel(status: TaskStatus | string): string {
  return statusLabelMap[status as TaskStatus] || '未知'
}
