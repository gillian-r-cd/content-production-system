// web/src/api/client.ts
// Axios HTTP客户端
// 功能：配置baseURL、拦截器、错误处理

import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 180000, // AI调用可能需要3分钟
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // 统一错误处理
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default apiClient

