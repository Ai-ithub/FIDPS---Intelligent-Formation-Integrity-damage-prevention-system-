import { Gauge, CheckCircle, XCircle, Clock } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'

const RTOControlPage = () => {
  const [selectedRecommendation, setSelectedRecommendation] = useState<string | null>(null)

  // Sample RTO recommendations
  const recommendations = [
    {
      id: 'rec-1',
      timestamp: new Date().toISOString(),
      damageType: 'DT-02',
      currentValues: {
        weightOnBit: 25.5,
        rotarySpeed: 120,
        flowRate: 350,
        mudWeight: 10.5,
      },
      recommendedValues: {
        weightOnBit: 22.0,
        rotarySpeed: 110,
        flowRate: 365,
        mudWeight: 10.2,
      },
      expectedImprovement: 0.15,
      riskReduction: 0.32,
      status: 'pending',
    },
  ]

  const handleApprove = () => {
    if (selectedRecommendation) {
      toast.success('RTO recommendation approved')
      setSelectedRecommendation(null)
    }
  }

  const handleReject = () => {
    if (selectedRecommendation) {
      toast.error('RTO recommendation rejected')
      setSelectedRecommendation(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">Real-Time Optimization Control</h2>
        <p className="text-gray-600 mt-2">Review and approve RTO recommendations for optimal drilling parameters</p>
      </div>

      {recommendations.map((rec) => (
        <div key={rec.id} className="card">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <Gauge className="h-8 w-8 text-blue-600" />
              <div>
                <h3 className="text-xl font-semibold">RTO Recommendation</h3>
                <p className="text-sm text-gray-600">
                  Target Damage Type: <span className="font-mono">{rec.damageType}</span>
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Clock className="h-4 w-4" />
              <span>Generated: {new Date(rec.timestamp).toLocaleTimeString()}</span>
            </div>
          </div>

          {/* Expected Benefits */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-2">Expected Improvement</p>
              <p className="text-3xl font-bold text-green-600">
                +{(rec.expectedImprovement * 100).toFixed(0)}%
              </p>
              <p className="text-xs text-gray-600 mt-1">Drilling efficiency</p>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-2">Risk Reduction</p>
              <p className="text-3xl font-bold text-blue-600">
                -{(rec.riskReduction * 100).toFixed(0)}%
              </p>
              <p className="text-xs text-gray-600 mt-1">Formation damage risk</p>
            </div>
          </div>

          {/* Parameter Comparison */}
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-4">Recommended Parameter Adjustments</h4>
            <div className="space-y-3">
              {Object.keys(rec.currentValues).map((param) => (
                <div key={param} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium capitalize">
                    {param.replace(/([A-Z])/g, ' $1').trim()}
                  </span>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-600">
                      Current: <span className="font-bold">{rec.currentValues[param as keyof typeof rec.currentValues]}</span>
                    </span>
                    <span className="text-blue-600">→</span>
                    <span className="text-sm font-bold text-green-600">
                      {rec.recommendedValues[param as keyof typeof rec.recommendedValues]}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Approval Actions */}
          {rec.status === 'pending' && (
            <div className="flex items-center justify-end space-x-4 pt-4 border-t">
              <button
                onClick={handleReject}
                className="flex items-center space-x-2 px-6 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
              >
                <XCircle className="h-5 w-5" />
                <span>Reject</span>
              </button>
              <button
                onClick={handleApprove}
                className="flex items-center space-x-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <CheckCircle className="h-5 w-5" />
                <span>Approve</span>
              </button>
            </div>
          )}

          {rec.status === 'approved' && (
            <div className="flex items-center space-x-2 text-green-600 pt-4 border-t">
              <CheckCircle className="h-5 w-5" />
              <span className="font-semibold">Approved</span>
            </div>
          )}
        </div>
      ))}

      {/* No Recommendations Message */}
      {recommendations.length === 0 && (
        <div className="card text-center py-12">
          <Gauge className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-600">No RTO recommendations available</p>
          <p className="text-sm text-gray-500 mt-2">
            Recommendations will appear here when the optimization engine detects opportunities
          </p>
        </div>
      )}
    </div>
  )
}

export default RTOControlPage

