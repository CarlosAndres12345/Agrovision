export type ImagenRepositorioEstado = "disponible" | "procesando" | "procesada" | "error";

export type ImagenRepositorio = {
  id: number;
  asset_id: string;
  public_id: string;
  secure_url: string;
  nombre_original: string;
  formato: string;
  ancho: number | null;
  alto: number | null;
  tamano_bytes: number | null;
  asset_folder: string;
  resource_type: string;
  fecha_creacion_cloudinary: string | null;
  cultivo_id: number;
  lote_id: number | null;
  repositorio_id: number | null;
  estado: ImagenRepositorioEstado;
  procesada: boolean;
  analisis_id: number | null;
  fecha_sincronizacion: string;
  fecha_procesamiento: string | null;
};

// ==================== Configuración de repositorio (por usuario) ====================

export type RepositorioProveedor = "CLOUDINARY";
export type RepositorioEstadoConexion = "sin_probar" | "conectado" | "fallido";

export type RepositorioImagen = {
  id: number;
  nombre: string;
  proveedor: RepositorioProveedor;
  cloud_name: string;
  api_key: string;
  carpeta_raiz: string;
  activo: boolean;
  estado_conexion: RepositorioEstadoConexion;
  ultimo_sync: string | null;
  fecha_creacion: string;
  fecha_actualizacion: string;
  cantidad_imagenes: number;
};

export type RepositorioConfigInput = {
  nombre: string;
  proveedor: RepositorioProveedor;
  cloud_name: string;
  api_key: string;
  api_secret: string;
  carpeta_raiz?: string;
};

export type RepositorioConfigEditInput = Omit<RepositorioConfigInput, "api_secret"> & {
  /** Vacío/omitido = conservar el secreto ya guardado. */
  api_secret?: string;
};

export type RepositorioListResponse = {
  results: RepositorioImagen[];
};

export type RepositorioCreateResponse = {
  repositorio: RepositorioImagen;
  descubrimiento: {
    cantidad_encontradas: number;
    hay_mas: boolean;
  };
};

export type RepositorioTestResponse = {
  ok: boolean;
  mensaje: string;
};

export type RepositoryImagesResumen = {
  total: number;
  pendientes: number;
  procesando: number;
  procesadas: number;
  con_error: number;
};

export type RepositoryImagesResponse = {
  results: ImagenRepositorio[];
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
  resumen: RepositoryImagesResumen;
};

export type RepositoryImagesFilters = {
  cultivoId: number;
  loteId?: number | null;
  estado?: ImagenRepositorioEstado | "";
  page?: number;
  pageSize?: number;
};

export type RepositorySyncResponse = {
  ok: boolean;
  folder: string;
  /** Cantidad total de assets que Cloudinary devolvió para la carpeta. */
  total_cloudinary: number;
  /** Assets nuevos en el repositorio global (nunca sincronizados por nadie). */
  created_assets: number;
  /** Assets ya existentes cuyos metadatos se refrescaron. */
  updated_assets: number;
  /** Asociaciones nuevas creadas para el cultivo seleccionado. */
  associated: number;
  /** Asociaciones que ya existían para el cultivo seleccionado (no se duplicaron). */
  already_associated: number;
  /** Recursos de Cloudinary sin datos suficientes para identificarlos. */
  skipped: number;
  /** Total de imágenes visibles para el cultivo seleccionado tras sincronizar. */
  total_visible_for_crop: number;
  message: string;
  // Campos históricos — se mantienen por compatibilidad con código existente.
  total: number;
  creadas: ImagenRepositorio[];
  cantidad_creadas: number;
  cantidad_actualizadas: number;
};

export type RepositoryFoldersResponse =
  | { ok: true; folders: string[] }
  | { ok: false; message: string };

export type RepositoryProcessResponse = {
  analisis_id: number;
  status: "COMPLETADO";
  metricas_creadas: number;
  modelo_usado: string;
  imagenes_procesadas: number;
  duracion_segundos: number;
  metrics: {
    cantidad_frutos?: number;
    frutos_maduros?: number;
    porcentaje_madurez?: number;
    estimacion_cosecha?: number;
  };
};

export type RepositoryProcessAllErrorEntry = {
  imagen_id: number;
  motivo: string;
};

/** Respuesta de POST /api/repository/process-all/ — procesa todas las imágenes pendientes del cultivo. */
export type RepositoryProcessAllResponse = {
  status: "SIN_PENDIENTES" | "COMPLETADO" | "COMPLETADO_CON_ERRORES" | "ERROR";
  cultivo_id: number;
  imagenes_procesadas: number;
  imagenes_con_error: number;
  message?: string;
  analisis_id?: number;
  duracion_segundos?: number;
  modelo_usado?: string;
  errores?: RepositoryProcessAllErrorEntry[];
  metrics?: {
    cantidad_frutos: number;
    frutos_maduros: number;
    porcentaje_madurez: number | null;
    estimacion_cosecha: number;
  };
};
