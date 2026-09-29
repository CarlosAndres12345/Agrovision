import type {
  ImagenRepositorio,
  RepositorioConfigEditInput,
  RepositorioConfigInput,
  RepositorioCreateResponse,
  RepositorioImagen,
  RepositorioListResponse,
  RepositorioTestResponse,
  RepositoryFoldersResponse,
  RepositoryImagesFilters,
  RepositoryImagesResponse,
  RepositoryProcessAllResponse,
  RepositoryProcessResponse,
  RepositorySyncResponse,
} from "../types/repository";
import type { Cultivo, CultivoInput, CultivoListResponse } from "../types/cultivo";
import type {
  Analisis,
  AnalisisListResponse,
  CultivoMetricasResponse,
  MetricaInput,
  MetricaListResponse,
  MetricaRaw,
  ProcesamientoResponse,
} from "../types/metrica";
import type { Lote, LoteInput, LoteListResponse } from "../types/lote";
import type { User, LoginResponse, RegisterResponse } from "../types/auth";
import type { DashboardSummary } from "../types/dashboard";

// IMPORTANTE: en desarrollo, NEXT_PUBLIC_API_URL debe usar 'localhost' (no
// '127.0.0.1'). Django en localhost:8000 establece Set-Cookie con dominio
// 'localhost'. El browser incluye esa cookie en requests a localhost:3000
// (mismo dominio, distinto puerto). Con 127.0.0.1, la cookie quedaría en
// otro dominio y el proxy.ts no la vería → bucle de login.
//
// Única fuente de verdad para la URL del backend en todo el frontend — no
// construyas otra variante en ningún otro archivo, importa BACKEND_BASE_URL
// desde aquí (ver AnalisisForm.tsx y lib/geolocationApi.ts).
export const BACKEND_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

// ==================== AUTH USER (caché de UI) ====================
// La fuente de verdad es la sesión Django (cookie 'sessionid').
// getAuthUser / setAuthUser solo sirven para mostrar el nombre en la UI
// sin llamar al backend en cada render.

export function getAuthUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("auth_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function setAuthUser(user: User): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("auth_user", JSON.stringify(user));
}

export function clearAuthData(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("auth_user");
}

// ==================== FETCH HELPERS ====================
// Todos los requests usan credentials: 'include' para enviar la cookie
// 'sessionid' que Django establece al hacer login.
// En localhost, la cookie SameSite=Lax se comparte entre :3000 y :8000
// porque ambos tienen el mismo registrable domain (localhost).

async function fetchJSON<T>(path: string): Promise<T> {
  const response = await fetch(`${BACKEND_BASE_URL}${path}`, {
    cache: "no-store",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.detail) detail = payload.detail;
    } catch {
      // keep default message
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

async function fetchJSONWithCookie<T>(path: string, cookieHeader?: string): Promise<T> {
  const response = await fetch(`${BACKEND_BASE_URL}${path}`, {
    cache: "no-store",
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(cookieHeader ? { Cookie: cookieHeader } : {}),
    },
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.detail) detail = payload.detail;
    } catch {
      // keep default message
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

async function requestJSON<T>(
  path: string,
  method: "POST" | "PUT" | "PATCH" | "DELETE",
  body?: unknown,
): Promise<T> {
  const response = await fetch(`${BACKEND_BASE_URL}${path}`, {
    method,
    cache: "no-store",
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.detail) detail = payload.detail;
    } catch {
      // keep default message
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

// ==================== CULTIVOS ====================

export async function getCultivos(): Promise<Cultivo[]> {
  const data = await fetchJSON<CultivoListResponse>("/api/cultivos/");
  return data.results;
}

export async function getCultivosWithCookie(cookieHeader: string): Promise<Cultivo[]> {
  const data = await fetchJSONWithCookie<CultivoListResponse>("/api/cultivos/", cookieHeader);
  return data.results;
}

export async function getCultivoById(id: string | number): Promise<Cultivo | null> {
  const response = await fetch(`${BACKEND_BASE_URL}/api/cultivos/${id}/`, {
    cache: "no-store",
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
  return (await response.json()) as Cultivo;
}

export async function getCultivoByIdWithCookie(
  id: string | number,
  cookieHeader: string,
): Promise<Cultivo | null> {
  const response = await fetch(`${BACKEND_BASE_URL}/api/cultivos/${id}/`, {
    cache: "no-store",
    credentials: "include",
    headers: { Accept: "application/json", Cookie: cookieHeader },
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
  return (await response.json()) as Cultivo;
}

export async function createCultivo(input: CultivoInput): Promise<Cultivo> {
  return await requestJSON<Cultivo>("/api/cultivos/", "POST", input);
}

export async function updateCultivo(id: string | number, input: CultivoInput): Promise<Cultivo> {
  return await requestJSON<Cultivo>(`/api/cultivos/${id}/`, "PATCH", input);
}

export async function deleteCultivo(id: string | number): Promise<void> {
  await requestJSON<void>(`/api/cultivos/${id}/`, "DELETE");
}

export async function getCultivoMetricas(id: string | number): Promise<CultivoMetricasResponse> {
  return await fetchJSON<CultivoMetricasResponse>(`/api/cultivos/${id}/metricas/`);
}

// ==================== DASHBOARD ====================

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return await fetchJSON<DashboardSummary>("/api/dashboard/summary/");
}

export async function getDashboardSummaryWithCookie(cookieHeader: string): Promise<DashboardSummary> {
  return await fetchJSONWithCookie<DashboardSummary>("/api/dashboard/summary/", cookieHeader);
}

// ==================== LOTES ====================

export async function getLotes(): Promise<Lote[]> {
  const data = await fetchJSON<LoteListResponse>("/api/lotes/");
  return data.results;
}

export async function getLotesWithCookie(cookieHeader: string): Promise<Lote[]> {
  const data = await fetchJSONWithCookie<LoteListResponse>("/api/lotes/", cookieHeader);
  return data.results;
}

export async function getLoteById(id: string | number): Promise<Lote | null> {
  const response = await fetch(`${BACKEND_BASE_URL}/api/lotes/${id}/`, {
    cache: "no-store",
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
  return (await response.json()) as Lote;
}

export async function getLoteByIdWithCookie(
  id: string | number,
  cookieHeader: string,
): Promise<Lote | null> {
  const response = await fetch(`${BACKEND_BASE_URL}/api/lotes/${id}/`, {
    cache: "no-store",
    credentials: "include",
    headers: { Accept: "application/json", Cookie: cookieHeader },
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
  return (await response.json()) as Lote;
}

export async function createLote(input: LoteInput): Promise<Lote> {
  return await requestJSON<Lote>("/api/lotes/", "POST", input);
}

export async function updateLote(id: string | number, input: LoteInput): Promise<Lote> {
  return await requestJSON<Lote>(`/api/lotes/${id}/`, "PATCH", input);
}

export async function deleteLote(id: string | number): Promise<void> {
  await requestJSON<void>(`/api/lotes/${id}/`, "DELETE");
}

export async function getLotesByCultivo(cultivoId: string | number): Promise<Lote[]> {
  const data = await fetchJSON<LoteListResponse>(`/api/lotes/cultivo/${cultivoId}/`);
  return data.results;
}

export async function getLotesByCultivoWithCookie(
  cultivoId: string | number,
  cookieHeader: string,
): Promise<Lote[]> {
  const data = await fetchJSONWithCookie<LoteListResponse>(`/api/lotes/cultivo/${cultivoId}/`, cookieHeader);
  return data.results;
}

// ==================== ANÁLISIS ====================

export async function getAnalisis(): Promise<Analisis[]> {
  const data = await fetchJSON<AnalisisListResponse>("/api/metricas/analisis/");
  return data.results;
}

export async function getAnalisisWithCookie(cookieHeader: string): Promise<Analisis[]> {
  const data = await fetchJSONWithCookie<AnalisisListResponse>("/api/metricas/analisis/", cookieHeader);
  return data.results;
}

export async function getAnalisisById(id: string | number): Promise<Analisis | null> {
  const response = await fetch(`${BACKEND_BASE_URL}/api/metricas/analisis/${id}/`, {
    cache: "no-store",
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
  return (await response.json()) as Analisis;
}

export async function updateAnalisis(id: string | number, data: Partial<Analisis>): Promise<Analisis> {
  return await requestJSON<Analisis>(`/api/metricas/analisis/${id}/`, "PATCH", data);
}

export async function deleteAnalisis(id: string | number): Promise<void> {
  await requestJSON<void>(`/api/metricas/analisis/${id}/`, "DELETE");
}

export async function getUltimoAnalisisLote(loteId: string | number): Promise<Analisis | null> {
  const response = await fetch(`${BACKEND_BASE_URL}/api/metricas/analisis/lote/${loteId}/ultimo/`, {
    cache: "no-store",
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
  const data = (await response.json()) as { results: Analisis | null };
  return data.results;
}

export async function getUltimoAnalisisCultivo(cultivoId: string | number): Promise<Analisis | null> {
  const response = await fetch(`${BACKEND_BASE_URL}/api/metricas/analisis/cultivo/${cultivoId}/ultimo/`, {
    cache: "no-store",
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
  const data = (await response.json()) as { results: Analisis | null };
  return data.results;
}

// ==================== MÉTRICAS ====================

export async function createMetrica(input: MetricaInput): Promise<MetricaRaw> {
  return await requestJSON<MetricaRaw>("/api/metricas/", "POST", input);
}

export async function getMetricasByCultivo(
  cultivoId: string | number,
): Promise<MetricaListResponse> {
  return await fetchJSON<MetricaListResponse>(`/api/metricas/cultivo/${cultivoId}/`);
}

export async function getMetricasByCultivoWithCookie(
  cultivoId: string | number,
  cookieHeader: string,
): Promise<MetricaListResponse> {
  return await fetchJSONWithCookie<MetricaListResponse>(`/api/metricas/cultivo/${cultivoId}/`, cookieHeader);
}

export async function getMetricasByLote(loteId: string | number): Promise<MetricaRaw[]> {
  return await fetchJSON<MetricaRaw[]>(`/api/metricas/lote/${loteId}/`);
}

export async function getMetricasByLoteWithCookie(
  loteId: string | number,
  cookieHeader: string,
): Promise<MetricaRaw[]> {
  return await fetchJSONWithCookie<MetricaRaw[]>(`/api/metricas/lote/${loteId}/`, cookieHeader);
}

export function resumirMetricasPorTipo(metricas: MetricaRaw[]) {
  const resumen: Record<MetricaRaw["tipo_resultado"], MetricaRaw | null> = {
    cantidad_frutos: null,
    frutos_maduros: null,
    estimacion_cosecha: null,
    porcentaje_madurez: null,
  };
  for (const metrica of metricas) {
    if (!resumen[metrica.tipo_resultado]) {
      resumen[metrica.tipo_resultado] = metrica;
    }
  }
  return resumen;
}

/**
 * Envía dataset de imágenes al backend para inferencia directa.
 * La sesión Django se incluye automáticamente vía credentials: 'include'.
 */
export async function procesarDataset(
  cultivoId: number,
  imagenes: File[],
  loteId?: number | null,
): Promise<ProcesamientoResponse> {
  const formData = new FormData();
  formData.append("cultivo_id", String(cultivoId));
  if (loteId != null) formData.append("lote_id", String(loteId));
  for (const img of imagenes) {
    formData.append("imagenes", img);
  }

  const response = await fetch(`${BACKEND_BASE_URL}/api/metricas/procesar/`, {
    method: "POST",
    cache: "no-store",
    credentials: "include",
    headers: { Accept: "application/json" },
    body: formData,
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

  return (await response.json()) as ProcesamientoResponse;
}

// ==================== CONFIGURACIÓN DE REPOSITORIO (por usuario) ====================

export async function getRepositoryConfigs(): Promise<RepositorioListResponse> {
  return await fetchJSON<RepositorioListResponse>("/api/repository/config/");
}

export async function createRepositoryConfig(
  input: RepositorioConfigInput,
): Promise<RepositorioCreateResponse> {
  return await requestJSON<RepositorioCreateResponse>("/api/repository/config/", "POST", input);
}

export async function testRepositoryConfigPayload(
  input: RepositorioConfigInput,
): Promise<RepositorioTestResponse> {
  return await requestJSON<RepositorioTestResponse>("/api/repository/config/test/", "POST", input);
}

export async function updateRepositoryConfig(
  id: number,
  input: RepositorioConfigEditInput,
): Promise<RepositorioImagen> {
  return await requestJSON<RepositorioImagen>(`/api/repository/config/${id}/`, "PATCH", input);
}

export async function testRepositoryConfig(id: number): Promise<RepositorioTestResponse> {
  return await requestJSON<RepositorioTestResponse>(`/api/repository/config/${id}/test/`, "POST");
}

export async function activateRepositoryConfig(id: number): Promise<RepositorioImagen> {
  return await requestJSON<RepositorioImagen>(`/api/repository/config/${id}/activate/`, "POST");
}

export async function deactivateRepositoryConfig(id: number): Promise<RepositorioImagen> {
  return await requestJSON<RepositorioImagen>(`/api/repository/config/${id}/deactivate/`, "POST");
}

// ==================== REPOSITORIO (Cloudinary) ====================

export async function syncRepository(
  cultivoId: number,
  loteId?: number | null,
  carpeta?: string,
): Promise<RepositorySyncResponse> {
  return await requestJSON<RepositorySyncResponse>("/api/repository/sync/", "POST", {
    cultivo_id: cultivoId,
    lote_id: loteId ?? undefined,
    carpeta: carpeta !== undefined ? carpeta : undefined,
  });
}

/** GET /api/repository/folders/ — carpetas disponibles en Cloudinary, consultadas en vivo. */
export async function getRepositoryFolders(): Promise<RepositoryFoldersResponse> {
  return await fetchJSON<RepositoryFoldersResponse>("/api/repository/folders/");
}

export async function getRepositoryImages(
  filters: RepositoryImagesFilters,
): Promise<RepositoryImagesResponse> {
  const params = new URLSearchParams();
  params.set("cultivo_id", String(filters.cultivoId));
  if (filters.loteId != null) params.set("lote_id", String(filters.loteId));
  if (filters.estado) params.set("estado", filters.estado);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? 20));

  return await fetchJSON<RepositoryImagesResponse>(`/api/repository/images/?${params.toString()}`);
}

export async function uploadRepositoryImages(
  cultivoId: number,
  imagenes: File[],
  loteId?: number | null,
): Promise<ImagenRepositorio[]> {
  const formData = new FormData();
  formData.append("cultivo_id", String(cultivoId));
  if (loteId != null) formData.append("lote_id", String(loteId));
  for (const img of imagenes) {
    formData.append("imagenes", img);
  }

  const response = await fetch(`${BACKEND_BASE_URL}/api/repository/images/upload/`, {
    method: "POST",
    cache: "no-store",
    credentials: "include",
    headers: { Accept: "application/json" },
    body: formData,
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

  const data = (await response.json()) as { results: ImagenRepositorio[] };
  return data.results;
}

export async function getRepositoryImage(id: number): Promise<ImagenRepositorio> {
  return await fetchJSON<ImagenRepositorio>(`/api/repository/images/${id}/`);
}

export async function deleteRepositoryImage(id: number): Promise<void> {
  await requestJSON<void>(`/api/repository/images/${id}/`, "DELETE");
}

export async function processRepositoryImages(
  cultivoId: number,
  imageIds: number[],
  loteId?: number | null,
  notas?: string,
): Promise<RepositoryProcessResponse> {
  return await requestJSON<RepositoryProcessResponse>("/api/repository/images/process/", "POST", {
    cultivo_id: cultivoId,
    lote_id: loteId ?? undefined,
    image_ids: imageIds,
    notas,
  });
}

/**
 * Procesa automáticamente todas las imágenes pendientes del cultivo (sin
 * selección manual) — POST /api/repository/process-all/.
 */
export async function processAllRepositoryImages(
  cultivoId: number,
  loteId?: number | null,
): Promise<RepositoryProcessAllResponse> {
  return await requestJSON<RepositoryProcessAllResponse>("/api/repository/process-all/", "POST", {
    cultivo_id: cultivoId,
    lote_id: loteId ?? undefined,
  });
}

// ==================== AUTH — SESIÓN DJANGO ====================

/**
 * Autentica al usuario. El backend crea una sesión Django y responde con
 * Set-Cookie: sessionid=... El browser almacena esa cookie automáticamente.
 * credentials: 'include' garantiza que la cookie se incluya en requests futuros.
 */
export async function login(
  username: string,
  password: string,
): Promise<LoginResponse> {
  return await requestJSON<LoginResponse>("/api/auth/login/", "POST", {
    username,
    password,
  });
}

/**
 * Crea un usuario nuevo en Django (persiste en PostgreSQL) e inicia sesión.
 */
export async function register(
  username: string,
  email: string,
  password: string,
  password2: string,
): Promise<RegisterResponse> {
  return await requestJSON<RegisterResponse>("/api/auth/register/", "POST", {
    username,
    email,
    password,
    password2,
  });
}

/**
 * Cierra la sesión en el servidor (elimina la fila en django_session)
 * y limpia la cookie. Siempre limpia localStorage local.
 */
export async function logout(): Promise<void> {
  try {
    await requestJSON<void>("/api/auth/logout/", "POST");
  } catch {
    // Siempre limpia localmente aunque falle el backend
  }
  clearAuthData();
}

/**
 * Retorna el usuario autenticado actual verificando con el backend.
 * Lanza Error si la sesión no es válida o expiró.
 * Usar en ProtectedRoute para verificar sesión real.
 */
export async function getCurrentUser(): Promise<User> {
  return await fetchJSON<User>("/api/auth/me/");
}