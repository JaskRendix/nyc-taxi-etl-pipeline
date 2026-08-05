export default function DashboardCard({
  title,
  value,
  unit,
  formatter,
}: {
  title: string;
  value: string | number | null;
  unit?: string;
  formatter?: (val: number) => string;
}) {
  const formattedValue = () => {
    if (value === null) return "…";
    if (typeof value === "number") {
      return formatter ? formatter(value) : value.toLocaleString();
    }
    return value;
  };

  return (
    <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm">
      <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider truncate">
        {title}
      </h3>
      <p className="mt-2 text-3xl font-bold text-slate-900 truncate">
        {formattedValue()}{" "}
        {unit && <span className="text-lg text-slate-400 font-normal">{unit}</span>}
      </p>
    </div>
  );
}
