"use client";

import React, { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Circle, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import type { MapPosition } from "../../types/locationTypes";

// Iconos por defecto de Leaflet servidos localmente (public/leaflet/) —
// sin depender de ningún CDN externo.
const deviceLocationIcon = L.icon({
  iconUrl: "/leaflet/marker-icon.png",
  iconRetinaUrl: "/leaflet/marker-icon-2x.png",
  shadowUrl: "/leaflet/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const DEFAULT_CENTER: [number, number] = [4.624335, -74.08175]; // Bogotá — solo mientras no hay posición
const DEFAULT_ZOOM = 13;
const POSITION_ZOOM = 17;

type Props = {
  position: MapPosition | null;
  /** Se incrementa para forzar un recentrado manual ("Volver a centrar"). */
  recenterToken?: number;
  className?: string;
  /**
   * Si se define, habilita seleccionar un punto haciendo clic en el mapa
   * (selección manual). Si se omite, el mapa queda de solo lectura, igual
   * que antes — ver useMapEvents en react-leaflet.
   */
  onMapClick?: (lat: number, lng: number) => void;
};

function MapSync({ position, recenterToken }: { position: MapPosition | null; recenterToken?: number }) {
  const map = useMap();

  // Recentra automáticamente cuando llega una nueva posición.
  useEffect(() => {
    if (position) {
      map.setView([position.lat, position.lng], Math.max(map.getZoom(), POSITION_ZOOM));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [position?.lat, position?.lng]);

  // Recentra manualmente vía el botón "Volver a centrar".
  useEffect(() => {
    if (position && recenterToken !== undefined) {
      map.setView([position.lat, position.lng], POSITION_ZOOM);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recenterToken]);

  return null;
}

function ClickHandler({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

/**
 * Mapa con marcador nunca arrastrable. Por defecto es de solo lectura (sin
 * selección por clic); pasar `onMapClick` habilita la selección manual de
 * un punto (usada por la opción "seleccionar en el mapa").
 */
export default function CurrentLocationMap({
  position,
  recenterToken,
  className = "h-80 w-full",
  onMapClick,
}: Props) {
  const center: [number, number] = position ? [position.lat, position.lng] : DEFAULT_CENTER;

  return (
    <div className={`overflow-hidden rounded-lg border border-gray-200 ${className}`}>
      <MapContainer
        center={center}
        zoom={position ? POSITION_ZOOM : DEFAULT_ZOOM}
        scrollWheelZoom
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {position && (
          <>
            <Marker position={[position.lat, position.lng]} icon={deviceLocationIcon} draggable={false} />
            {position.accuracy != null && position.accuracy > 0 && (
              <Circle
                center={[position.lat, position.lng]}
                radius={position.accuracy}
                pathOptions={{ color: "#16a34a", fillColor: "#16a34a", fillOpacity: 0.15 }}
              />
            )}
          </>
        )}
        <MapSync position={position} recenterToken={recenterToken} />
        {onMapClick && <ClickHandler onMapClick={onMapClick} />}
      </MapContainer>
    </div>
  );
}
