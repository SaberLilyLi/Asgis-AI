// 权限判断统一通过 hasPermission 方法封装。
export function hasPermission(code: string, permissions: string[]) {
  return permissions.includes(code)
}

