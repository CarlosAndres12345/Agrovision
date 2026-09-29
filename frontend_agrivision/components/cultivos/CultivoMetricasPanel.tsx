"use client";

import React, { useCallback, useEffect, useState } from "react";

import { getCultivoMetricas } from "../../lib/api";
import type { CultivoMetricasResponse } from "../../types/metrica";

type Props = {
  cultivoId: number;
};

const METRICAS_ORDENADAS = [
  { key: "cantidad_frutos_ultimo", label: "Cantidad de frutos", unidad: "", accent: "bg-emerald-500" },
  { key: "frutos_maduros_ultimo", label: "Frutos maduros", unidad: "", accent: "bg-lime-500" },
  { key: "estimacion_cosecha_ultima", label: "Estimación de cosecha", unidad: "kg", accent: "bg-green-700" },
  { key: "porcentaje_madurez_ultimo", label: "Porcentaje de madurez", unidad: "%", accent: "bg-teal-600" },
] as const;

export default function CultivoMetricasPanel({ cultivoId }: Props) {
  const [data, setData] = useState<CultivoMetricasResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resultado = await getCultivoMetricas(cultivoId);
      setData(resultado);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "No se pudo conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  }, [cultivoId]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-green-600 border-r-transparent" />
        Cargando métricas...
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        <p className="font-medium">Error de conexión</p>
        <p className="mt-1 text-xs">{error}</p>
        <button
          type="button"
          onClick={cargar}
          className="mt-2 rounded-md border border-red-300 bg-white px-3 py-1 text-xs font-medium text-red-700 hover:bg-red-50"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!data || data.historial.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
        <p className="text-sm font-medium text-gray-700">Sin análisis registrados</p>
        <p className="text-xs text-gray-400">Procesa imágenes de este cultivo para ver métricas aquí.</p>
      </div>
    );
  }

  const ultimoIntento = data.historial[0];
  const fallaUltimoIntento = ultimoIntento.estado === "ERROR";

  return (
    <div className="space-y-4">
      {fallaUltimoIntento && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <p className="font-medium">El último procesamiento falló</p>
          {ultimoIntento.mensaje_error && <p className="mt-1 text-xs">{ultimoIntento.mensaje_error}</p>}
          <p className="mt-1 text-xs text-red-500">
            {new Date(ultimoIntento.fecha_procesamiento).toLocaleString()}
          </p>
        </div>
      )}

      {data.ultimo_analisis && data.resumen ? (
        <>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs text-gray-500">
              Último procesamiento completado: {new Date(data.ultimo_analisis.fecha_procesamiento).toLocaleString()}
            </span>
            <button
              type="button"
              onClick={cargar}
              className="rounded-md border border-gray-300 px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-50"
            >
              Actualizar
            </button>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {METRICAS_ORDENADAS.map((metrica) => {
              const valor = data.resumen![metrica.key];
              return (
                <div key={metrica.key} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-xs uppercase tracking-wide text-gray-500">{metrica.label}</div>
                      {valor !== null ? (
                        <div className="mt-2 flex items-end gap-1 text-2xl font-semibold text-gray-900">
                          <span>{valor}</span>
                          {metrica.unidad && <span className="text-sm font-medium text-gray-500">{metrica.unidad}</span>}
                        </div>
                      ) : (
                        <div className="mt-2 text-sm text-gray-400">Sin datos</div>
                      )}
                    </div>
                    <div className={`h-10 w-10 rounded-lg ${metrica.accent} opacity-90`} />
                  </div>
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">Todavía no hay un procesamiento completado para este cultivo.</p>
          <button
            type="button"
            onClick={cargar}
            className="rounded-md border border-gray-300 px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-50"
          >
            Actualizar
          </button>
        </div>
      )}

      {data.historial.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">Historial reciente</p>
          <div className="divide-y divide-gray-100 overflow-hidden rounded-lg border border-gray-200">
            {data.historial.map((a) => (
              <div key={a.id} className="flex items-center justify-between gap-3 bg-white px-3 py-2 text-sm">
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                      a.estado === "COMPLETADO"
                        ? "bg-emerald-100 text-emerald-700"
                        : a.estado === "COMPLETADO_CON_ERRORES"
                          ? "bg-orange-100 text-orange-700"
                          : a.estado === "ERROR"
                            ? "bg-red-100 text-red-700"
                            : "bg-amber-100 text-amber-700"
                    }`}
                  >
                    {a.estado}
                  </span>
                  <span className="text-gray-500">{new Date(a.fecha_procesamiento).toLocaleString()}</span>
                </div>
                <span className="text-gray-700">
                  {a.estado === "COMPLETADO"
                    ? `${a.cantidad_frutos ?? "—"} frutos, ${a.frutos_maduros ?? "—"} maduros`
                    : a.mensaje_error || "—"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
