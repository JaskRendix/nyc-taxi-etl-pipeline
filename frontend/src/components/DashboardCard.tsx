export default function DashboardCard({
  title,
  value,
  unit,
}: {
  title: string;
  value: string | number | null;
  unit?: string;
}) {
  return (
    <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm">
      <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider">
        {title}
      </h3>
      <p className="mt-2 text-3xl font-bold text-slate-900">
        {value !== null ? value : "…"}{" "}
        {unit && <span className="text-lg text-slate-400">{unit}</span>}
      </p>
    </div>
  );
}
