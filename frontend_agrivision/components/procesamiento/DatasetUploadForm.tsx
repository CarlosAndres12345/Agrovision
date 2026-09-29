"use client";

import React, { useState, useEffect, useRef } from "react";
import { getCultivos, getLotesByCultivo, procesarDataset } from "../../lib/api";
import type { Cultivo } from "../../types/cultivo";
import type { Lote } from "../../types/lote";
import type { ProcesamientoResponse } from "../../types/metrica";

const LABELS: Record<string, string> = {
  cantidad_frutos: "Cantidad de frutos",
  frutos_maduros: "Frutos maduros",
  estimacion_cosecha: "Estimación de cosecha",
  porcentaje_madurez: "Porcentaje de madurez",
};

const ACCENT: Record<string, string> = {
  cantidad_frutos: "bg-emerald-500",
  frutos_maduros: "bg-lime-500",
  estimacion_cosecha: "bg-green-700",
  porcentaje_madurez: "bg-teal-600",
};

interface Props {
  initialCultivoId?: number | null;
  initialLoteId?: number | null;
}

export default function DatasetUploadForm({
  initialCultivoId = null,
  initialLoteId = null,
}: Props) {
  const [cultivos, setCultivos] = useState<Cultivo[]>([]);
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [cultivoId, setCultivoId] = useState<number | null>(initialCultivoId);
  const [loteId, setLoteId] = useState<number | null>(initialLoteId);
  const [imagenes, setImagenes] = useState<File[]>([]);
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultado, setResultado] = useState<ProcesamientoResponse | null>(null);
  const isFirstLoteLoad = useRef(true);

  useEffect(() => {
    getCultivos()
      .then(setCultivos)
      .catch(() => setError("No se pudieron cargar los cultivos."));
  }, []);

  useEffect(() => {
    if (cultivoId == null) {
      setLotes([]);
      if (!isFirstLoteLoad.current) setLoteId(null);
      isFirstLoteLoad.current = false;
      return;
    }
    getLotesByCultivo(cultivoId)
      .then((data) => {
        setLotes(data);
        // Solo resetear lote si el usuario cambió el cultivo manualmente (no en el mount inicial)
        if (!isFirstLoteLoad.current) setLoteId(null);
        isFirstLoteLoad.current = false;
      })
      .catch(() => {
        setLotes([]);
        isFirstLoteLoad.current = false;
      });
  }, [cultivoId]);

  function handleArchivos(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files ? Array.from(e.target.files) : [];
    setImagenes(files);
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResultado(null);

    if (cultivoId == null) {
      setError("Selecciona un cultivo.");
      return;
    }
    if (imagenes.length === 0) {
      setError("Carga al menos una imagen.");
      return;
    }

    setProcesando(true);
    try {
      const res = await procesarDataset(cultivoId, imagenes, loteId);
      setResultado(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al procesar el dataset.";
      setError(msg);
    } finally {
      setProcesando(false);
    }
  }

  function handleReset() {
    setResultado(null);
    setImagenes([]);
    setError(null);
  }

  if (resultado) {
    return (
      <div className="space-y-5">
        <div className="rounded-md bg-green-50 border border-green-200 px-4 py-3">
          <p className="text-sm font-semibold text-green-800">
            Dataset procesado correctamente
          </p>
          <p className="text-xs text-green-700 mt-0.5">
            {resultado.imagenes_procesadas} imagen
            {resultado.imagenes_procesadas !== 1 ? "es" : ""} analizadas
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {resultado.metricas.map((m) => (
            <div
              key={m.tipo_resultado}
              className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500">
                    {LABELS[m.tipo_resultado] ?? m.tipo_resultado}
                  </div>
                  <div className="mt-1 flex items-end gap-1 text-2xl font-semibold text-gray-900">
                    <span>{m.valor}</span>
                    {m.unidad && (
                      <span className="text-sm font-medium text-gray-500">{m.unidad}</span>
                    )}
                  </div>
                </div>
                <div
                  className={`h-9 w-9 rounded-lg ${ACCENT[m.tipo_resultado] ?? "bg-gray-400"} opacity-90 shrink-0`}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap gap-3 pt-1">
          <button
            onClick={handleReset}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Procesar otro dataset
          </button>
          {resultado.lote_id ? (
            <a
              href={`/lotes/${resultado.lote_id}`}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 transition-colors"
            >
              Ver lote
            </a>
          ) : (
            <a
              href={`/cultivos/${resultado.cultivo_id}`}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 transition-colors"
            >
              Ver cultivo
            </a>
          )}
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Cultivo */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Cultivo <span className="text-red-500">*</span>
        </label>
        <select
          value={cultivoId ?? ""}
          onChange={(e) => setCultivoId(e.target.value ? Number(e.target.value) : null)}
          className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
          required
        >
          <option value="">Seleccionar cultivo...</option>
          {cultivos.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre} — {c.tipo_fruto}
            </option>
          ))}
        </select>
      </div>

      {/* Lote (optional) */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Lote <span className="text-gray-400 font-normal">(opcional)</span>
        </label>
        <select
          value={loteId ?? ""}
          onChange={(e) => setLoteId(e.target.value ? Number(e.target.value) : null)}
          disabled={cultivoId == null || lotes.length === 0}
          className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
        >
          <option value="">Sin lote específico</option>
          {lotes.map((l) => (
            <option key={l.id} value={l.id}>
              {l.nombre}
            </option>
          ))}
        </select>
        {cultivoId != null && lotes.length === 0 && (
          <p className="mt-1 text-xs text-gray-400">
            Este cultivo no tiene lotes registrados.
          </p>
        )}
      </div>

      {/* Imágenes */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Imágenes del cultivo <span className="text-red-500">*</span>
        </label>
        <label className="mt-1 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-gray-300 px-6 py-10 text-center transition-colors hover:border-green-400 hover:bg-green-50/30">
          <svg
            className="h-10 w-10 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
            aria-hidden="true"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className="text-sm text-gray-600">
            <span className="font-medium text-green-600">Seleccionar imágenes</span>
            {" "}o arrastra aquí
          </span>
          <span className="text-xs text-gray-400">JPG, PNG, WEBP, BMP — múltiples archivos</span>
          {imagenes.length > 0 && (
            <span className="mt-1 text-sm font-semibold text-green-700">
              {imagenes.length} imagen{imagenes.length !== 1 ? "es" : ""} seleccionada
              {imagenes.length !== 1 ? "s" : ""}
            </span>
          )}
          <input
            type="file"
            multiple
            accept=".jpg,.jpeg,.png,.webp,.bmp"
            onChange={handleArchivos}
            className="sr-only"
          />
        </label>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={procesando || cultivoId == null || imagenes.length === 0}
        className="w-full rounded-md bg-green-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {procesando ? "Procesando..." : "Procesar dataset"}
      </button>
    </form>
  );
}
