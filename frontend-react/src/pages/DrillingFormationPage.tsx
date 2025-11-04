import { useState, useEffect } from 'react'
import DrillingParameters from '../components/Dashboard/DrillingParameters'

const DrillingFormationPage = () => {
  const [rop, setRop] = useState<{ value: number; average: number; timestamp: string }[]>([])
  const [torque, setTorque] = useState<{ value: number; timestamp: string }[]>([])
  const [drag, setDrag] = useState<{ value: number; timestamp: string }[]>([])
  const [lwd, setLwd] = useState<{
    gammaRay: number[]
    resistivity: { deep: number[]; shallow: number[] }
    depth: number[]
  } | null>(null)

  useEffect(() => {
    const now = new Date()
    
    // Initialize ROP data
    const initialRop = Array.from({ length: 30 }, (_, i) => {
      const value = 45 + Math.random() * 15
      return {
        value,
        average: 50,
        timestamp: new Date(now.getTime() - (30 - i) * 60000).toISOString(),
      }
    })
    setRop(initialRop)

    // Initialize Torque data
    const initialTorque = Array.from({ length: 30 }, (_, i) => ({
      value: 12 + Math.random() * 3,
      timestamp: new Date(now.getTime() - (30 - i) * 60000).toISOString(),
    }))
    setTorque(initialTorque)

    // Initialize Drag data
    const initialDrag = Array.from({ length: 30 }, (_, i) => ({
      value: 180 + Math.random() * 20,
      timestamp: new Date(now.getTime() - (30 - i) * 60000).toISOString(),
    }))
    setDrag(initialDrag)

    // Initialize LWD data
    const depth = Array.from({ length: 50 }, (_, i) => 1500 + i * 2)
    const gammaRay = depth.map(() => 60 + Math.random() * 40)
    const resistivityDeep = depth.map(() => 2 + Math.random() * 3)
    const resistivityShallow = resistivityDeep.map(r => r * 0.7 + Math.random() * 0.5)
    setLwd({
      gammaRay,
      resistivity: { deep: resistivityDeep, shallow: resistivityShallow },
      depth,
    })

    // Simulate real-time updates
    const interval = setInterval(() => {
      setRop(prev => [
        ...prev.slice(1),
        {
          value: 45 + Math.random() * 15,
          average: 50,
          timestamp: new Date().toISOString(),
        },
      ])
      setTorque(prev => [
        ...prev.slice(1),
        {
          value: 12 + Math.random() * 3,
          timestamp: new Date().toISOString(),
        },
      ])
      setDrag(prev => [
        ...prev.slice(1),
        {
          value: 180 + Math.random() * 20,
          timestamp: new Date().toISOString(),
        },
      ])
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">Drilling & Formation Parameters</h2>
        <p className="text-gray-600 mt-2">Real-time monitoring of drilling operations and formation response</p>
      </div>

      <DrillingParameters rop={rop} torque={torque} drag={drag} lwd={lwd} />
    </div>
  )
}

export default DrillingFormationPage

