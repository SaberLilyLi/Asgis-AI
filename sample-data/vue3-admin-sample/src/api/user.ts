import { request } from './request'

// 用户 API 统一通过 request 封装，便于拦截器和错误处理复用。
export function getUserProfile() {
  return request.get('/user/profile')
}

