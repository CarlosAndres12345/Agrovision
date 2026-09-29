import Link from "next/link";
import React from "react";

import PageContainer from "../../../../components/layout/PageContainer";
import SectionCard from "../../../../components/ui/SectionCard";
import StatusBadge from "../../../../components/ui/StatusBadge";
import { getCookieHeader } from "../../../../lib/server-cookies";
import {
  getCultivoByIdWithCookie,
  getLoteByIdWithCookie,
  getMetricasByLoteWithCookie,
  getUltimoAnalisisLote,
} from "../../../../lib/api";
import type { MetricaRaw, Analisis } from "../../../../types/metrica";
import { analisisImagenUrl } from "../../../../types/metrica";

export const dynamic = "force-dynamic";

export default async function LoteDetallePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const cookieHeader = await getCookieHeader();
  const lote = await getLoteByIdWithCookie(id, cookieHeader);

  if (!lote) {
    return (
      <PageContainer title={`Detalle de lote #${id}`}>
        <SectionCard title="Lote no encontrado">
          <p className="text-sm text-gray-600">No existe un lote con ese identificador.</p>
        </SectionCard>
      </PageContainer>
    );
  }

  const cultivo = await getCultivoByIdWithCookie(lote.cultivo_id, cookieHeader);
  let metricas: MetricaRaw[] | null = null;
  let metricasError: string | null = null;
  let ultimoAnalisis: Analisis | null = null;

  try {
    metricas = await getMetricasByLoteWithCookie(lote.id, cookieHeader);
  } catch (err: unknown) {
    metricas = null;
    metricasError = err instanceof Error ? err.message : "Error al cargar métricas.";
  }

  try {
    ultimoAnalisis = await getUltimoAnalisisLote(lote.id);
  } catch {
    // Si no hay análisis, se muestra sin imágenes
  }

  const metricasMostrar = metricas ?? [];

  return (
    <PageContainer title={`Detalle de lote #${id}`}>
      <div className="grid gap-6 lg:grid-cols-3">
        <SectionCard title={lote.nombre} className="lg:col-span-2">
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={ultimoAnalisis?.estado ?? null} />
            <span className="text-sm text-gray-500">Área: {lote.area_lote} ha</span>
            {lote.ancho && lote.largo ? (
              <span className="text-sm text-gray-500">Dimensiones: {lote.ancho} x {lote.largo} m</span>
            ) : null}
            <span className="text-sm text-gray-500">
              Cultivo: {cultivo ? cultivo.nombre : `Cultivo #${lote.cultivo_id}`}
            </span>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <div className="rounded-md bg-gray-50 p-4">
              <div className="text-xs uppercase tracking-wide text-gray-500">ID</div>
              <div className="mt-1 text-xl font-semibold text-gray-900">{lote.id}</div>
            </div>
            <div className="rounded-md bg-gray-50 p-4">
              <div className="text-xs uppercase tracking-wide text-gray-500">Área lote</div>
              <div className="mt-1 text-xl font-semibold text-gray-900">{lote.area_lote} ha</div>
            </div>
            <div className="rounded-md bg-gray-50 p-4">
              <div className="text-xs uppercase tracking-wide text-gray-500">Cultivo</div>
              <div className="mt-1 text-sm font-semibold text-gray-900">
                {cultivo ? cultivo.nombre : `Cultivo #${lote.cultivo_id}`}
              </div>
            </div>
          </div>

          <div className="mt-6">
            <h3 className="text-sm font-medium text-gray-700">Descripción</h3>
            <p className="mt-2 text-sm leading-6 text-gray-600">
              {lote.descripcion || "Sin descripción registrada."}
            </p>
          </div>
        </SectionCard>

        <SectionCard title="Resumen rápido">
          <div className="space-y-4 text-sm text-gray-600">
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-500">Cultivo asociado</div>
              <div className="mt-1 font-medium text-gray-900">
                {cultivo ? cultivo.nombre : `Cultivo #${lote.cultivo_id}`}
              </div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-500">Tipo de fruto</div>
              <div className="mt-1 font-medium text-gray-900">
                {cultivo ? cultivo.tipo_fruto : "No disponible"}
              </div>
            </div>
            <div className="flex flex-wrap gap-2 pt-2">
              <Link
                href={`/lotes/${lote.id}/editar`}
                className="inline-flex rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
              >
                Editar lote
              </Link>
              <Link
                href={`/procesamiento/nuevo?cultivo_id=${lote.cultivo_id}&lote_id=${lote.id}&tab=drive`}
                className="inline-flex rounded-md border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-100"
              >
                Subir a Drive
              </Link>
              <Link
                href={`/procesamiento/nuevo?cultivo_id=${lote.cultivo_id}&lote_id=${lote.id}&tab=directo`}
                className="inline-flex rounded-md border border-green-200 bg-green-50 px-4 py-2 text-sm font-medium text-green-700 hover:bg-green-100"
              >
                Procesar dataset
              </Link>
            </div>
          </div>
        </SectionCard>
      </div>

      <div className="mt-6">
        <SectionCard title="Métricas del lote" className="lg:col-span-3">
          {metricasError ? (
            <div className="text-sm text-red-600">Error al cargar métricas: {metricasError}</div>
          ) : metricasMostrar.length === 0 ? (
            <div className="text-sm text-gray-600">No hay métricas registradas para este lote.</div>
          ) : (
            <div className="-mx-4 mt-4 overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-gray-500">Tipo</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-500">Valor</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-500">Unidad</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-500">Fecha</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-500">Fuente</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {metricasMostrar.map((m) => (
                    <tr key={m.id}>
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium text-gray-900">{m.tipo_resultado}</div>
                      </td>
                      <td className="px-4 py-3">{m.valor}</td>
                      <td className="px-4 py-3">{m.unidad}</td>
                      <td className="px-4 py-3">{new Date(m.fecha_registro).toLocaleString()}</td>
                      <td className="px-4 py-3">{m.fuente}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      </div>

      {ultimoAnalisis && ultimoAnalisis.imagen_urls && ultimoAnalisis.imagen_urls.length > 0 ? (
        <div className="mt-6">
          <SectionCard title="Últimas imágenes procesadas">
            <div className="grid grid-cols-4 gap-3">
              {ultimoAnalisis.imagen_urls.slice(0, 4).map((entry, i) => {
                const src = analisisImagenUrl(entry);
                if (!src) return null;
                return (
                  <img
                    key={i}
                    src={src}
                    alt={`Imagen ${i + 1}`}
                    className="h-24 w-full object-cover rounded-md border border-gray-200"
                  />
                );
              })}
            </div>
            {ultimoAnalisis.imagen_urls.length > 4 ? (
              <p className="mt-2 text-xs text-gray-500">+{ultimoAnalisis.imagen_urls.length - 4} más...</p>
            ) : null}
          </SectionCard>
        </div>
      ) : null}
    </PageContainer>
  );
}