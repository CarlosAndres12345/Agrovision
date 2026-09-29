export type Lote = {
  id: number;
  nombre: string;
  ancho: string | null;
  largo: string | null;
  area_lote: string;
  descripcion: string;
  cultivo_id: number;
};

export type LoteInput = {
  cultivo_id: string;
  nombre: string;
  ancho: string;
  largo: string;
  area_lote: string;
  descripcion: string;
};

export type LoteListResponse = {
  results: Lote[];
};
