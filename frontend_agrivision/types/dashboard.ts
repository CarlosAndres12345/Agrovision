export type EvolucionPunto = {
  fecha: string;
  cantidad_frutos: number;
  frutos_maduros: number;
};

export type RegistroReciente = {
  id: number;
  cultivo: string;
  cultivo_id: number;
  lote: string | null;
  lote_id: number | null;
  estado: "pendiente" | "procesado" | "error";
  fecha: string;
};

export type DashboardSummary = {
  cantidad_frutos: number;
  frutos_maduros: number;
  estimacion_cosecha: number;
  porcentaje_madurez: number | null;
  total_analisis: number;
  evolucion: EvolucionPunto[];
  registros_recientes: RegistroReciente[];
};
