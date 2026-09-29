import React from "react";

import CultivoForm from "../../../../components/cultivos/CultivoForm";
import PageContainer from "../../../../components/layout/PageContainer";
import SectionCard from "../../../../components/ui/SectionCard";

export default function NuevoCultivoPage() {
  return (
    <PageContainer title="Nuevo cultivo">
      <SectionCard title="Crear cultivo">
        <CultivoForm mode="create" redirectTo="/cultivos" />
      </SectionCard>
    </PageContainer>
  );
}
