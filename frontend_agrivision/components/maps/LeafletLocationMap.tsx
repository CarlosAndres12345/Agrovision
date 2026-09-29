"use client";

import React from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

type Props = {
  latitud: number;
  longitud: number;
  className?: string;
  label?: string;
};

const staticLocationIcon = L.icon({
  iconUrl: "/leaflet/marker-icon.png",
  iconRetinaUrl: "/leaflet/marker-icon-2x.png",
  shadowUrl: "/leaflet/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

/**
 * Mapa de solo lectura para una ubicación ya guardada (sin clic, sin arrastre).
 * Este componente solo debe cargarse en cliente (ver uso con next/dynamic si
 * se embebe en un árbol server-rendered).
 */
export default function LocationMap({
  latitud,
  longitud,
  className = "h-80 w-full",
  label = "Ubicación",
}: Props) {
  return (
    <div className={`overflow-hidden rounded-lg ${className}`}>
      <MapContainer center={[latitud, longitud]} zoom={16} scrollWheelZoom className="h-full w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={[latitud, longitud]} icon={staticLocationIcon} draggable={false}>
          <Popup>{label}</Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}
