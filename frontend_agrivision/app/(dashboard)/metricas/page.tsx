import React from "react";

import PageContainer from "../../../components/layout/PageContainer";
import SectionCard from "../../../components/ui/SectionCard";
import StatusBadge from "../../../components/ui/StatusBadge";
import Link from "next/link";
import { getCookieHeader } from "../../../lib/server-cookies";
import { getAnalisisWithCookie } from "../../../lib/api";
import type { Analisis, AnalisisImagen } from "../../../types/metrica";
import { analisisImagenUrl } from "../../../types/metrica";

export const dynamic = "force-dynamic";

const LABELS: Record<string, string> = {
  cantidad_frutos: "Cantidad de frutos",
  frutos_maduros: "Frutos maduros",
  estimacion_cosecha: "Estimación de cosecha",
  porcentaje_madurez: "Porcentaje de madurez",
};

const ACCENTS: Record<string, string> = {
  cantidad_frutos: "bg-emerald-500",
  frutos_maduros: "bg-lime-500",
  estimacion_cosecha: "bg-green-700",
  porcentaje_madurez: "bg-teal-600",
};

export default async function MetricasPage() {
  const cookieHeader = await getCookieHeader();
  const analisis: Analisis[] = await getAnalisisWithCookie(cookieHeader);

  return (
    <PageContainer title="Análisis de imágenes">
      <div className="space-y-6">
        <SectionCard title="Historial de análisis">
          {analisis.length === 0 ? (
            <div className="text-sm text-gray-600">No hay análisis registrados.</div>
          ) : (
            <div className="space-y-6">
              {analisis.map((a) => (
                <div key={a.id} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        Análisis #{a.id} — {a.origen === "manual" ? "Subida manual" : "Repositorio (Cloudinary)"}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(a.created_at).toLocaleString()}
                      </div>
                    </div>
                    <StatusBadge status={a.estado} />
                  </div>

                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    {Object.entries(a.resultado_json || {}).map(([tipo, datos]) => (
                      <div
                        key={tipo}
                        className="rounded-lg border border-gray-100 bg-gray-50 p-3"
                      >
                        <div className="text-xs uppercase tracking-wide text-gray-500">
                          {LABELS[tipo] ?? tipo}
                        </div>
                        <div className="mt-1 flex items-end gap-1 text-xl font-semibold text-gray-900">
                          <span>{datos.valor}</span>
                          {datos.unidad && (
                            <span className="text-sm font-medium text-gray-500">{datos.unidad}</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {a.imagen_urls && a.imagen_urls.length > 0 ? (
                    <div className="mt-4">
                      <div className="text-xs font-medium text-gray-500 mb-2">Imágenes procesadas</div>
                      <div className="grid grid-cols-4 gap-2">
                        {a.imagen_urls.slice(0, 4).map((entry, i) => {
                          const src = analisisImagenUrl(entry);
                          if (!src) return null;
                          return (
                            <img
                              key={i}
                              src={src}
                              alt={`Imagen ${i + 1}`}
                              className="h-16 w-full object-cover rounded-md border border-gray-200"
                            />
                          );
                        })}
                      </div>
                      {a.imagen_urls.length > 4 ? (
                        <p className="mt-1 text-xs text-gray-400">+{a.imagen_urls.length - 4} más...</p>
                      ) : null}
                    </div>
                  ) : null}

                  {a.notas ? (
                    <div className="mt-4">
                      <div className="text-xs font-medium text-gray-500 mb-1">Notas</div>
                      <p className="text-sm text-gray-600">{a.notas}</p>
                    </div>
                  ) : null}

                  <div className="mt-4 flex flex-wrap gap-2 text-xs text-gray-500">
                    <span>Cultivo: #{a.cultivo_id}</span>
                    {a.lote_id ? <span>Lote: #{a.lote_id}</span> : null}
                  </div>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      </div>
    </PageContainer>
  );
}