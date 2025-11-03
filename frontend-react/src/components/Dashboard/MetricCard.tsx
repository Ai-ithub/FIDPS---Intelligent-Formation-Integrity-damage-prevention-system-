import { TrendingUp, TrendingDown } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: number | string
  icon: string
  trend?: number | null
  loading?: boolean
  alert?: boolean
}

const MetricCard = ({ title, value, icon, trend, loading, alert }: MetricCardProps) => {
  const getIcon = () => {
    switch (icon) {
      case 'wells':
        return '🛢️'
      case 'anomalies':
        return '⚠️'
      case 'alerts':
        return '🔔'
      case 'quality':
        return '✓'
      default:
        return '📊'
    }
  }

  const getColor = () => {
    if (alert) return 'text-red-600'
    if (icon === 'quality') return 'text-green-600'
    if (icon === 'alerts') return 'text-orange-600'
    return 'text-blue-600'
  }

  if (loading) {
    return (
      <div className="metric-card">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-24 mb-4"></div>
          <div className="h-10 bg-gray-200 rounded w-32"></div>
        </div>
      </div>
    )
  }

  return (
    <div className={`metric-card ${alert ? 'border-l-4 border-l-red-500' : ''}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-600 mb-2">{title}</p>
          <p className={`text-3xl font-bold ${getColor()}`}>
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {trend !== null && trend !== undefined && (
            <div className="flex items-center mt-2">
              {trend >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
              )}
              <span className={`text-sm ${trend >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {Math.abs(trend)}%
              </span>
            </div>
          )}
        </div>
        <div className="text-4xl opacity-20">{getIcon()}</div>
      </div>
    </div>
  )
}

export default MetricCard

