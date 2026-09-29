"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

import type { Cultivo, CultivoInput, CultivoLocation, CultivoLocationInput } from "../../types/cultivo";
import { createCultivo, updateCultivo } from "../../lib/api";
import CultivoLocationSection from "./CultivoLocationSection";

type Props = {
  mode: "create" | "edit";
  initialValues?: Cultivo | null;
  redirectTo: string;
};

const defaultValues = {
  nombre: "",
  tipo_fruto: "",
  ubicacion: "",
  area_sembrada: "",
  fecha_siembra: "",
  descripcion: "",
};

function toLocationInput(location?: CultivoLocation | null): CultivoLocationInput | null {
  if (!location) return null;
  return {
    latitude: Number(location.latitude),
    longitude: Number(location.longitude),
    address: location.address || undefined,
    source: location.source,
    accuracy_meters: location.accuracy_meters != null ? Number(location.accuracy_meters) : null,
    captured_at: location.captured_at,
  };
}

export default function CultivoForm({ mode, initialValues, redirectTo }: Props) {
  const router = useRouter();
  const [formData, setFormData] = useState({
    nombre: initialValues?.nombre ?? defaultValues.nombre,
    tipo_fruto: initialValues?.tipo_fruto ?? defaultValues.tipo_fruto,
    ubicacion: initialValues?.ubicacion ?? defaultValues.ubicacion,
    area_sembrada: initialValues?.area_sembrada ?? defaultValues.area_sembrada,
    fecha_siembra: initialValues?.fecha_siembra ?? defaultValues.fecha_siembra,
    descripcion: initialValues?.descripcion ?? defaultValues.descripcion,
  });
  const [location, setLocation] = useState<CultivoLocationInput | null>(() =>
    toLocationInput(initialValues?.location),
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateField(field: keyof typeof formData, value: string) {
    setFormData((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const payload: CultivoInput = { ...formData, location };

      if (mode === "create") {
        await createCultivo(payload);
      } else {
        if (!initialValues) {
          throw new Error("No se pudo cargar el cultivo para editar.");
        }
        await updateCultivo(initialValues.id, payload);
      }

      router.push(redirectTo);
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "No se pudo guardar el cultivo.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
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
          <span className="text-sm font-medium text-gray-700">Tipo de fruto *</span>
          <input
            value={formData.tipo_fruto}
            onChange={(event) => updateField("tipo_fruto", event.target.value)}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
            required
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-gray-700">Ubicación *</span>
          <input
            value={formData.ubicacion}
            onChange={(event) => updateField("ubicacion", event.target.value)}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
            placeholder="Ciudad, Departamento"
            required
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-gray-700">Área sembrada *</span>
          <input
            type="number"
            step="0.01"
            value={formData.area_sembrada}
            onChange={(event) => updateField("area_sembrada", event.target.value)}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
            required
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium text-gray-700">Fecha de siembra *</span>
          <input
            type="date"
            value={formData.fecha_siembra}
            onChange={(event) => updateField("fecha_siembra", event.target.value)}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:border-green-500 focus:ring-2 focus:ring-green-100"
            required
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

        <div className="md:col-span-2">
          <CultivoLocationSection value={location} onChange={setLocation} />
        </div>
      </div>

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? "Guardando..." : mode === "create" ? "Crear cultivo" : "Guardar cambios"}
        </button>
      </div>
    </form>
  );
}
