import Link from "next/link";

import PageContainer from "../../../components/layout/PageContainer";
import SectionCard from "../../../components/ui/SectionCard";

export const dynamic = "force-dynamic";

export default function ConfiguracionPage() {
  return (
    <PageContainer title="Configuración">
      {/* ── Repositorio de imágenes (Cloudinary) ─────────────────────── */}
      <SectionCard title="Repositorio de imágenes">
        <div className="space-y-3">
          <p className="text-sm text-slate-600">
            Las imágenes se almacenan en Cloudinary y se asocian a un cultivo y,
            opcionalmente, a un lote. Se sincronizan, cargan y procesan desde el
            módulo Repositorio.
          </p>
          <Link
            href="/repositorio"
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 transition-colors"
          >
            Ir al repositorio de imágenes
          </Link>
        </div>
      </SectionCard>

      {/* ── Acciones rápidas ─────────────────────────────────── */}
      <SectionCard title="Acciones rápidas">
        <div className="flex flex-wrap gap-3">
          <Link
            href="/procesamiento/nuevo"
            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Procesar dataset
          </Link>
          <Link
            href="/cultivos"
            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Ver cultivos
          </Link>
        </div>
      </SectionCard>
    </PageContainer>
  );
}
