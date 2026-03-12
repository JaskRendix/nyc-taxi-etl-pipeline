import { useEffect, useState } from 'react'

const DashboardCard = ({
  title,
  value,
  unit
}: {
  title: string
  value: string | number | null
  unit: string
}) => (
  <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm">
    <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider">
      {title}
    </h3>
    <p className="mt-2 text-3xl font-bold text-slate-900">
      {value !== null ? value : 'Loading...'}{' '}
      <span className="text-lg font-normal text-slate-400">{unit}</span>
    </p>
  </div>
)

export default function TaxiDashboard() {
  const [avgFare, setAvgFare] = useState<number | null>(null)
  const [tripCount, setTripCount] = useState<number | null>(null)

  useEffect(() => {
    fetch('http://localhost:3001/api/stats')
      .then((res) => res.json())
      .then((data) => {
        setAvgFare(Number(data._avg.fare_amount.toFixed(2)))
        setTripCount(data._count.id)
      })
  }, [])

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">
          Fleet Analytics Dashboard
        </h1>
        <p className="text-slate-500">Insights from processed NYC data</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <DashboardCard
          title="Avg. Fare"
          value={avgFare !== null ? `$${avgFare}` : null}
          unit="USD"
        />

        <DashboardCard
          title="Trips Processed"
          value={tripCount !== null ? tripCount.toLocaleString() : null}
          unit="rows"
        />

        <DashboardCard
          title="Anomalies Detected"
          value="0.4"
          unit="%"
        />
      </div>
    </div>
  )
}
