"use client";

import React from "react";

export default function CultivosError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="av-card p-6">
      <h2 className="text-lg font-semibold text-red-700">No se pudieron cargar los cultivos</h2>
      <p className="mt-2 text-sm text-gray-600">No fue posible cargar la información de los cultivos.</p>
      <button
        onClick={() => reset()}
        className="mt-4 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
      >
        Reintentar
      </button>
    </div>
  );
}
