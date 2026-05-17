/// <reference types="vite/client" />

// 声明 Vue 单文件组件类型，避免 TypeScript 无法识别 .vue 导入。
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, any>
  export default component
}

