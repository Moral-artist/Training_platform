import axios from 'axios'
import { BASE_URL } from '../config'

let csrfToken = null
let csrfPromise = null
const request = axios.create({ baseURL: BASE_URL, withCredentials: true })
export function setCsrfToken(token) { csrfToken = token }
export function getCsrfToken() { return csrfToken }

export async function ensureCsrfToken() {
  if (csrfToken) return csrfToken
  if (!csrfPromise) {
    csrfPromise = request.get('/api/user/user_info')
      .then(response => {
        csrfToken = response.data.csrf_token
        if (!csrfToken) throw new Error('没有获取到登录校验信息，请重新登录。')
        return csrfToken
      }).finally(() => { csrfPromise = null })
  }
  return csrfPromise
}

const publicAuth = new Set([
  '/api/auth/login', '/api/auth/pre_register', '/api/auth/verify_register',
  '/api/auth/pre_reset', '/api/auth/verify_reset'
])
request.interceptors.request.use(async config => {
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(config.method?.toUpperCase()) && !publicAuth.has(config.url)) {
    config.headers['X-CSRF-Token'] = await ensureCsrfToken()
  }
  return config
})
request.interceptors.response.use(response => {
  if (response.data?.csrf_token) setCsrfToken(response.data.csrf_token)
  if (response.config.url === '/api/auth/logout') setCsrfToken(null)
  return response
}, error => {
  if (error.response?.status === 401 || error.response?.data?.detail === 'Invalid CSRF token') setCsrfToken(null)
  // 不重放修改请求，避免重复创建课程；下次操作重新取 CSRF。
  return Promise.reject(error)
})
export default request
