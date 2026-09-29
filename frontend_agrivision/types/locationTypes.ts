export type LocationSource = "DEVICE_GEOLOCATION" | "ADDRESS_SEARCH" | "MAP_SELECTION";

/** Forma mínima que necesita el mapa para centrar y dibujar el marcador. */
export type MapPosition = {
  lat: number;
  lng: number;
  /** Solo tiene un valor real cuando proviene del dispositivo (GPS). */
  accuracy: number | null;
};

/** Ubicación candidata, todavía sin confirmar por el usuario. */
export type PendingLocation = MapPosition & {
  address: string | null;
  source: LocationSource;
  capturedAt: string;
};

export type AddressSearchResult = {
  lat: number;
  lon: number;
  displayName: string;
};

export type ReverseGeocodeResult = {
  displayName: string;
} | null;
