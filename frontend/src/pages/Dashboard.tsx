import DashboardCard from "../components/DashboardCard";
import { useApi } from "../hooks/useApi";

export default function TaxiDashboard() {
  const stats = useApi<{ rows: number; avg_fare: number }>("/api/stats");

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">
          Fleet Analytics Dashboard
        </h1>
        <p className="text-slate-500">Insights from processed NYC data</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <DashboardCard
          title="Avg. Fare"
          value={stats.data ? stats.data.avg_fare.toFixed(2) : null}
          unit="USD"
        />
        <DashboardCard
          title="Trips Processed"
          value={stats.data ? stats.data.rows.toLocaleString() : null}
          unit="rows"
        />
        <DashboardCard title="Anomalies Detected" value="0.4" unit="%" />
      </div>
    </div>
  );
}
