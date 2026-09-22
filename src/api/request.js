import axios from 'axios'
import { BASE_URL } from '../config'

let csrfToken = null

const request = axios.create({
  baseURL: BASE_URL,
  // 自动携带 Cookie，例如后端的 session_id
  withCredentials: true
})

// 保存 CSRF Token
export function setCsrfToken(token) {
  csrfToken = token
}

// 获取 CSRF Token
export function getCsrfToken() {
  return csrfToken
}

// 请求拦截器
request.interceptors.request.use((config) => {
  const method = config.method?.toUpperCase()

  // 修改数据的请求才添加 CSRF Token
  if (
    ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) &&
    csrfToken
  ) {
    config.headers['X-CSRF-Token'] = csrfToken
  }

  return config
})

export default request
