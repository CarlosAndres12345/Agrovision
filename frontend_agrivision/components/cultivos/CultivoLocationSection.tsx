"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";

import { useDeviceGeolocation } from "../../hooks/useDeviceGeolocation";
import { geocodificarInverso } from "../../lib/geolocationApi";
import AddressSearch from "../ubicacion/AddressSearch";
import SearchResults from "../ubicacion/SearchResults";
import LocationConfirmation from "../ubicacion/LocationConfirmation";
import LocationStatus from "../ubicacion/LocationStatus";
import type { AddressSearchResult, LocationSource, MapPosition, PendingLocation } from "../../types/locationTypes";
import type { CultivoLocationInput } from "../../types/cultivo";

const CurrentLocationMap = dynamic(() => import("../ubicacion/CurrentLocationMap"), { ssr: false });

const ORIGEN_LABEL: Record<LocationSource, string> = {
  DEVICE_GEOLOCATION: "Ubicación actual del dispositivo",
  ADDRESS_SEARCH: "Búsqueda de dirección",
  MAP_SELECTION: "Selección manual en el mapa",
};

type Props = {
  /** Ubicación ya confirmada (creación: null; edición: la guardada del cultivo). */
  value: CultivoLocationInput | null;
  /** Se llama solo al confirmar una nueva ubicación candidata — nunca con datos a medio capturar. */
  onChange: (value: CultivoLocationInput) => void;
};

function pendingToMapPosition(pending: PendingLocation | null): MapPosition | null {
  if (!pending) return null;
  return { lat: pending.lat, lng: pending.lng, accuracy: pending.accuracy };
}

function valueToMapPosition(value: CultivoLocationInput | null): MapPosition | null {
  if (!value) return null;
  return { lat: value.latitude, lng: value.longitude, accuracy: value.accuracy_meters ?? null };
}

/**
 * Sección reutilizable de ubicación para el formulario de cultivo (creación
 * y edición). Combina las 3 formas de capturar un punto (GPS del
 * dispositivo, búsqueda de dirección, clic en el mapa) y exige una
 * confirmación explícita antes de reportarla al formulario padre vía
 * `onChange`. No llama a ningún endpoint del backend — la persistencia
 * ocurre junto con el resto del cultivo al enviar el formulario.
 */
export default function CultivoLocationSection({ value, onChange }: Props) {
  const geo = useDeviceGeolocation();
  const [pending, setPending] = useState<PendingLocation | null>(null);
  const [searchResults, setSearchResults] = useState<AddressSearchResult[]>([]);
  const [resolviendoDireccion, setResolviendoDireccion] = useState(false);
  const [recenterToken, setRecenterToken] = useState(0);

  useEffect(() => {
    if (geo.position && (geo.status === "success" || geo.status === "watching")) {
      setPending({
        lat: geo.position.lat,
        lng: geo.position.lng,
        accuracy: geo.position.accuracy,
        address: null,
        source: "DEVICE_GEOLOCATION",
        capturedAt: geo.position.capturedAt,
      });
      setSearchResults([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [geo.position?.lat, geo.position?.lng]);

  function handleUseDevice() {
    geo.getCurrentPosition();
    setRecenterToken((token) => token + 1);
  }

  function handleSelectResult(result: AddressSearchResult) {
    setPending({
      lat: result.lat,
      lng: result.lon,
      accuracy: null,
      address: result.displayName,
      source: "ADDRESS_SEARCH",
      capturedAt: new Date().toISOString(),
    });
    setSearchResults([]);
    setRecenterToken((token) => token + 1);
  }

  async function handleMapClick(lat: number, lng: number) {
    setPending({
      lat,
      lng,
      accuracy: null,
      address: null,
      source: "MAP_SELECTION",
      capturedAt: new Date().toISOString(),
    });
    setResolviendoDireccion(true);
    try {
      const resultado = await geocodificarInverso(lat, lng);
      setPending((current) =>
        current && current.source === "MAP_SELECTION" && current.lat === lat && current.lng === lng
          ? { ...current, address: resultado?.displayName ?? null }
          : current,
      );
    } finally {
      setResolviendoDireccion(false);
    }
  }

  function handleConfirm() {
    if (!pending) return;
    onChange({
      latitude: pending.lat,
      longitude: pending.lng,
      address: pending.address ?? undefined,
      source: pending.source,
      accuracy_meters: pending.accuracy,
      captured_at: pending.capturedAt,
    });
    setPending(null);
  }

  function handleCancelPending() {
    setPending(null);
    setSearchResults([]);
  }

  const displayPosition = pendingToMapPosition(pending) ?? valueToMapPosition(value);

  return (
    <div className="space-y-4 rounded-lg border border-gray-200 p-4">
      <div>
        <h3 className="text-sm font-semibold text-gray-900">Ubicación del cultivo</h3>
        {!value && !pending && (
          <p className="mt-1 text-xs text-gray-500">
            Puede crear el cultivo sin ubicación y agregarla después.
          </p>
        )}
      </div>

      <CurrentLocationMap position={displayPosition} recenterToken={recenterToken} onMapClick={handleMapClick} />

      <button
        type="button"
        onClick={handleUseDevice}
        className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
      >
        Usar mi ubicación actual
      </button>

      <LocationStatus
        status={geo.status}
        errorType={geo.errorType}
        position={geo.position}
        isLowAccuracy={geo.isLowAccuracy}
        isSupported={geo.isSupported}
        isSecureContext={geo.isSecureContext}
        isConfirmed={Boolean(value) && !pending && value?.source === "DEVICE_GEOLOCATION"}
      />

      <AddressSearch onResults={setSearchResults} />
      <SearchResults results={searchResults} onSelect={handleSelectResult} />

      {value && !pending && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-3 text-xs text-green-800">
          Ubicación guardada — origen: {ORIGEN_LABEL[value.source]}
          {value.address ? ` · ${value.address}` : ""}
        </div>
      )}

      {pending && (
        <LocationConfirmation
          pending={pending}
          onConfirm={handleConfirm}
          onCancel={handleCancelPending}
          confirming={false}
          resolviendoDireccion={resolviendoDireccion}
        />
      )}
    </div>
  );
}
