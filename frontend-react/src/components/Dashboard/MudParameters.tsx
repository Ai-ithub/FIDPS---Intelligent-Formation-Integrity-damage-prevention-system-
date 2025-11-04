import { Droplet, TestTube, Filter, Layers } from 'lucide-react'

interface MudParametersProps {
  mudWeightIn?: number // MW In (ppg)
  mudWeightOut?: number // MW Out (ppg)
  viscosity?: number // Viscosity (cP)
  viscosityTarget?: number // Target Viscosity
  plasticViscosity?: number // PV (cP)
  yieldPoint?: number // YP (lb/100ft²)
  yieldPointTarget?: number // Target YP
  apiFluidLoss?: number // API Fluid Loss (ml/30min)
  hthpFluidLoss?: number // HTHP Fluid Loss (ml/30min)
  hthpFluidLossTime?: string // Last HTHP test time
  solidsContent?: number // Solids Content (%)
  lgs?: number // Low Gravity Solids (%)
  lgsTime?: string // Last LGS test time
}

const MudParameters = ({
  mudWeightIn = 10.5,
  mudWeightOut = 10.4,
  viscosity = 45,
  viscosityTarget = 40,
  plasticViscosity = 25,
  yieldPoint = 18,
  yieldPointTarget = 15,
  apiFluidLoss = 5.2,
  hthpFluidLoss = 12.5,
  hthpFluidLossTime = '2024-01-15 14:30',
  solidsContent = 12.5,
  lgs = 4.2,
  lgsTime = '2024-01-15 14:30',
}: MudParametersProps) => {
  const mudWeightDiff = mudWeightOut - mudWeightIn
  const viscosityDiff = viscosity - viscosityTarget
  const yieldPointDiff = yieldPoint - yieldPointTarget

  return (
    <div className="space-y-6">
      <div className="flex items-center mb-4">
        <Droplet className="mr-2 h-6 w-6 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-900">Drilling Fluid Parameters (Mud Parameters)</h2>
      </div>

      {/* Mud Weight */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Droplet className="mr-2 h-5 w-5" />
            Mud Weight
          </h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div className="text-sm text-gray-600 mb-2">Mud Weight In (MW In)</div>
            <div className="text-3xl font-bold text-blue-600">{mudWeightIn.toFixed(2)}</div>
            <div className="text-sm text-gray-500 mt-1">ppg</div>
          </div>
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <div className="text-sm text-gray-600 mb-2">Mud Weight Out (MW Out)</div>
            <div className="text-3xl font-bold text-green-600">{mudWeightOut.toFixed(2)}</div>
            <div className="text-sm text-gray-500 mt-1">ppg</div>
          </div>
        </div>
        <div className="mt-4 bg-white rounded-lg p-4 border border-gray-200">
          <div className="text-sm text-gray-600 mb-2">Difference (MW Out - MW In)</div>
          <div className={`text-2xl font-bold ${Math.abs(mudWeightDiff) > 0.1 ? mudWeightDiff > 0 ? 'text-orange-600' : 'text-red-600' : 'text-green-600'}`}>
            {mudWeightDiff > 0 ? '+' : ''}{mudWeightDiff.toFixed(3)} ppg
          </div>
          {Math.abs(mudWeightDiff) > 0.1 && (
            <div className="text-sm text-gray-600 mt-2">
              {mudWeightDiff < 0 
                ? '⚠️ Decrease in MW Out may indicate gas or water influx'
                : '⚠️ Increase in MW Out may indicate cuttings accumulation'
              }
            </div>
          )}
        </div>
      </div>

      {/* Rheology Parameters */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <TestTube className="mr-2 h-5 w-5" />
            Rheology Parameters
          </h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Viscosity</div>
            <div className="text-3xl font-bold">{viscosity}</div>
            <div className="text-sm text-gray-500 mt-1">cP</div>
            <div className="mt-2 text-sm">
              <span className="text-gray-600">Target: </span>
              <span className="font-semibold">{viscosityTarget} cP</span>
              <span className={`ml-2 ${viscosityDiff > 0 ? 'text-yellow-600' : 'text-green-600'}`}>
                ({viscosityDiff > 0 ? '+' : ''}{viscosityDiff})
              </span>
            </div>
            {viscosity > viscosityTarget * 1.2 && (
              <div className="mt-2 text-xs text-yellow-600">
                ⚠️ High viscosity can falsely increase ECD
              </div>
            )}
          </div>
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Plastic Viscosity (PV)</div>
            <div className="text-3xl font-bold">{plasticViscosity}</div>
            <div className="text-sm text-gray-500 mt-1">cP</div>
          </div>
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Yield Point (YP)</div>
            <div className="text-3xl font-bold">{yieldPoint}</div>
            <div className="text-sm text-gray-500 mt-1">lb/100ft²</div>
            <div className="mt-2 text-sm">
              <span className="text-gray-600">Target: </span>
              <span className="font-semibold">{yieldPointTarget} lb/100ft²</span>
              <span className={`ml-2 ${yieldPointDiff > 0 ? 'text-yellow-600' : 'text-green-600'}`}>
                ({yieldPointDiff > 0 ? '+' : ''}{yieldPointDiff})
              </span>
            </div>
            {yieldPoint > yieldPointTarget * 1.3 && (
              <div className="mt-2 text-xs text-yellow-600">
                ⚠️ High YP increases pressure when restarting pumps
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Fluid Loss */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Filter className="mr-2 h-5 w-5" />
            Filtration Rate (Fluid Loss)
          </h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">API Fluid Loss</div>
            <div className="text-3xl font-bold">{apiFluidLoss.toFixed(1)}</div>
            <div className="text-sm text-gray-500 mt-1">ml/30min</div>
            <div className="mt-2 text-xs text-gray-600">
              {apiFluidLoss <= 5 ? '✅ Within acceptable range' : apiFluidLoss <= 10 ? '⚠️ Acceptable' : '🚨 Out of range'}
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">HTHP Fluid Loss</div>
            <div className="text-3xl font-bold">{hthpFluidLoss.toFixed(1)}</div>
            <div className="text-sm text-gray-500 mt-1">ml/30min</div>
            <div className="mt-2 text-xs text-gray-600">
              Last test: {hthpFluidLossTime}
            </div>
            <div className="mt-2 text-xs">
              {hthpFluidLoss <= 15 ? (
                <span className="text-green-600">✅ Within acceptable range</span>
              ) : hthpFluidLoss <= 25 ? (
                <span className="text-yellow-600">⚠️ Acceptable - Monitor closely</span>
              ) : (
                <span className="text-red-600">🚨 Out of range - High chemical damage risk</span>
              )}
            </div>
            {hthpFluidLoss > 20 && (
              <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                ⚠️ High HTHP Fluid Loss: Excessive filtrate is invading the formation, increasing risk of chemical damage (shale swelling)
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Solids Content */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Layers className="mr-2 h-5 w-5" />
            Solids Content
          </h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Total Solids</div>
            <div className="text-3xl font-bold">{solidsContent.toFixed(1)}</div>
            <div className="text-sm text-gray-500 mt-1">%</div>
          </div>
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Low Gravity Solids (LGS)</div>
            <div className="text-3xl font-bold">{lgs.toFixed(1)}</div>
            <div className="text-sm text-gray-500 mt-1">%</div>
            <div className="mt-2 text-xs text-gray-600">
              Last test: {lgsTime}
            </div>
            <div className="mt-2 text-xs">
              {lgs <= 3 ? (
                <span className="text-green-600">✅ Ideal range</span>
              ) : lgs <= 5 ? (
                <span className="text-yellow-600">⚠️ Acceptable</span>
              ) : (
                <span className="text-red-600">🚨 High - Risk of pore plugging</span>
              )}
            </div>
            {lgs > 5 && (
              <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                ⚠️ High LGS: Potential for formation pore plugging and permeability reduction
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default MudParameters

