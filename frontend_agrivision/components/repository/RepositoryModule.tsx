"use client";

import React, { useEffect, useRef, useState } from "react";

import {
  getCultivos,
  getLotesByCultivo,
  syncRepository,
  getRepositoryImages,
  uploadRepositoryImages,
  processAllRepositoryImages,
} from "../../lib/api";
import type { Cultivo } from "../../types/cultivo";
import type { Lote } from "../../types/lote";
import type {
  ImagenRepositorio,
  ImagenRepositorioEstado,
  RepositoryImagesResumen,
  RepositoryProcessAllResponse,
} from "../../types/repository";
import RepositoryConfigSection from "./RepositoryConfigSection";
import RepositoryFilters from "./RepositoryFilters";
import RepositoryGallery from "./RepositoryGallery";
import RepositoryPagination from "./RepositoryPagination";
import RepositoryProcessSummary from "./RepositoryProcessSummary";

const PAGE_SIZE = 12;

const RESUMEN_VACIO: RepositoryImagesResumen = { total: 0, pendientes: 0, procesando: 0, procesadas: 0, con_error: 0 };

export default function RepositoryModule() {
  const [cultivos, setCultivos] = useState<Cultivo[]>([]);
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [cultivoId, setCultivoId] = useState<number | null>(null);
  const [loteId, setLoteId] = useState<number | null>(null);
  const [estado, setEstado] = useState<ImagenRepositorioEstado | "">("");
  const isFirstLoteLoad = useRef(true);

  const [imagenes, setImagenes] = useState<ImagenRepositorio[]>([]);
  const [resumen, setResumen] = useState<RepositoryImagesResumen>(RESUMEN_VACIO);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loadingImages, setLoadingImages] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [syncNotice, setSyncNotice] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);

  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [procesandoTodo, setProcesandoTodo] = useState(false);
  const [procesarError, setProcesarError] = useState<string | null>(null);
  const [resultadoProceso, setResultadoProceso] = useState<RepositoryProcessAllResponse | null>(null);

  const autoSyncedRef = useRef<number | null>(null);

  useEffect(() => {
    getCultivos()
      .then(setCultivos)
      .catch(() => setLoadError("No se pudieron cargar los cultivos."));
  }, []);

  useEffect(() => {
    if (cultivoId == null) {
      setLotes([]);
      if (!isFirstLoteLoad.current) setLoteId(null);
      isFirstLoteLoad.current = false;
      return;
    }
    getLotesByCultivo(cultivoId)
      .then((data) => {
        setLotes(data);
        if (!isFirstLoteLoad.current) setLoteId(null);
        isFirstLoteLoad.current = false;
      })
      .catch(() => setLotes([]));
  }, [cultivoId]);

  async function cargarImagenes() {
    if (cultivoId == null) {
      setImagenes([]);
      setResumen(RESUMEN_VACIO);
      return;
    }
    setLoadingImages(true);
    setLoadError(null);
    try {
      const data = await getRepositoryImages({
        cultivoId,
        loteId,
        estado,
        page,
        pageSize: PAGE_SIZE,
      });
      setImagenes(data.results);
      setTotalPages(data.total_pages);
      setResumen(data.resumen);
    } catch (err: unknown) {
      setLoadError(err instanceof Error ? err.message : "No se pudieron cargar las imágenes.");
      setImagenes([]);
    } finally {
      setLoadingImages(false);
    }
  }

  useEffect(() => {
    cargarImagenes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cultivoId, loteId, estado, page]);

  // Sincronización automática: una vez por cultivo seleccionado.
  useEffect(() => {
    if (cultivoId == null || autoSyncedRef.current === cultivoId) return;
    autoSyncedRef.current = cultivoId;
    handleSincronizar(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cultivoId]);

  async function handleSincronizar(silencioso = false, carpeta?: string) {
    if (cultivoId == null) return;
    setSyncing(true);
    setSyncError(null);
    if (!silencioso) {
      setSyncMessage(null);
      setSyncNotice(null);
    }
    try {
      const resultado = await syncRepository(cultivoId, loteId, carpeta);
      // Éxito (verde) solo si se crearon asociaciones nuevas para este
      // cultivo. Cualquier otro desenlace no técnico (ya estaban asociadas,
      // carpeta vacía) es informativo (ámbar), no un error ni un logro nuevo.
      if (resultado.associated > 0) {
        setSyncMessage(resultado.message);
        setSyncNotice(null);
      } else {
        setSyncNotice(resultado.message);
        setSyncMessage(null);
      }
      await cargarImagenes();
    } catch (err: unknown) {
      setSyncError(err instanceof Error ? err.message : "No se pudo sincronizar con Cloudinary.");
    } finally {
      setSyncing(false);
    }
  }

  async function handleUpload() {
    if (cultivoId == null || uploadFiles.length === 0) return;
    setUploading(true);
    setUploadError(null);
    try {
      await uploadRepositoryImages(cultivoId, uploadFiles, loteId);
      setUploadFiles([]);
      await cargarImagenes();
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "No se pudieron cargar las imágenes.");
    } finally {
      setUploading(false);
    }
  }

  async function handleProcesarTodo() {
    if (cultivoId == null) return;
    setProcesandoTodo(true);
    setProcesarError(null);
    setResultadoProceso(null);
    try {
      const resultado = await processAllRepositoryImages(cultivoId, loteId);
      setResultadoProceso(resultado);
      await cargarImagenes();
    } catch (err: unknown) {
      setProcesarError(err instanceof Error ? err.message : "No se pudieron procesar las imágenes pendientes.");
    } finally {
      setProcesandoTodo(false);
    }
  }

  return (
    <div className="space-y-5">
      <RepositoryConfigSection
        cultivoSeleccionadoId={cultivoId}
        syncing={syncing}
        onSincronizar={() => handleSincronizar(false)}
        onSincronizarCarpeta={(carpeta) => handleSincronizar(false, carpeta)}
        onRepositorioActivoCambio={() => {
          autoSyncedRef.current = null;
          if (cultivoId != null) cargarImagenes();
        }}
      />

      <RepositoryFilters
        cultivos={cultivos}
        lotes={lotes}
        cultivoId={cultivoId}
        loteId={loteId}
        estado={estado}
        onCultivoChange={(id) => {
          setCultivoId(id);
          setPage(1);
          setResultadoProceso(null);
        }}
        onLoteChange={(id) => {
          setLoteId(id);
          setPage(1);
        }}
        onEstadoChange={(value) => {
          setEstado(value);
          setPage(1);
        }}
      />

      {cultivoId == null ? (
        <div className="rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-500">
          Selecciona un cultivo para ver su repositorio de imágenes en Cloudinary.
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-md border border-gray-200 bg-white px-3 py-2">
              <div className="text-xs uppercase tracking-wide text-gray-500">Total</div>
              <div className="mt-1 text-lg font-semibold text-gray-900">{resumen.total}</div>
            </div>
            <div className="rounded-md border border-gray-200 bg-white px-3 py-2">
              <div className="text-xs uppercase tracking-wide text-gray-500">Pendientes</div>
              <div className="mt-1 text-lg font-semibold text-gray-900">{resumen.pendientes}</div>
            </div>
            <div className="rounded-md border border-gray-200 bg-white px-3 py-2">
              <div className="text-xs uppercase tracking-wide text-gray-500">Procesadas</div>
              <div className="mt-1 text-lg font-semibold text-gray-900">{resumen.procesadas}</div>
            </div>
            <div className="rounded-md border border-gray-200 bg-white px-3 py-2">
              <div className="text-xs uppercase tracking-wide text-gray-500">Con error</div>
              <div className="mt-1 text-lg font-semibold text-gray-900">{resumen.con_error}</div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <input
              type="file"
              multiple
              accept=".jpg,.jpeg,.png,.webp,.bmp"
              onChange={(e) => setUploadFiles(e.target.files ? Array.from(e.target.files) : [])}
              className="text-sm text-gray-600 file:mr-3 file:rounded-md file:border-0 file:bg-green-50 file:px-3 file:py-2 file:text-sm file:font-medium file:text-green-700 hover:file:bg-green-100"
            />
            <button
              type="button"
              onClick={handleUpload}
              disabled={uploading || uploadFiles.length === 0}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {uploading ? "Subiendo..." : "Cargar imágenes"}
            </button>

            <button
              type="button"
              onClick={handleProcesarTodo}
              disabled={procesandoTodo || resumen.pendientes === 0}
              title={resumen.pendientes === 0 ? "No hay imágenes pendientes por procesar." : undefined}
              className="ml-auto rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {procesandoTodo
                ? "Procesando imágenes..."
                : `Procesar imágenes pendientes${resumen.pendientes > 0 ? ` (${resumen.pendientes})` : ""}`}
            </button>
          </div>

          {syncMessage && (
            <div className="rounded-md border border-green-200 bg-green-50 px-3 py-2 text-xs text-green-700">
              {syncMessage}
            </div>
          )}
          {syncNotice && (
            <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
              {syncNotice}
            </div>
          )}
          {syncError && (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
              {syncError}
            </div>
          )}
          {uploadError && (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
              {uploadError}
            </div>
          )}
          {procesarError && (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
              {procesarError}
            </div>
          )}

          {resultadoProceso && (
            <RepositoryProcessSummary
              resultado={resultadoProceso}
              cultivoId={cultivoId}
              onVolver={() => setResultadoProceso(null)}
            />
          )}

          <RepositoryGallery imagenes={imagenes} loading={loadingImages} error={loadError} />

          <RepositoryPagination page={page} totalPages={totalPages} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
