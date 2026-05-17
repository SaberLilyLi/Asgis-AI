import axios from 'axios'

// 统一创建 Axios 实例，页面和业务模块不得直接调用 axios。
export const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

