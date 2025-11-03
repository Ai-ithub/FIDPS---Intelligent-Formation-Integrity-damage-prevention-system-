import { create } from 'zustand'

interface WebSocketState {
  socket: any
  isConnected: boolean
  connectionError: string | null
  metrics: {
    activeWells: number
    anomaliesToday: number
    criticalAlerts: number
    dataQualityScore: number
    systemHealth: 'healthy' | 'warning' | 'degraded' | 'critical'
  }
  recentAnomalies: any[]
  sensorData: any[]
  // Actions
  connect: () => void
  disconnect: () => void
  updateMetrics: (metrics: Partial<WebSocketState['metrics']>) => void
  addAnomaly: (anomaly: any) => void
  addSensorData: (data: any) => void
}

export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  socket: null,
  isConnected: false,
  connectionError: null,
  metrics: {
    activeWells: 0,
    anomaliesToday: 0,
    criticalAlerts: 0,
    dataQualityScore: 0,
    systemHealth: 'healthy',
  },
  recentAnomalies: [],
  sensorData: [],

  connect: () => {
    // Use native WebSocket for now (can be upgraded to socket.io later)
    const ws = new WebSocket('ws://localhost:8000/ws/dashboard/frontend')

    ws.onopen = () => {
      console.log('WebSocket connected')
      set({ isConnected: true, connectionError: null })
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      set({ isConnected: false })
    }

    ws.onerror = (error) => {
      console.error('WebSocket connection error:', error)
      set({ connectionError: 'Connection failed' })
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        
        if (message.type === 'sensor_data_update') {
          const currentData = get().sensorData
          const newData = [...currentData, message.data].slice(-100)
          set({ sensorData: newData })
        } else if (message.type === 'anomaly_alert') {
          const currentAnomalies = get().recentAnomalies
          set({ recentAnomalies: [message.alert, ...currentAnomalies].slice(0, 50) })
          
          if (message.alert.severity === 'critical') {
            const metrics = get().metrics
            set({ metrics: { ...metrics, criticalAlerts: metrics.criticalAlerts + 1 } })
          }
        } else if (message.type === 'dashboard_metrics') {
          set({ metrics: message.metrics })
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }

    set({ socket: ws })
  },

  disconnect: () => {
    const { socket } = get()
    if (socket && socket.close) {
      socket.close()
      set({ socket: null, isConnected: false })
    }
  },

  updateMetrics: (newMetrics) => {
    const metrics = get().metrics
    set({
      metrics: {
        ...metrics,
        ...newMetrics,
      }
    })
  },

  addAnomaly: (anomaly) => {
    const currentAnomalies = get().recentAnomalies
    set({
      recentAnomalies: [anomaly, ...currentAnomalies].slice(0, 50)
    })
  },

  addSensorData: (data) => {
    const currentData = get().sensorData
    set({
      sensorData: [...currentData, data].slice(-100)
    })
  },
}))

