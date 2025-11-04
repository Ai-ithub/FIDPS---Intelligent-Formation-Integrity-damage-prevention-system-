import { useState, useEffect } from 'react'
import MudParameters from '../components/Dashboard/MudParameters'

const MudParametersPage = () => {
  const [mudWeight, setMudWeight] = useState<{ in: number; out: number; timestamp: string }[]>([])
  const [rheology, setRheology] = useState<{ viscosity: number; pv: number; yp: number; timestamp: string }[]>([])
  const [fluidLoss, setFluidLoss] = useState<{ api: number; hthp: number; timestamp: string } | null>(null)
  const [solidsContent, setSolidsContent] = useState<{ lgs: number; timestamp: string } | null>(null)

  useEffect(() => {
    // Initialize with sample data
    const now = new Date()
    const initialMudWeight = Array.from({ length: 20 }, (_, i) => ({
      in: 9.2 + Math.random() * 0.2,
      out: 9.15 + Math.random() * 0.3,
      timestamp: new Date(now.getTime() - (20 - i) * 60000).toISOString(),
    }))
    setMudWeight(initialMudWeight)

    const initialRheology = Array.from({ length: 20 }, (_, i) => ({
      viscosity: 45 + Math.random() * 10,
      pv: 25 + Math.random() * 5,
      yp: 15 + Math.random() * 5,
      timestamp: new Date(now.getTime() - (20 - i) * 60000).toISOString(),
    }))
    setRheology(initialRheology)

    setFluidLoss({
      api: 4.5 + Math.random() * 2,
      hthp: 12 + Math.random() * 5,
      timestamp: new Date(now.getTime() - 2 * 3600000).toISOString(),
    })

    setSolidsContent({
      lgs: 3.5 + Math.random() * 2,
      timestamp: new Date(now.getTime() - 2 * 3600000).toISOString(),
    })

    // Simulate real-time updates
    const interval = setInterval(() => {
      setMudWeight(prev => [
        ...prev.slice(1),
        {
          in: 9.2 + Math.random() * 0.2,
          out: 9.15 + Math.random() * 0.3,
          timestamp: new Date().toISOString(),
        },
      ])
      setRheology(prev => [
        ...prev.slice(1),
        {
          viscosity: 45 + Math.random() * 10,
          pv: 25 + Math.random() * 5,
          yp: 15 + Math.random() * 5,
          timestamp: new Date().toISOString(),
        },
      ])
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">Drilling Fluid Parameters</h2>
        <p className="text-gray-600 mt-2">Real-time monitoring of mud properties and quality</p>
      </div>

      <MudParameters
        mudWeight={mudWeight}
        rheology={rheology}
        fluidLoss={fluidLoss}
        solidsContent={solidsContent}
      />
    </div>
  )
}

export default MudParametersPage

