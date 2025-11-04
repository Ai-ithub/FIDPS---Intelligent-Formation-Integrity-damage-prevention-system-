import { useState } from 'react'
import { Database, Activity, History, Sparkles } from 'lucide-react'
import SensorDataView from '../components/Data/SensorDataView'
import HistoricalDataView from '../components/Data/HistoricalDataView'
import SyntheticDataView from '../components/Data/SyntheticDataView'

type DataView = 'sensor' | 'historical' | 'synthetic'

const DataPage = () => {
  const [activeView, setActiveView] = useState<DataView>('sensor')

  const tabs = [
    { id: 'sensor' as DataView, label: 'Sensor Data', icon: Activity },
    { id: 'historical' as DataView, label: 'Historical Data', icon: History },
    { id: 'synthetic' as DataView, label: 'Synthetic Data', icon: Sparkles },
  ]

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <div className="flex items-center space-x-3 mb-2">
          <Database className="h-8 w-8 text-primary-600" />
          <h2 className="text-3xl font-bold text-gray-900">Data Management</h2>
        </div>
        <p className="text-gray-600 mt-2">View and manage sensor, historical, and synthetic data</p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveView(tab.id)}
                  className={`
                    flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                    ${
                      activeView === tab.id
                        ? 'border-primary-600 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="h-5 w-5" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeView === 'sensor' && <SensorDataView />}
          {activeView === 'historical' && <HistoricalDataView />}
          {activeView === 'synthetic' && <SyntheticDataView />}
        </div>
      </div>
    </div>
  )
}

export default DataPage

