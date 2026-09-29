"use client";

import React from "react";

import type { DevicePosition, GeoErrorType, GeolocationStatus } from "../../hooks/useDeviceGeolocation";
import { LOW_ACCURACY_THRESHOLD_METERS } from "../../hooks/useDeviceGeolocation";

type Props = {
  status: GeolocationStatus;
  errorType: GeoErrorType | null;
  position: DevicePosition | null;
  isLowAccuracy: boolean;
  isSupported: boolean;
  isSecureContext: boolean;
  isConfirmed: boolean;
};

const ERROR_MESSAGES: Record<GeoErrorType, string> = {
  unsupported: "Este navegador no soporta geolocalización.",
  insecure_context: "La geolocalización requiere una conexión segura (HTTPS) en producción.",
  permission_denied: "Permiso de ubicación rechazado. Habilítalo en la configuración del navegador.",
  position_unavailable: "No se pudo determinar la posición del dispositivo.",
  timeout: "Se agotó el tiempo de espera al obtener la ubicación.",
  unknown: "Ocurrió un error al obtener la ubicación.",
};

function Badge({ tone, children }: { tone: "green" | "amber" | "red" | "gray" | "blue"; children: React.ReactNode }) {
  const tones: Record<string, string> = {
    green: "bg-green-50 text-green-700 border-green-200",
    amber: "bg-amber-50 text-amber-800 border-amber-200",
    red: "bg-red-50 text-red-700 border-red-200",
    gray: "bg-gray-50 text-gray-600 border-gray-200",
    blue: "bg-blue-50 text-blue-700 border-blue-200",
  };
  return (
    <div className={`rounded-md border px-3 py-2 text-sm ${tones[tone]}`}>{children}</div>
  );
}

export default function LocationStatus({
  status,
  errorType,
  position,
  isLowAccuracy,
  isSupported,
  isSecureContext,
  isConfirmed,
}: Props) {
  if (!isSupported) {
    return <Badge tone="red">{ERROR_MESSAGES.unsupported}</Badge>;
  }
  if (!isSecureContext) {
    return <Badge tone="amber">{ERROR_MESSAGES.insecure_context}</Badge>;
  }

  return (
    <div className="space-y-2">
      {status === "locating" && <Badge tone="gray">Obteniendo ubicación del dispositivo...</Badge>}

      {status === "error" && errorType && <Badge tone="red">{ERROR_MESSAGES[errorType]}</Badge>}

      {status === "watching" && (
        <Badge tone="blue">Seguimiento en tiempo real activo — actualizando posición...</Badge>
      )}

      {position && status !== "watching" && status !== "locating" && (
        <Badge tone="green">Ubicación detectada</Badge>
      )}

      {position && (
        <Badge tone={isLowAccuracy ? "amber" : "green"}>
          Precisión aproximada: ±{Math.round(position.accuracy)} m
          {isLowAccuracy ? ` (baja precisión, mayor a ${LOW_ACCURACY_THRESHOLD_METERS} m)` : ""}
        </Badge>
      )}

      {isConfirmed && <Badge tone="green">Ubicación confirmada y guardada.</Badge>}
    </div>
  );
}
