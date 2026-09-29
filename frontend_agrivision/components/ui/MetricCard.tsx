import React from "react";

type Props = {
  title: string;
  value: string | number;
  subtitle?: string;
  accent?: string;
  icon?: React.ReactNode;
};

export default function MetricCard({ title, value, subtitle, accent = "bg-green-500", icon }: Props) {
  return (
    <div className="av-card p-4 flex items-center gap-4">
      {icon ? <div className={`p-2 rounded ${accent} text-white`}>{icon}</div> : null}
      <div>
        <div className="text-sm text-gray-500">{title}</div>
        <div className="text-2xl font-semibold">{value}</div>
        {subtitle ? <div className="text-sm text-gray-400">{subtitle}</div> : null}
      </div>
    </div>
  );
}
