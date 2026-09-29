import React from "react";

import MetricaForm from "../../../../components/metricas/MetricaForm";
import PageContainer from "../../../../components/layout/PageContainer";
import SectionCard from "../../../../components/ui/SectionCard";
import { getCultivosWithCookie, getLotesWithCookie } from "../../../../lib/api";
import { getCookieHeader } from "../../../../lib/server-cookies";

export const dynamic = "force-dynamic";

export default async function NuevaMetricaPage({
  searchParams,
}: {
  searchParams: Promise<{ cultivo_id?: string; lote_id?: string }>;
}) {
  const params = await searchParams;
  const defaultCultivoId = params.cultivo_id ? Number(params.cultivo_id) : undefined;
  const defaultLoteId = params.lote_id ? Number(params.lote_id) : undefined;

  const cookieHeader = await getCookieHeader();
  const [cultivos, lotes] = await Promise.all([
    getCultivosWithCookie(cookieHeader),
    getLotesWithCookie(cookieHeader),
  ]);

  return (
    <PageContainer title="Registrar métrica">
      <SectionCard title="Nueva métrica">
        <MetricaForm
          cultivos={cultivos}
          lotes={lotes}
          defaultCultivoId={defaultCultivoId}
          defaultLoteId={defaultLoteId}
        />
      </SectionCard>
    </PageContainer>
  );
}
