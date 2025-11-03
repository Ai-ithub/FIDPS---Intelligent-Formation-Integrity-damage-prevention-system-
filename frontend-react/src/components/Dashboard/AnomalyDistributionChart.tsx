import { Doughnut } from 'react-chartjs-2'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend)

const AnomalyDistributionChart = () => {
  const data = {
    labels: ['Critical', 'Warning', 'Info'],
    datasets: [
      {
        data: [5, 12, 8],
        backgroundColor: [
          'rgb(239, 68, 68)',
          'rgb(234, 179, 8)',
          'rgb(59, 130, 246)',
        ],
        borderWidth: 2,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
    },
  }

  return (
    <div className="h-80">
      <Doughnut data={data} options={options} />
    </div>
  )
}

export default AnomalyDistributionChart

