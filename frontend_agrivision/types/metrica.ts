export type AnalisisImagen = string | { url: string; nombre?: string };

export function analisisImagenUrl(entry: AnalisisImagen): string | null {
  if (typeof entry === "string") return entry;
  return entry.url ?? null;
}

export type EstadoAnalisis = "pendiente" | "procesando" | "procesado" | "procesado_con_errores" | "error";

export type Analisis = {
  id: number;
  origen: "manual" | "repositorio";
  estado: EstadoAnalisis;
  imagen_urls: AnalisisImagen[];
  resultado_json: Record<string, { valor: number; unidad: string }>;
  notas: string;
  cultivo_id: number;
  lote_id: number | null;
  created_at: string;
};

export type MetricaTipo = "cantidad_frutos" | "frutos_maduros" | "estimacion_cosecha" | "porcentaje_madurez";

export type AnalisisInputManual = {
  cultivo_id: number;
  lote_id?: number | null;
  imagenes: File[];
  notas?: string;
};

export type AnalisisListResponse = {
  results: Analisis[];
};

// Tipos existentes de métricas (mantener)
export type MetricaRaw = {
  id: number;
  tipo_resultado: "cantidad_frutos" | "frutos_maduros" | "estimacion_cosecha" | "porcentaje_madurez";
  valor: string | number;
  unidad: string;
  fecha_registro: string;
  fuente: string;
  descripcion: string;
  cultivo_id: number;
  lote_id: number | null;
};

export type MetricaInput = {
  cultivo_id: number;
  lote_id?: number | null;
  tipo_resultado: string;
  valor: string;
  unidad?: string;
  fecha_registro: string;
  descripcion?: string;
  fuente?: string;
};

export type MetricaListResponse = {
  results: MetricaRaw[];
};

export type ProcesamientoResponse = {
  cultivo_id: number;
  lote_id: number | null;
  imagenes_procesadas: number;
  metricas: MetricaRaw[];
};

// ==================== GET /api/cultivos/{id}/metricas/ ====================

export type EstadoAnalisisApi = "PENDIENTE" | "PROCESANDO" | "COMPLETADO" | "COMPLETADO_CON_ERRORES" | "ERROR";

export type AnalisisResumen = {
  id: number;
  fecha_procesamiento: string;
  cantidad_frutos: number | null;
  frutos_maduros: number | null;
  porcentaje_madurez: number | null;
  estimacion_cosecha: number | null;
  estado: EstadoAnalisisApi;
  lote_id: number | null;
  mensaje_error: string | null;
};

export type CultivoMetricasResponse = {
  cultivo_id: number;
  ultimo_analisis: AnalisisResumen | null;
  resumen: {
    total_analisis: number;
    cantidad_frutos_ultimo: number | null;
    frutos_maduros_ultimo: number | null;
    porcentaje_madurez_ultimo: number | null;
    estimacion_cosecha_ultima: number | null;
  } | null;
  historial: AnalisisResumen[];
};