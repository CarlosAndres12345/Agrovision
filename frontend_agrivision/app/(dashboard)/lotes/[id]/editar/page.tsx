import React from "react";

import LoteForm from "../../../../../components/lotes/LoteForm";
import PageContainer from "../../../../../components/layout/PageContainer";
import SectionCard from "../../../../../components/ui/SectionCard";
import { getCultivosWithCookie, getLoteByIdWithCookie } from "../../../../../lib/api";
import { getCookieHeader } from "../../../../../lib/server-cookies";

export const dynamic = "force-dynamic";

export default async function EditarLotePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const cookieHeader = await getCookieHeader();
  const [lote, cultivos] = await Promise.all([
    getLoteByIdWithCookie(id, cookieHeader),
    getCultivosWithCookie(cookieHeader),
  ]);

  return (
    <PageContainer title={`Editar lote #${id}`}>
      {!lote ? (
        <SectionCard title="Lote no encontrado">
          <p className="text-sm text-gray-600">No existe un lote con ese identificador.</p>
        </SectionCard>
      ) : (
        <SectionCard title="Editar lote">
          <LoteForm mode="edit" initialValues={lote} cultivos={cultivos} redirectTo="/lotes" />
        </SectionCard>
      )}
    </PageContainer>
  );
}
