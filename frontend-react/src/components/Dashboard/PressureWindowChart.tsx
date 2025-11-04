import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

interface PressureWindowChartProps {
  tvd?: number[] // True Vertical Depth
  porePressure?: number[] // Pore Pressure (EMW in ppg)
  fractureGradient?: number[] // Fracture Gradient (EMW in ppg)
  currentECD?: number // Current ECD value
  currentDepth?: number // Current depth where ECD is measured
}

const PressureWindowChart = ({
  tvd = Array.from({ length: 50 }, (_, i) => 1000 + i * 100), // Sample depth data
  porePressure = Array.from({ length: 50 }, (_, i) => 8.5 + (i * 0.02)), // Sample pore pressure
  fractureGradient = Array.from({ length: 50 }, (_, i) => 12.5 + (i * 0.02)), // Sample fracture gradient
  currentECD = 10.2,
  currentDepth = 5000,
}: PressureWindowChartProps) => {
  // Find the index closest to current depth
  const depthIndex = tvd.findIndex(d => d >= currentDepth) || Math.floor(tvd.length / 2)
  const ecdPoint = currentECD

  const data = {
    labels: tvd.map(d => `${d} ft`),
    datasets: [
      {
        label: 'خط فشار تخلخل (Pore Pressure)',
        data: porePressure,
        borderColor: 'rgb(34, 197, 94)', // Green
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderWidth: 2,
        tension: 0.1,
        fill: false,
      },
      {
        label: 'خط گرادیان شکست (Fracture Gradient)',
        data: fractureGradient,
        borderColor: 'rgb(239, 68, 68)', // Red
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        borderWidth: 2,
        tension: 0.1,
        fill: false,
      },
      {
        label: 'نقطه فعلی ECD',
        data: Array(tvd.length).fill(null).map((_, i) => i === depthIndex ? ecdPoint : null),
        borderColor: 'rgb(59, 130, 246)', // Blue
        backgroundColor: 'rgb(59, 130, 246)',
        borderWidth: 3,
        pointRadius: 8,
        pointHoverRadius: 10,
        pointStyle: 'circle',
        showLine: false,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          font: {
            family: 'Arial, sans-serif',
          },
        },
      },
      title: {
        display: true,
        text: 'نمودار پنجره فشار (Pressure Window) - The Money Plot',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: ${context.parsed.y?.toFixed(2)} ppg (EMW)`
          },
        },
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'عمق (TVD - ft)',
          font: {
            size: 12,
            weight: 'bold' as const,
          },
        },
        reverse: true, // Depth increases downward
      },
      y: {
        title: {
          display: true,
          text: 'فشار معادل وزن گل (EMW - ppg)',
          font: {
            size: 12,
            weight: 'bold' as const,
          },
        },
        beginAtZero: false,
        min: Math.min(...porePressure) - 0.5,
        max: Math.max(...fractureGradient) + 0.5,
      },
    },
  }

  // Check if ECD is in safe zone
  const safeZone = ecdPoint > porePressure[depthIndex] && ecdPoint < fractureGradient[depthIndex]
  const dangerZone = !safeZone

  return (
    <div className="space-y-4">
      <div className={`card p-4 ${dangerZone ? 'border-l-4 border-l-red-500 bg-red-50' : 'border-l-4 border-l-green-500'}`}>
        <div className="h-96">
          <Line data={data} options={options} />
        </div>
        <div className="mt-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={`w-4 h-4 rounded-full ${safeZone ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm font-medium">
                وضعیت: {safeZone ? '✅ در محدوده ایمن' : '⚠️ خارج از محدوده ایمن'}
              </span>
            </div>
            <div className="text-sm text-gray-600">
              ECD فعلی: <span className="font-bold">{ecdPoint.toFixed(2)} ppg</span> در عمق: <span className="font-bold">{currentDepth} ft</span>
            </div>
          </div>
          {dangerZone && (
            <div className="text-red-600 font-bold text-sm">
              ⚠️ هشدار: ECD خارج از محدوده ایمن است!
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default PressureWindowChart

