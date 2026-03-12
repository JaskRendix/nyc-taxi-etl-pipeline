import React from 'react'

const DashboardCard = ({ title, value, unit }: { title: string, value: string, unit: string }) => (
  <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm hover:border-blue-500 transition-colors">
    <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider">{title}</h3>
    <p className="mt-2 text-3xl font-bold text-slate-900">{value} <span className="text-lg font-normal text-slate-400">{unit}</span></p>
  </div>
)

export default function TaxiDashboard() {
  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Fleet Analytics Dashboard 🌱</h1>
        <p className="text-slate-500">Real-time insights from processed NYC data</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <DashboardCard title="Avg. Fare" value="$18.50" unit="USD" />
        <DashboardCard title="Trips Processed" value="14,202" unit="rows" />
        <DashboardCard title="Anomalies Detected" value="0.4" unit="%" />
      </div>
    </div>
  )
}
