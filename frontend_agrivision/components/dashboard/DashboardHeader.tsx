import React from "react";

export default function DashboardHeader({ title = "Dashboard de AgriVision", subtitle = "Resumen general de la finca" }: { title?: string; subtitle?: string }) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-semibold">{title}</h1>
        <div className="text-sm text-gray-500">{subtitle}</div>
      </div>
    </div>
  );
}
