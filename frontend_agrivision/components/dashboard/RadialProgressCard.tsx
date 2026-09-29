import React from "react";

function CircularProgress({ percent = 0, size = 96 }: { percent: number; size?: number }) {
  const stroke = 8;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;

  return (
    <svg width={size} height={size} className="block">
      <defs>
        <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#34d399" />
          <stop offset="100%" stopColor="#059669" />
        </linearGradient>
      </defs>
      <g transform={`translate(${size / 2}, ${size / 2})`}>
        <circle r={radius} fill="none" stroke="#e6e6e6" strokeWidth={stroke} />
        <circle
          r={radius}
          fill="none"
          stroke="url(#g1)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${circumference} ${circumference}`}
          strokeDashoffset={offset}
          transform="rotate(-90)"
        />
        <text x="0" y="6" textAnchor="middle" fontSize="18" fontWeight={700} fill="#064e3b">{percent}%</text>
      </g>
    </svg>
  );
}

export default function RadialProgressCard({
  percent,
  title = "Madurez",
}: {
  percent: number | null;
  title?: string;
}) {
  return (
    <div className="av-card p-4 flex items-center gap-4">
      <div>
        <div className="text-sm text-gray-500">{title}</div>
        <div className="mt-2">
          <CircularProgress percent={percent ?? 0} />
        </div>
      </div>
      <div>
        <div className="text-sm text-gray-500">Estado general</div>
        <div className="text-lg font-semibold mt-2">
          {percent !== null ? `${percent}% Madurez` : "Sin datos"}
        </div>
        <div className="text-sm text-gray-400">
          {percent !== null ? "Calculado a partir del último análisis de cada cultivo." : "Procesa imágenes para ver el avance."}
        </div>
      </div>
    </div>
  );
}
