import { useState, useEffect } from 'react'
import PressureWindowChart from '../components/Dashboard/PressureWindowChart'
import DeltaPGauge from '../components/Dashboard/DeltaPGauge'
import FlowOutPercentage from '../components/Dashboard/FlowOutPercentage'

const KPIsPage = () => {
  const [pressureData, setPressureData] = useState({
    depth: Array.from({ length: 100 }, (_, i) => 1000 + i * 50),
    porePressure: Array.from({ length: 100 }, () => 9.2 + Math.random() * 0.3),
    fractureGradient: Array.from({ length: 100 }, () => 11.5 + Math.random() * 0.5),
    ecd: Array.from({ length: 100 }, () => 9.5 + Math.random() * 0.4),
  })

  const [deltaP, setDeltaP] = useState(120)
  const [flowIn, setFlowIn] = useState(450)
  const [flowOut, setFlowOut] = useState(448)

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate real-time updates
      setPressureData(prev => ({
        ...prev,
        ecd: prev.ecd.map(val => Math.max(9.2, Math.min(11.5, val + (Math.random() - 0.5) * 0.1))),
      }))
      setDeltaP(prev => Math.max(0, Math.min(250, prev + (Math.random() - 0.5) * 5)))
      setFlowIn(prev => Math.max(400, Math.min(500, prev + (Math.random() - 0.5) * 2)))
      setFlowOut(prev => Math.max(390, Math.min(510, prev + (Math.random() - 0.5) * 2)))
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">Critical KPIs</h2>
        <p className="text-gray-600 mt-2">Real-time monitoring of critical drilling parameters</p>
      </div>

      {/* Pressure Window - The Money Plot */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <PressureWindowChart
          depth={pressureData.depth}
          porePressure={pressureData.porePressure}
          fractureGradient={pressureData.fractureGradient}
          ecd={pressureData.ecd}
        />
      </div>

      {/* Delta P and Flow Out */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DeltaPGauge
          value={deltaP}
          min={0}
          max={250}
          optimalRange={{ min: 50, max: 150 }}
        />
        <FlowOutPercentage flowIn={flowIn} flowOut={flowOut} />
      </div>
    </div>
  )
}

export default KPIsPage

