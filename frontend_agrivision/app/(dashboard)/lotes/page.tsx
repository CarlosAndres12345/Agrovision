import React from "react";
import Link from "next/link";

import PageContainer from "../../../components/layout/PageContainer";
import SectionCard from "../../../components/ui/SectionCard";
import { getLotesWithCookie } from "../../../lib/api";
import LotesTable from "../../../components/lotes/LotesTable";
import { getCookieHeader } from "../../../lib/server-cookies";

export const dynamic = "force-dynamic";

export default async function LotesPage() {
  const lotes = await getLotesWithCookie(await getCookieHeader());

  return (
    <PageContainer title="Lotes">
      <SectionCard>
        <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-2xl">
            <div className="text-sm font-medium uppercase tracking-[0.16em] text-emerald-600">Inventario</div>
            <h3 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">Lista de lotes reales</h3>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              Gestiona lotes, filtros, dimensiones y edición desde la demo.
            </p>
            <p className="mt-2 text-xs text-slate-400">
              {lotes.length} lote{lotes.length !== 1 ? "s" : ""} registrados.
            </p>
          </div>
          <Link
            href="/lotes/nuevo"
            className="inline-flex items-center justify-center rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 hover:shadow-md"
          >
            Nuevo lote
          </Link>
        </div>
      </SectionCard>
      <SectionCard>
        <LotesTable lotes={lotes} />
      </SectionCard>
    </PageContainer>
  );
}
