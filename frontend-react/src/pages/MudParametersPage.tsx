import { useState, useEffect } from 'react'
import MudParameters from '../components/Dashboard/MudParameters'

const MudParametersPage = () => {
  const [mudWeightIn, setMudWeightIn] = useState<number>(10.5)
  const [mudWeightOut, setMudWeightOut] = useState<number>(10.4)
  const [viscosity, setViscosity] = useState<number>(45)
  const [plasticViscosity, setPlasticViscosity] = useState<number>(25)
  const [yieldPoint, setYieldPoint] = useState<number>(18)
  const [apiFluidLoss, setApiFluidLoss] = useState<number>(5.2)
  const [hthpFluidLoss, setHthpFluidLoss] = useState<number>(12.5)
  const [solidsContent, setSolidsContent] = useState<number>(12.5)
  const [lgs, setLgs] = useState<number>(4.2)

  useEffect(() => {
    // Initialize with sample data
    setMudWeightIn(10.5)
    setMudWeightOut(10.4)
    setViscosity(45)
    setPlasticViscosity(25)
    setYieldPoint(18)
    setApiFluidLoss(5.2)
    setHthpFluidLoss(12.5)
    setSolidsContent(12.5)
    setLgs(4.2)

    // Simulate real-time updates
    const interval = setInterval(() => {
      setMudWeightIn(9.2 + Math.random() * 0.5)
      setMudWeightOut(9.15 + Math.random() * 0.5)
      setViscosity(45 + Math.random() * 10)
      setPlasticViscosity(25 + Math.random() * 5)
      setYieldPoint(15 + Math.random() * 5)
      setApiFluidLoss(4.5 + Math.random() * 2)
      setHthpFluidLoss(12 + Math.random() * 5)
      setSolidsContent(12.5 + Math.random() * 2)
      setLgs(3.5 + Math.random() * 2)
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const hthpFluidLossTime = new Date().toLocaleString('en-US', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
  
  const lgsTime = new Date().toLocaleString('en-US', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit' 
  })

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">Drilling Fluid Parameters</h2>
        <p className="text-gray-600 mt-2">Real-time monitoring of mud properties and quality</p>
      </div>

      <MudParameters
        mudWeightIn={mudWeightIn}
        mudWeightOut={mudWeightOut}
        viscosity={viscosity}
        viscosityTarget={40}
        plasticViscosity={plasticViscosity}
        yieldPoint={yieldPoint}
        yieldPointTarget={15}
        apiFluidLoss={apiFluidLoss}
        hthpFluidLoss={hthpFluidLoss}
        hthpFluidLossTime={hthpFluidLossTime}
        solidsContent={solidsContent}
        lgs={lgs}
        lgsTime={lgsTime}
      />
    </div>
  )
}

export default MudParametersPage

