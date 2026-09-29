"use client";

import React, { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import type { Cultivo } from "../../types/cultivo";
import type { Lote } from "../../types/lote";
import type { MetricaTipo } from "../../types/metrica";
import { createMetrica } from "../../lib/api";

const TIPOS_RESULTADO: { value: MetricaTipo; label: string }[] = [
  { value: "cantidad_frutos", label: "Cantidad de frutos" },
  { value: "frutos_maduros", label: "Frutos maduros" },
  { value: "estimacion_cosecha", label: "Estimación de cosecha" },
  { value: "porcentaje_madurez", label: "Porcentaje de madurez" },
];

type Props = {
  cultivos: Cultivo[];
  lotes: Lote[];
  defaultCultivoId?: number;
  defaultLoteId?: number;
};

type FormState = {
  cultivo_id: string;
  lote_id: string;
  tipo_resultado: string;
  valor: string;
  unidad: string;
  fecha_registro: string;
  descripcion: string;
};

export default function MetricaForm({ cultivos, lotes, defaultCultivoId, defaultLoteId }: Props) {
  const router = useRouter();

  const [formData, setFormData] = useState<FormState>({
    cultivo_id: defaultCultivoId ? String(defaultCultivoId) : "",
    lote_id: defaultLoteId ? String(defaultLoteId) : "",
    tipo_resultado: "",
    valor: "",
    unidad: "",
    fecha_registro: "",
    descripcion: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filteredLotes = useMemo(
    () =>
      formData.cultivo_id
        ? lotes.filter((l) => l.cultivo_id === Number(formData.cultivo_id))
        : [],
    [lotes, formData.cultivo_id],
  );

  function updateField(field: keyof FormState, value: string) {
    setFormData((prev) => {
      if (field === "cultivo_id") {
        return { ...prev, cultivo_id: value, lote_id: "" };
      }
      return { ...prev, [field]: value };
    });
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const cultivoId = Number(formData.cultivo_id);
      const loteId = formData.lote_id ? Number(formData.lote_id) : null;

      // datetime-local da "YYYY-MM-DDTHH:MM" (sin segundos) — se normaliza antes de enviar
      const fechaNorm =
        formData.fecha_registro.length === 16
          ? `${formData.fecha_registro}:00`
          : formData.fecha_registro;

      await createMetrica({
        cultivo_id: cultivoId,
        lote_id: loteId,
        tipo_resultado: formData.tipo_resultado as MetricaTipo,
        valor: formData.valor,
        unidad: formData.unidad,
        fecha_registro: fechaNorm,
        descripcion: formData.descripcion,
        fuente: "registro_manual",
      });

      router.push(loteId ? `/lotes/${loteId}` : `/cultivos/${cultivoId}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo registrar la métrica.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">

        <label className="space-y-2">
          <span className="text-sm font-medium text-gray-700">Cultivo *</span>
          <select
            value={formData.cultivo_id}
            onChange={(e) => updateField("cultivo_id", e.target.value)}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
            required
          >
            <option value="">Selecciona un cultivo</option>
            {cultivos.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre} — {c.tipo_fruto}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-gray-700">
            Lote{" "}
            <span className="font-normal text-gray-400">(opcional)</span>
          </span>
          <select
            value={formData.lote_id}
            onChange={(e) => updateField("lote_id", e.target.value)}
            disabled={!formData.cultivo_id}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100 disabled:bg-gray-50 disabled:text-gray-400"
          >
            <option value="">Sin lote</option>
            {filteredLotes.map((l) => (
              <option key={l.id} value={l.id}>
                {l.nombre}
              </option>
            ))}
          </select>
          {formData.cultivo_id && filteredLotes.length === 0 ? (
            <span className="text-xs text-gray-400">
              Este cultivo no tiene lotes registrados.
            </span>
          ) : null}
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-gray-700">Tipo de resultado *</span>
          <select
            value={formData.tipo_resultado}
            onChange={(e) => updateField("tipo_resultado", e.target.value)}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
            required
          >
            <option value="">Selecciona un tipo</option>
            {TIPOS_RESULTADO.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-gray-700">Valor *</span>
          <input
            type="number"
            step="any"
            min="0"
            value={formData.valor}
            onChange={(e) => updateField("valor", e.target.value)}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
            required
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-gray-700">
            Unidad{" "}
            <span className="font-normal text-gray-400">(opcional)</span>
          </span>
          <input
            type="text"
            value={formData.unidad}
            onChange={(e) => updateField("unidad", e.target.value)}
            placeholder="frutos, kg, %, etc."
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-gray-700">Fecha y hora de registro *</span>
          <input
            type="datetime-local"
            value={formData.fecha_registro}
            onChange={(e) => updateField("fecha_registro", e.target.value)}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
            required
          />
        </label>

        <label className="space-y-2 md:col-span-2">
          <span className="text-sm font-medium text-gray-700">
            Descripción{" "}
            <span className="font-normal text-gray-400">(opcional)</span>
          </span>
          <textarea
            rows={3}
            value={formData.descripcion}
            onChange={(e) => updateField("descripcion", e.target.value)}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
          />
        </label>
      </div>

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? "Guardando..." : "Registrar métrica"}
        </button>
      </div>
    </form>
  );
}
