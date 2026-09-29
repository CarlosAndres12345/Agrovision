"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

import type { Cultivo } from "../../types/cultivo";
import type { Lote, LoteInput } from "../../types/lote";
import { createLote, updateLote } from "../../lib/api";

type Props = {
  mode: "create" | "edit";
  cultivos: Cultivo[];
  initialValues?: Lote | null;
  redirectTo: string;
};

const defaultValues: LoteInput = {
  cultivo_id: "",
  nombre: "",
  ancho: "",
  largo: "",
  area_lote: "",
  descripcion: "",
};

export default function LoteForm({ mode, cultivos, initialValues, redirectTo }: Props) {
  const router = useRouter();
  const hasStoredDimensions = Boolean(initialValues?.ancho && initialValues?.largo);
  const requireDimensions = mode === "create" || hasStoredDimensions;
  const [formData, setFormData] = useState<LoteInput>({
    cultivo_id: initialValues?.cultivo_id ? String(initialValues.cultivo_id) : defaultValues.cultivo_id,
    nombre: initialValues?.nombre ?? defaultValues.nombre,
    ancho: initialValues?.ancho ?? defaultValues.ancho,
    largo: initialValues?.largo ?? defaultValues.largo,
    area_lote: initialValues?.area_lote ?? defaultValues.area_lote,
    descripcion: initialValues?.descripcion ?? defaultValues.descripcion,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateField(field: keyof LoteInput, value: string) {
    setFormData((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "create") {
        await createLote(formData);
      } else {
        if (!initialValues) {
          throw new Error("No se pudo cargar el lote para editar.");
        }
        await updateLote(initialValues.id, formData);
      }

      router.push(redirectTo);
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "No se pudo guardar el lote.");
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
            onChange={(event) => updateField("cultivo_id", event.target.value)}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
            required
          >
            <option value="">Selecciona un cultivo</option>
            {cultivos.map((cultivo) => (
              <option key={cultivo.id} value={cultivo.id}>
                {cultivo.nombre} — {cultivo.tipo_fruto}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-gray-700">Nombre *</span>
          <input
            value={formData.nombre}
            onChange={(event) => updateField("nombre", event.target.value)}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
            required
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-gray-700">Ancho (m) *</span>
          <input
            type="number"
            step="0.01"
            value={formData.ancho}
            onChange={(event) => updateField("ancho", event.target.value)}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
            required={requireDimensions}
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-gray-700">Largo (m) *</span>
          <input
            type="number"
            step="0.01"
            value={formData.largo}
            onChange={(event) => updateField("largo", event.target.value)}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
            required={requireDimensions}
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-gray-700">Área calculada</span>
          <input
            value={
              formData.ancho && formData.largo
                ? (Number(formData.ancho) * Number(formData.largo)).toFixed(2)
                : formData.area_lote
            }
            readOnly
            className="w-full rounded-md border border-gray-200 bg-slate-50 px-3 py-2 text-sm text-slate-600 outline-none"
          />
        </label>

        <label className="space-y-2 md:col-span-2">
          <span className="text-sm font-medium text-gray-700">Descripción</span>
          <textarea
            rows={4}
            value={formData.descripcion}
            onChange={(event) => updateField("descripcion", event.target.value)}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
          />
        </label>

        {!hasStoredDimensions && mode === "edit" ? (
          <p className="md:col-span-2 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            Este lote fue creado antes de guardar ancho y largo. Puedes editarlo sin completar
            dimensiones, o capturarlas ahora para que el área quede calculada automáticamente.
          </p>
        ) : null}
      </div>

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}

      {cultivos.length === 0 ? (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          No hay cultivos disponibles. Crea un cultivo primero para poder registrar lotes.
        </div>
      ) : null}

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={loading || cultivos.length === 0}
          className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? "Guardando..." : mode === "create" ? "Crear lote" : "Guardar cambios"}
        </button>
      </div>
    </form>
  );
}
