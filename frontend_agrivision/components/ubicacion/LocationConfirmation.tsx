"use client";

import React from "react";

import type { PendingLocation } from "../../types/locationTypes";

const ORIGEN_LABEL: Record<PendingLocation["source"], string> = {
  DEVICE_GEOLOCATION: "Ubicación actual del dispositivo",
  ADDRESS_SEARCH: "Búsqueda de dirección",
  MAP_SELECTION: "Selección manual en el mapa",
};

type Props = {
  pending: PendingLocation;
  onConfirm: () => void;
  onCancel: () => void;
  confirming: boolean;
  error?: string | null;
  /** Verdadero mientras se busca la dirección aproximada (selección en mapa). */
  resolviendoDireccion?: boolean;
};

export default function LocationConfirmation({
  pending,
  onConfirm,
  onCancel,
  confirming,
  error,
  resolviendoDireccion = false,
}: Props) {
  return (
    <div className="space-y-3 rounded-lg border border-gray-200 bg-white p-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Ubicación seleccionada</p>
        <p className="mt-1 text-sm font-medium text-gray-900">
          {resolviendoDireccion ? "Buscando dirección aproximada..." : pending.address || "Dirección no disponible"}
        </p>
      </div>

      <div className="flex flex-wrap gap-4 text-xs text-gray-500">
        <span>
          Origen: <span className="font-medium text-gray-700">{ORIGEN_LABEL[pending.source]}</span>
        </span>
        {pending.source === "DEVICE_GEOLOCATION" && pending.accuracy != null && (
          <span>
            Precisión aproximada: <span className="font-medium text-gray-700">±{Math.round(pending.accuracy)} m</span>
          </span>
        )}
      </div>

      {pending.source === "MAP_SELECTION" && (
        <p className="text-xs text-gray-400">
          La dirección es aproximada y puede no coincidir exactamente con el punto seleccionado.
        </p>
      )}

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">{error}</div>
      )}

      <div className="flex gap-2 pt-1">
        <button
          type="button"
          onClick={onConfirm}
          disabled={confirming || resolviendoDireccion}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {confirming ? "Guardando..." : "Confirmar ubicación"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={confirming}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}
