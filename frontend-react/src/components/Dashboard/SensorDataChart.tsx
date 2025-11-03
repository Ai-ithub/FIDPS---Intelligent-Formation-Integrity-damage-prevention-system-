import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale } from 'chart.js'
import 'chartjs-adapter-date-fns'
import { useWebSocketStore } from '../../store/useWebSocketStore'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
)

const SensorDataChart = () => {
  const { sensorData } = useWebSocketStore()

  // Sample data for demonstration (replace with real data from WebSocket)
  const sampleData = {
    labels: Array.from({ length: 20 }, (_, i) => new Date(Date.now() - (20 - i) * 60000)),
    datasets: [
      {
        label: 'Pressure (psi)',
        data: Array.from({ length: 20 }, () => Math.random() * 1000 + 2000),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.1,
      },
      {
        label: 'Temperature (°F)',
        data: Array.from({ length: 20 }, () => Math.random() * 50 + 150),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.1,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: 'minute' as const,
        },
      },
      y: {
        beginAtZero: false,
      },
    },
  }

  return (
    <div className="h-80">
      <Line data={sampleData} options={options} />
    </div>
  )
}

export default SensorDataChart

