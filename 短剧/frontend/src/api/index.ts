import axios from 'axios'

/**
 * Axios 实例 - 统一封装 API 请求。

 * baseURL 从环境变量读取，开发环境通过 Vite proxy 代理到后端。
 */
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 300000, // AI 生成可能较慢，5 分钟超时
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error(`[API Error] ${error.config?.url}: ${message}`)
    return Promise.reject(error)
  },
)

export default apiClient
