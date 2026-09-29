"use client";

import React from "react";

import type { Cultivo } from "../../types/cultivo";
import type { Lote } from "../../types/lote";
import type { ImagenRepositorioEstado } from "../../types/repository";

type Props = {
  cultivos: Cultivo[];
  lotes: Lote[];
  cultivoId: number | null;
  loteId: number | null;
  estado: ImagenRepositorioEstado | "";
  onCultivoChange: (cultivoId: number | null) => void;
  onLoteChange: (loteId: number | null) => void;
  onEstadoChange: (estado: ImagenRepositorioEstado | "") => void;
};

const ESTADOS: { value: ImagenRepositorioEstado | ""; label: string }[] = [
  { value: "", label: "Todos los estados" },
  { value: "disponible", label: "Pendiente" },
  { value: "procesando", label: "Procesando" },
  { value: "procesada", label: "Procesada" },
  { value: "error", label: "Error" },
];

export default function RepositoryFilters({
  cultivos,
  lotes,
  cultivoId,
  loteId,
  estado,
  onCultivoChange,
  onLoteChange,
  onEstadoChange,
}: Props) {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      <label className="space-y-1">
        <span className="text-xs font-medium uppercase tracking-wide text-gray-500">Cultivo</span>
        <select
          value={cultivoId ?? ""}
          onChange={(e) => onCultivoChange(e.target.value ? Number(e.target.value) : null)}
          className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
        >
          <option value="">Seleccionar cultivo...</option>
          {cultivos.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre} — {c.tipo_fruto}
            </option>
          ))}
        </select>
      </label>

      <label className="space-y-1">
        <span className="text-xs font-medium uppercase tracking-wide text-gray-500">Lote</span>
        <select
          value={loteId ?? ""}
          onChange={(e) => onLoteChange(e.target.value ? Number(e.target.value) : null)}
          disabled={cultivoId == null || lotes.length === 0}
          className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500 disabled:bg-gray-100 disabled:text-gray-400"
        >
          <option value="">Todos los lotes</option>
          {lotes.map((l) => (
            <option key={l.id} value={l.id}>
              {l.nombre}
            </option>
          ))}
        </select>
      </label>

      <label className="space-y-1">
        <span className="text-xs font-medium uppercase tracking-wide text-gray-500">Estado</span>
        <select
          value={estado}
          onChange={(e) => onEstadoChange(e.target.value as ImagenRepositorioEstado | "")}
          className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
        >
          {ESTADOS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
