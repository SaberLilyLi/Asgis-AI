import { defineStore } from 'pinia'

// 用户全局状态统一放在 Pinia store 中。
export const useUserStore = defineStore('user', {
  state: () => ({
    name: '',
    permissions: [] as string[],
  }),
})

