import React from "react";

import PageContainer from "../../../../../components/layout/PageContainer";
import SectionCard from "../../../../../components/ui/SectionCard";

export default function LoadingCultivoEditarPage() {
  return (
    <PageContainer title="Editar cultivo">
      <SectionCard title="Cargando cultivo">
        <div className="space-y-3">
          <div className="h-4 w-40 animate-pulse rounded bg-gray-200" />
          <div className="h-10 w-full animate-pulse rounded bg-gray-100" />
          <div className="h-10 w-full animate-pulse rounded bg-gray-100" />
          <div className="h-24 w-full animate-pulse rounded bg-gray-100" />
        </div>
      </SectionCard>
    </PageContainer>
  );
}