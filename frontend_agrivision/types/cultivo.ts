import type { LocationSource } from "./locationTypes";
import type { EstadoAnalisis } from "./metrica";

export type CultivoLocation = {
  latitude: string;
  longitude: string;
  address: string;
  source: LocationSource;
  accuracy_meters: string | null;
  captured_at: string;
};

export type CultivoLocationInput = {
  latitude: number;
  longitude: number;
  address?: string;
  source: LocationSource;
  accuracy_meters?: number | null;
  captured_at?: string;
};

export type Cultivo = {
  id: number;
  nombre: string;
  tipo_fruto: string;
  ubicacion: string;
  latitud: string | null;
  longitud: string | null;
  area_sembrada: string;
  fecha_siembra: string;
  descripcion: string;
  /** Presente en detalle (GET/POST/PATCH de un solo cultivo); ausente en el listado. */
  location?: CultivoLocation | null;
  /** Estado del último análisis del cultivo (null si todavía no tiene ninguno). */
  ultimo_analisis_estado?: EstadoAnalisis | null;
};

export type CultivoInput = {
  nombre: string;
  tipo_fruto: string;
  ubicacion: string;
  area_sembrada: string;
  fecha_siembra: string;
  descripcion: string;
  location?: CultivoLocationInput | null;
};

export type CultivoListResponse = {
  results: Cultivo[];
};
