import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout/Layout'
import Dashboard from './pages/Dashboard'
import KPIsPage from './pages/KPIsPage'
import MudParametersPage from './pages/MudParametersPage'
import DrillingFormationPage from './pages/DrillingFormationPage'
import AlertsPage from './pages/AlertsPage'
import DataPage from './pages/DataPage'
import SystemPage from './pages/SystemPage'
import AnomaliesPage from './pages/AnomaliesPage'
import DataQualityPage from './pages/DataQualityPage'
import WellsPage from './pages/WellsPage'

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
            <Route path="/kpis" element={<KPIsPage />} />
            <Route path="/mud-parameters" element={<MudParametersPage />} />
            <Route path="/drilling-formation" element={<DrillingFormationPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/anomalies" element={<AnomaliesPage />} />
            <Route path="/data" element={<DataPage />} />
            <Route path="/data-quality" element={<DataQualityPage />} />
            <Route path="/wells" element={<WellsPage />} />
            <Route path="/system" element={<SystemPage />} />
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

