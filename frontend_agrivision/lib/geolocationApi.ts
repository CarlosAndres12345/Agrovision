"use client";

import { BACKEND_BASE_URL } from "./api";
import type { AddressSearchResult, ReverseGeocodeResult } from "../types/locationTypes";

async function fetchJSON<T>(path: string): Promise<T> {
  const response = await fetch(`${BACKEND_BASE_URL}${path}`, {
    cache: "no-store",
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    let detail = `Error ${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.detail) detail = payload.detail;
    } catch {
      // keep default
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

/**
 * GET /api/geolocation/search/?q= — el backend consulta Nominatim, nunca el navegador.
 * Solo debe llamarse al pulsar "Buscar" o Enter (nunca por cada tecla).
 */
export async function buscarDireccion(query: string): Promise<AddressSearchResult[]> {
  const params = new URLSearchParams({ q: query });
  const data = await fetchJSON<{
    results: Array<{ lat: number; lon: number; display_name: string }>;
  }>(`/api/geolocation/search/?${params.toString()}`);

  return data.results.map((r) => ({ lat: r.lat, lon: r.lon, displayName: r.display_name }));
}

/** GET /api/geolocation/reverse/?lat=&lon= — dirección aproximada de un punto. */
export async function geocodificarInverso(lat: number, lon: number): Promise<ReverseGeocodeResult> {
  const params = new URLSearchParams({ lat: String(lat), lon: String(lon) });
  const data = await fetchJSON<{ result: { display_name: string } | null }>(
    `/api/geolocation/reverse/?${params.toString()}`,
  );

  return data.result ? { displayName: data.result.display_name } : null;
}
