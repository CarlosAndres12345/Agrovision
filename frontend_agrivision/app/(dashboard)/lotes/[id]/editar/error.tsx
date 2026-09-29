"use client";

import React, { useEffect } from "react";

import PageContainer from "../../../../../components/layout/PageContainer";
import SectionCard from "../../../../../components/ui/SectionCard";

type Props = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function ErrorLoteEditarPage({ error, reset }: Props) {
  useEffect(() => {
    console.error("Error en edición de lote:", error);
  }, [error]);

  return (
    <PageContainer title="Editar lote">
      <SectionCard title="No se pudo cargar el lote">
        <p className="text-sm text-gray-600">Ocurrió un error al cargar o preparar el formulario de edición.</p>
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