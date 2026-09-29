import React from "react";

import PageContainer from "../../../../../components/layout/PageContainer";
import SectionCard from "../../../../../components/ui/SectionCard";

export default function LoadingLoteEditarPage() {
  return (
    <PageContainer title="Editar lote">
      <SectionCard title="Cargando lote">
        <div className="space-y-3">
          <div className="h-4 w-36 animate-pulse rounded bg-slate-200" />
          <div className="h-10 w-full animate-pulse rounded bg-slate-100" />
          <div className="h-10 w-full animate-pulse rounded bg-slate-100" />
          <div className="h-24 w-full animate-pulse rounded bg-slate-100" />
        </div>
      </SectionCard>
    </PageContainer>
  );
}