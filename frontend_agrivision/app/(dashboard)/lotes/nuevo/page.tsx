import React from "react";

import LoteForm from "../../../../components/lotes/LoteForm";
import PageContainer from "../../../../components/layout/PageContainer";
import SectionCard from "../../../../components/ui/SectionCard";
import { getCultivosWithCookie } from "../../../../lib/api";
import { getCookieHeader } from "../../../../lib/server-cookies";

export const dynamic = "force-dynamic";

export default async function NuevoLotePage() {
  const cultivos = await getCultivosWithCookie(await getCookieHeader());

  return (
    <PageContainer title="Nuevo lote">
      <SectionCard title="Crear lote">
        <LoteForm mode="create" cultivos={cultivos} redirectTo="/lotes" />
      </SectionCard>
    </PageContainer>
  );
}
