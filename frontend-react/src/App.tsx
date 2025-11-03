import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout/Layout'
import Dashboard from './pages/Dashboard'
import WellsPage from './pages/WellsPage'
import AnomaliesPage from './pages/AnomaliesPage'
import DataQualityPage from './pages/DataQualityPage'
import SystemPage from './pages/SystemPage'
import DamageDiagnosticsPage from './pages/DamageDiagnosticsPage'
import RTOControlPage from './pages/RTOControlPage'
import RealtimeMonitoringPage from './pages/RealtimeMonitoringPage'

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      refetchInterval: 30000, // 30 seconds
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/wells" element={<WellsPage />} />
            <Route path="/anomalies" element={<AnomaliesPage />} />
            <Route path="/damage-diagnostics" element={<DamageDiagnosticsPage />} />
            <Route path="/rto-control" element={<RTOControlPage />} />
            <Route path="/data-quality" element={<DataQualityPage />} />
            <Route path="/system" element={<SystemPage />} />
            <Route path="/realtime-monitoring" element={<RealtimeMonitoringPage />} />
          </Routes>
        </Layout>
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </Router>
    </QueryClientProvider>
  )
}

export default App

