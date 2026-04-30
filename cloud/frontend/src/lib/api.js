import axios from 'axios'
import { getAuthToken } from './auth'

const api = axios.create()

api.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (!token) return config

  config.headers = config.headers || {}
  config.headers.Authorization = `Bearer ${token}`
  config.headers['X-Auth-Token'] = token
  return config
})

export default api

