import { Beaker, TrendingUp, AlertCircle } from 'lucide-react'

// Formation Damage Types as per FR-2.2
const DAMAGE_TYPES = [
  { id: 'DT-01', name: 'CLAY_IRON_CONTROL', description: 'Clay swelling and iron precipitation issues' },
  { id: 'DT-02', name: 'DRILLING_INDUCED', description: 'Damage caused by drilling operations' },
  { id: 'DT-03', name: 'FLUID_LOSS', description: 'Loss of drilling fluid into formation' },
  { id: 'DT-04', name: 'SCALE_SLUDGE', description: 'Scale and sludge deposition' },
  { id: 'DT-05', name: 'NEAR_WELLBORE_EMULSIONS', description: 'Emulsion formation near wellbore' },
  { id: 'DT-06', name: 'ROCK_FLUID_INTERACTION', description: 'Adverse rock-fluid interactions' },
  { id: 'DT-07', name: 'COMPLETION_DAMAGE', description: 'Formation damage during completion' },
  { id: 'DT-08', name: 'STRESS_CORROSION', description: 'Stress corrosion cracking' },
  { id: 'DT-09', name: 'SURFACE_FILTRATION', description: 'Surface filtration damage' },
  { id: 'DT-10', name: 'ULTRA_CLEAN_FLUIDS', description: 'Issues with ultra-clean fluid systems' },
]

const DamageDiagnosticsPage = () => {
  // This will be connected to real ML predictions later
  const currentPrediction = {
    damageType: 'DT-02',
    probability: 0.87,
    confidence: 0.92,
    contributingFactors: [
      { parameter: 'Weight on Bit', impact: 0.45 },
      { parameter: 'Drilling Rate', impact: 0.32 },
      { parameter: 'Mud Weight', impact: 0.23 },
    ],
  }

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">Damage Diagnostics</h2>
        <p className="text-gray-600 mt-2">Real-time formation damage type classification and analysis</p>
      </div>

      {/* Current Prediction */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <Beaker className="h-8 w-8 text-blue-600" />
          <h3 className="text-xl font-semibold">Current Prediction</h3>
        </div>

        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-gray-600 mb-2">Damage Type</p>
              <p className="text-2xl font-bold text-gray-900">DT-02</p>
              <p className="text-sm text-gray-600 mt-1">DRILLING_INDUCED</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-2">Probability</p>
              <div className="flex items-center space-x-2">
                <div className="flex-1 bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-blue-600 h-3 rounded-full"
                    style={{ width: `${currentPrediction.probability * 100}%` }}
                  />
                </div>
                <span className="text-2xl font-bold">87%</span>
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-2">Confidence</p>
              <div className="flex items-center space-x-2">
                <div className="flex-1 bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-green-600 h-3 rounded-full"
                    style={{ width: `${currentPrediction.confidence * 100}%` }}
                  />
                </div>
                <span className="text-2xl font-bold">92%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Contributing Factors */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
            <TrendingUp className="h-4 w-4 mr-2" />
            Contributing Factors
          </h4>
          <div className="space-y-2">
            {currentPrediction.contributingFactors.map((factor, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium">{factor.parameter}</span>
                <div className="flex items-center space-x-3">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${factor.impact * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold w-12 text-right">
                    {(factor.impact * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* All Damage Types Reference */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-4">
          <AlertCircle className="h-6 w-6 text-gray-600" />
          <h3 className="text-lg font-semibold">Formation Damage Types</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {DAMAGE_TYPES.map((type) => (
            <div
              key={type.id}
              className={`p-4 border rounded-lg ${
                type.id === currentPrediction.damageType
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-sm font-bold">{type.id}</span>
                {type.id === currentPrediction.damageType && (
                  <span className="px-2 py-1 bg-blue-600 text-white rounded-full text-xs font-semibold">
                    ACTIVE
                  </span>
                )}
              </div>
              <p className="text-sm font-semibold text-gray-900">{type.name}</p>
              <p className="text-xs text-gray-600 mt-1">{type.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default DamageDiagnosticsPage

