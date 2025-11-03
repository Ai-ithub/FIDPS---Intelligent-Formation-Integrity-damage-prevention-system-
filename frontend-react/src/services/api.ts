import axios from 'axios'
import toast from 'react-hot-toast'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred'
    toast.error(message)
    return Promise.reject(error)
  }
)

// API Functions
export const apiService = {
  // Dashboard Metrics
  getDashboardMetrics: () => api.get('/dashboard/metrics'),
  
  // Wells
  getWells: () => api.get('/wells'),
  getWellSummary: (wellId: string) => api.get(`/wells/${wellId}/summary`),
  
  // Sensor Data
  getLatestSensorData: (wellId: string) => api.get(`/sensor-data/latest/${wellId}`),
  getSensorDataHistory: (wellId: string, params?: any) => 
    api.get(`/data/history/${wellId}`, { params }),
  
  // Anomalies
  getActiveAnomalies: (params?: any) => api.get('/anomalies/recent', { params }),
  getAnomalyHistory: (params?: any) => api.get('/anomalies/history', { params }),
  acknowledgeAnomaly: (anomalyId: string) => api.post(`/anomalies/${anomalyId}/acknowledge`),
  
  // Data Quality
  getValidationResults: (params?: any) => api.get('/validation/results', { params }),
  
  // System Status
  getSystemStatus: () => api.get('/system/status'),
  
  // Health Check
  healthCheck: () => api.get('/health'),
}

export default api

