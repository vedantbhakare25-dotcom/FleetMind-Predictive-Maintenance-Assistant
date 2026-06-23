// Axios instance for calling the FleetMind FastAPI backend
// Automatically attaches the current user's JWT token to every request

import axios from 'axios'
import { supabase } from './supabase'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL
})

// Interceptor runs before every request
// Fetches the current session token and attaches it as Authorization header
api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession()
  const token = data?.session?.access_token

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

export default api