"use client";

import PageContainer from "../../../../components/layout/PageContainer";
import SectionCard from "../../../../components/ui/SectionCard";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <PageContainer title="Detalle de lote">
      <SectionCard title="No se pudo cargar el lote">
        <p className="text-sm text-gray-600">No fue posible cargar la información del lote.</p>
        <button
          type="button"
          onClick={reset}
          className="mt-4 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
        >
          Reintentar
        </button>
      </SectionCard>
    </PageContainer>
  );
}
