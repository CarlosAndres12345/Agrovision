import React from "react";
import type { EstadoAnalisis } from "../../types/metrica";

type Props = {
  status?: EstadoAnalisis | null;
};

const LABELS: Record<EstadoAnalisis, string> = {
  pendiente: "Pendiente",
  procesando: "Procesando",
  procesado: "Procesado",
  procesado_con_errores: "Con errores",
  error: "Error",
};

const STYLES: Record<EstadoAnalisis, string> = {
  pendiente: "bg-slate-100 text-slate-700",
  procesando: "bg-blue-100 text-blue-800",
  procesado: "bg-green-100 text-green-800",
  procesado_con_errores: "bg-amber-100 text-amber-800",
  error: "bg-red-100 text-red-800",
};

export default function StatusBadge({ status }: Props) {
  if (!status) {
    return (
      <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
        Sin análisis
      </span>
    );
  }

  const label = LABELS[status] ?? status;
  const cls = STYLES[status] ?? "bg-gray-100 text-gray-800";

  return <span className={`px-2 py-1 rounded-full text-xs font-medium ${cls}`}>{label}</span>;
}
