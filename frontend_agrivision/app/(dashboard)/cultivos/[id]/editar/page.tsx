import React from "react";

import CultivoForm from "../../../../../components/cultivos/CultivoForm";
import PageContainer from "../../../../../components/layout/PageContainer";
import SectionCard from "../../../../../components/ui/SectionCard";
import { getCultivoByIdWithCookie } from "../../../../../lib/api";
import { getCookieHeader } from "../../../../../lib/server-cookies";

export const dynamic = "force-dynamic";

export default async function EditarCultivoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const cultivo = await getCultivoByIdWithCookie(id, await getCookieHeader());

  return (
    <PageContainer title={`Editar cultivo #${id}`}>
      {!cultivo ? (
        <SectionCard title="Cultivo no encontrado">
          <p className="text-sm text-gray-600">No existe un cultivo con ese identificador.</p>
        </SectionCard>
      ) : (
        <SectionCard title="Editar cultivo">
          <CultivoForm mode="edit" initialValues={cultivo} redirectTo={`/cultivos/${cultivo.id}`} />
        </SectionCard>
      )}
    </PageContainer>
  );
}
