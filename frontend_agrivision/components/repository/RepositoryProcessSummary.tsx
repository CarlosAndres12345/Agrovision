"use client";

import React from "react";
import Link from "next/link";

import type { RepositoryProcessAllResponse } from "../../types/repository";

type Props = {
  resultado: RepositoryProcessAllResponse;
  cultivoId: number;
  onVolver: () => void;
};

const TITULOS: Record<RepositoryProcessAllResponse["status"], string> = {
  SIN_PENDIENTES: "No hay imágenes pendientes por procesar",
  COMPLETADO: "Procesamiento finalizado",
  COMPLETADO_CON_ERRORES: "Procesamiento finalizado con errores",
  ERROR: "No fue posible completar el procesamiento",
};

/** Tarjeta de cierre del flujo automático — reemplaza cualquier confirmación por selección manual. */
export default function RepositoryProcessSummary({ resultado, cultivoId, onVolver }: Props) {
  const tono =
    resultado.status === "COMPLETADO"
      ? "border-green-200 bg-green-50"
      : resultado.status === "SIN_PENDIENTES"
        ? "border-gray-200 bg-gray-50"
        : resultado.status === "COMPLETADO_CON_ERRORES"
          ? "border-amber-200 bg-amber-50"
          : "border-red-200 bg-red-50";

  return (
    <div className={`space-y-4 rounded-lg border p-4 ${tono}`}>
      <h3 className="text-sm font-semibold text-gray-900">{TITULOS[resultado.status]}</h3>

      {resultado.status === "SIN_PENDIENTES" && (
        <p className="text-sm text-gray-600">Todas las imágenes de este cultivo ya fueron procesadas.</p>
      )}

      {resultado.status === "ERROR" && (
        <div className="text-sm text-red-700">
          <p>{resultado.message ?? "No fue posible completar el procesamiento."}</p>
          {resultado.errores && resultado.errores.length > 0 && (
            <ul className="mt-2 list-inside list-disc text-xs">
              {resultado.errores.slice(0, 5).map((e) => (
                <li key={e.imagen_id}>
                  Imagen #{e.imagen_id}: {e.motivo}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {(resultado.status === "COMPLETADO" || resultado.status === "COMPLETADO_CON_ERRORES") && resultado.metrics && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <div className="rounded-md bg-white px-3 py-2 shadow-sm">
            <div className="text-xs uppercase tracking-wide text-gray-500">Imágenes procesadas</div>
            <div className="mt-1 text-lg font-semibold text-gray-900">{resultado.imagenes_procesadas}</div>
          </div>
          <div className="rounded-md bg-white px-3 py-2 shadow-sm">
            <div className="text-xs uppercase tracking-wide text-gray-500">Imágenes con error</div>
            <div className="mt-1 text-lg font-semibold text-gray-900">{resultado.imagenes_con_error}</div>
          </div>
          <div className="rounded-md bg-white px-3 py-2 shadow-sm">
            <div className="text-xs uppercase tracking-wide text-gray-500">Cantidad de frutos</div>
            <div className="mt-1 text-lg font-semibold text-gray-900">{resultado.metrics.cantidad_frutos}</div>
          </div>
          <div className="rounded-md bg-white px-3 py-2 shadow-sm">
            <div className="text-xs uppercase tracking-wide text-gray-500">Frutos maduros</div>
            <div className="mt-1 text-lg font-semibold text-gray-900">{resultado.metrics.frutos_maduros}</div>
          </div>
          <div className="rounded-md bg-white px-3 py-2 shadow-sm">
            <div className="text-xs uppercase tracking-wide text-gray-500">Porcentaje de madurez</div>
            <div className="mt-1 text-lg font-semibold text-gray-900">
              {resultado.metrics.porcentaje_madurez != null ? `${resultado.metrics.porcentaje_madurez}%` : "Sin datos"}
            </div>
          </div>
          <div className="rounded-md bg-white px-3 py-2 shadow-sm">
            <div className="text-xs uppercase tracking-wide text-gray-500">Estimación de cosecha</div>
            <div className="mt-1 text-lg font-semibold text-gray-900">{resultado.metrics.estimacion_cosecha} kg</div>
          </div>
        </div>
      )}

      {resultado.errores && resultado.errores.length > 0 && resultado.status === "COMPLETADO_CON_ERRORES" && (
        <details className="text-xs text-gray-600">
          <summary className="cursor-pointer font-medium text-gray-700">
            Ver imágenes con error ({resultado.errores.length})
          </summary>
          <ul className="mt-2 list-inside list-disc">
            {resultado.errores.map((e) => (
              <li key={e.imagen_id}>
                Imagen #{e.imagen_id}: {e.motivo}
              </li>
            ))}
          </ul>
        </details>
      )}

      <div className="flex flex-wrap gap-2 pt-1">
        {resultado.status !== "SIN_PENDIENTES" && resultado.status !== "ERROR" && (
          <Link
            href={`/cultivos/${cultivoId}`}
            className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
          >
            Ver cultivo
          </Link>
        )}
        <button
          type="button"
          onClick={onVolver}
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Volver al repositorio
        </button>
      </div>
    </div>
  );
}
