"use client";

import React, { useState } from "react";
import AnalisisForm from "./AnalisisForm";

type Props = {
  initialCultivoId?: number | null;
  initialLoteId?: number | null;
};

const TABS: { id: "analisis"; label: string; description: string }[] = [
  {
    id: "analisis",
    label: "Análisis de imágenes",
    description: "Sube imágenes y analízalas de inmediato, o procesa imágenes desde el Repositorio (Cloudinary).",
  },
];

export default function ProcesamientoTabs({
  initialCultivoId = null,
  initialLoteId = null,
}: Props) {
  const [activeTab] = useState<"analisis">("analisis");

  return (
    <div className="space-y-5">
      {/* Description */}
      <p className="text-sm text-gray-500">
        {TABS.find((t) => t.id === activeTab)?.description}
      </p>

      {/* Form */}
      <AnalisisForm
        initialCultivoId={initialCultivoId}
        initialLoteId={initialLoteId}
      />
    </div>
  );
}