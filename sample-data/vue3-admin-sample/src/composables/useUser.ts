import { getUserProfile } from '../api/user'

// 用户业务逻辑统一抽离到 composable。
export function useUser() {
  return getUserProfile()
}

