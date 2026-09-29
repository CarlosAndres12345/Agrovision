import React from "react";

import LocationMap from "../../../../components/maps/LocationMap";
import PageContainer from "../../../../components/layout/PageContainer";
import SectionCard from "../../../../components/ui/SectionCard";
import StatusBadge from "../../../../components/ui/StatusBadge";
import CultivoMetricasPanel from "../../../../components/cultivos/CultivoMetricasPanel";
import Link from "next/link";
import { getCookieHeader } from "../../../../lib/server-cookies";
import { getCultivoByIdWithCookie, getUltimoAnalisisCultivo } from "../../../../lib/api";
import type { Analisis } from "../../../../types/metrica";
import { analisisImagenUrl } from "../../../../types/metrica";

export const dynamic = "force-dynamic";

export default async function CultivoDetallePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const cookieHeader = await getCookieHeader();
  const cultivo = await getCultivoByIdWithCookie(id, cookieHeader);

  if (!cultivo) {
    return (
      <PageContainer title={`Detalle de cultivo #${id}`}>
        <SectionCard title="Cultivo no encontrado">
          <p className="text-sm text-gray-600">
            No existe un cultivo con ese identificador o no fue posible cargarlo.
          </p>
        </SectionCard>
      </PageContainer>
    );
  }

  let ultimoAnalisis: Analisis | null = null;
  try {
    ultimoAnalisis = await getUltimoAnalisisCultivo(id);
  } catch {
    // Si no hay análisis, se muestra sin imágenes
  }

  return (
    <PageContainer title={`Detalle de cultivo #${id}`}>
      <div className="grid gap-6 lg:grid-cols-3">
        <SectionCard title={cultivo.nombre} className="lg:col-span-2">
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={ultimoAnalisis?.estado ?? null} />
            <span className="text-sm text-gray-500">{cultivo.tipo_fruto}</span>
            <span className="text-sm text-gray-500">{cultivo.ubicacion}</span>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <div className="rounded-md bg-gray-50 p-4">
              <div className="text-xs uppercase tracking-wide text-gray-500">Área sembrada</div>
              <div className="mt-1 text-xl font-semibold text-gray-900">{cultivo.area_sembrada} ha</div>
            </div>
            <div className="rounded-md bg-gray-50 p-4">
              <div className="text-xs uppercase tracking-wide text-gray-500">Fecha de siembra</div>
              <div className="mt-1 text-xl font-semibold text-gray-900">{cultivo.fecha_siembra}</div>
            </div>
            <div className="rounded-md bg-gray-50 p-4">
              <div className="text-xs uppercase tracking-wide text-gray-500">Coordenadas</div>
              <div className="mt-1 text-sm font-semibold text-gray-900">
                {cultivo.latitud != null && cultivo.longitud != null
                  ? `${cultivo.latitud}, ${cultivo.longitud}`
                  : "No registradas"}
              </div>
            </div>
          </div>

          {cultivo.latitud != null && cultivo.longitud != null ? (
            <div className="mt-6 overflow-hidden rounded-xl border border-gray-200">
              <LocationMap
                latitud={Number(cultivo.latitud)}
                longitud={Number(cultivo.longitud)}
                className="h-80 w-full"
                label={cultivo.nombre}
              />
            </div>
          ) : null}

          <div className="mt-6">
            <h3 className="text-sm font-medium text-gray-700">Descripción</h3>
            <p className="mt-2 text-sm leading-6 text-gray-600">
              {cultivo.descripcion || "Sin descripción registrada."}
            </p>
          </div>
        </SectionCard>

        <SectionCard title="Resumen rápido">
          <div className="space-y-4 text-sm text-gray-600">
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-500">ID</div>
              <div className="mt-1 font-medium text-gray-900">{cultivo.id}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-500">Ubicación</div>
              <div className="mt-1 font-medium text-gray-900">{cultivo.ubicacion}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-500">Tipo de fruto</div>
              <div className="mt-1 font-medium text-gray-900">{cultivo.tipo_fruto}</div>
            </div>
            <div className="flex flex-wrap gap-2 pt-2">
              <Link
                href={`/cultivos/${cultivo.id}/editar`}
                className="inline-flex rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
              >
                Editar cultivo
              </Link>
              <Link
                href={`/procesamiento/nuevo?cultivo_id=${cultivo.id}`}
                className="inline-flex rounded-md border border-green-200 bg-green-50 px-4 py-2 text-sm font-medium text-green-700 hover:bg-green-100"
              >
                Procesar dataset
              </Link>
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Métricas agrícolas" className="lg:col-span-3">
          <CultivoMetricasPanel cultivoId={cultivo.id} />
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