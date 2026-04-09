import DashboardCard from "../components/DashboardCard";
import { useApi } from "../hooks/useApi";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

export default function TaxiDashboard() {
  const stats = useApi<{ rows: number; avg_fare: number }>("/api/stats");
  const tips = useApi<{ avg_tip: number; avg_tip_pct: number }>("/api/tip-stats");
  const duration = useApi<{ avg: number }>("/api/duration-stats");
  const fraud = useApi<Record<string, number>>("/api/fraud-signals");
  const hourly = useApi<{ hour: number; count: number }[]>("/api/hourly-distribution");
  const payments = useApi<Record<string, number>>("/api/payment-types");

  const paymentData = payments.data
    ? Object.entries(payments.data).map(([type, count]) => ({
        name: type,
        value: count,
      }))
    : [];

  const COLORS = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626"];

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">
          Fleet Analytics Dashboard
        </h1>
        <p className="text-slate-500">Insights from processed NYC data</p>
      </header>

      {/* Top summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
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
        <DashboardCard
          title="Avg. Tip"
          value={tips.data ? tips.data.avg_tip.toFixed(2) : null}
          unit="USD"
        />
        <DashboardCard
          title="Avg. Tip %"
          value={tips.data ? (tips.data.avg_tip_pct * 100).toFixed(1) : null}
          unit="%"
        />
      </div>

      {/* Second row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <DashboardCard
          title="Avg. Duration"
          value={duration.data ? duration.data.avg.toFixed(0) : null}
          unit="sec"
        />
        <DashboardCard
          title="Cash Payments"
          value={fraud.data ? fraud.data.cash_only.toLocaleString() : null}
          unit="trips"
        />
        <DashboardCard
          title="Zero-Distance Fares"
          value={fraud.data ? fraud.data.zero_distance_nonzero_fare : null}
          unit="cases"
        />
      </div>

      {/* Hourly Trips Chart */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm mb-8 w-full">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Trips by Hour of Day
        </h2>

        <div style={{ height: 260, width: "100%" }}>
          {Array.isArray(hourly.data) && hourly.data.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={hourly.data}>
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#2563eb"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-slate-400 text-center pt-20">Loading…</div>
          )}
        </div>
      </div>

      {/* Payment Type Pie Chart */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm mb-8 w-full">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Payment Type Breakdown
        </h2>

        <div style={{ height: 260, width: "100%" }}>
          {Array.isArray(paymentData) && paymentData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={paymentData}
                  dataKey="value"
                  nameKey="name"
                  outerRadius={80}
                  label
                >
                  {paymentData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-slate-400 text-center pt-20">Loading…</div>
          )}
        </div>
      </div>

      {/* Fraud / Anomaly Panel */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm mb-8 w-full">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Fraud & Anomaly Signals
        </h2>

        <ul className="space-y-2">
          {fraud.data &&
            Object.entries(fraud.data).map(([key, value]) => (
              <li
                key={key}
                className="flex justify-between items-center text-slate-700 gap-4"
              >
                <span className="capitalize">{key.replace(/_/g, " ")}</span>
                <span className="font-semibold">{value.toLocaleString()}</span>
              </li>
            ))}
        </ul>
      </div>
    </div>
  );
}
