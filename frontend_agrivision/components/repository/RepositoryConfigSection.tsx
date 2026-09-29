"use client";

import React, { useCallback, useEffect, useState } from "react";

import {
  activateRepositoryConfig,
  deactivateRepositoryConfig,
  getRepositoryConfigs,
  getRepositoryFolders,
  testRepositoryConfig,
} from "../../lib/api";
import type { RepositorioImagen } from "../../types/repository";
import RepositoryConfigForm from "./RepositoryConfigForm";

type Props = {
  /** El cultivo actualmente seleccionado en el módulo (o null si no hay ninguno). */
  cultivoSeleccionadoId: number | null;
  syncing: boolean;
  onSincronizar: () => void;
  /** Sincroniza usando la carpeta que el usuario eligió en el selector, en vez de la ya guardada. */
  onSincronizarCarpeta: (carpeta: string) => void;
  /** Se llama después de crear/activar/desactivar un repositorio — el módulo recarga imágenes. */
  onRepositorioActivoCambio: () => void;
};

type FolderLoadState = "idle" | "loading" | "loaded" | "error";

const ESTADO_CONEXION_LABEL: Record<string, string> = {
  sin_probar: "Sin probar",
  conectado: "Conectado",
  fallido: "Conexión fallida",
};

const ESTADO_CONEXION_BADGE: Record<string, string> = {
  sin_probar: "bg-gray-100 text-gray-600",
  conectado: "bg-green-100 text-green-700",
  fallido: "bg-red-100 text-red-700",
};

export default function RepositoryConfigSection({
  cultivoSeleccionadoId,
  syncing,
  onSincronizar,
  onSincronizarCarpeta,
  onRepositorioActivoCambio,
}: Props) {
  const [configs, setConfigs] = useState<RepositorioImagen[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [editando, setEditando] = useState<RepositorioImagen | null>(null);
  const [mostrarCambiar, setMostrarCambiar] = useState(false);

  const [probando, setProbando] = useState(false);
  const [probarMensaje, setProbarMensaje] = useState<string | null>(null);
  const [descubrimientoMensaje, setDescubrimientoMensaje] = useState<string | null>(null);

  const [folders, setFolders] = useState<string[]>([]);
  const [folderState, setFolderState] = useState<FolderLoadState>("idle");
  const [folderError, setFolderError] = useState<string | null>(null);
  const [carpetaSeleccionada, setCarpetaSeleccionada] = useState<string>("");

  const cargarConfigs = useCallback(async () => {
    try {
      const data = await getRepositoryConfigs();
      setConfigs(data.results);
      setLoadError(null);
    } catch (err: unknown) {
      setLoadError(err instanceof Error ? err.message : "No se pudieron cargar los repositorios.");
    }
  }, []);

  useEffect(() => {
    cargarConfigs();
  }, [cargarConfigs]);

  const activo = configs?.find((c) => c.activo) ?? null;
  const otros = configs?.filter((c) => !c.activo) ?? [];

  // Precarga el selector con la carpeta ya guardada del repositorio activo,
  // la primera vez que se conoce (no sobreescribe una elección en curso).
  useEffect(() => {
    if (activo && carpetaSeleccionada === "" && activo.carpeta_raiz) {
      setCarpetaSeleccionada(activo.carpeta_raiz);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activo?.id]);

  async function handleActualizarCarpetas() {
    setFolderState("loading");
    setFolderError(null);
    try {
      const resultado = await getRepositoryFolders();
      if (!resultado.ok) {
        setFolderState("error");
        setFolderError(resultado.message);
        return;
      }
      setFolders(resultado.folders);
      setFolderState("loaded");
      if (resultado.folders.length > 0 && !resultado.folders.includes(carpetaSeleccionada)) {
        setCarpetaSeleccionada(resultado.folders[0]);
      }
    } catch (err: unknown) {
      setFolderState("error");
      setFolderError(err instanceof Error ? err.message : "No se pudo conectar con Cloudinary.");
    }
  }

  function handleSincronizarCarpetaClick() {
    if (!carpetaSeleccionada) {
      setFolderError("No se seleccionó ninguna carpeta.");
      return;
    }
    setFolderError(null);
    onSincronizarCarpeta(carpetaSeleccionada);
  }

  function handleSaved(_config: RepositorioImagen, descubrimiento?: { cantidad_encontradas: number; hay_mas: boolean }) {
    setMostrarFormulario(false);
    setEditando(null);
    setMostrarCambiar(false);
    setProbarMensaje(null);
    if (descubrimiento) {
      setDescubrimientoMensaje(
        `Conexión guardada. Se encontraron ${descubrimiento.cantidad_encontradas} imagen(es)${
          descubrimiento.hay_mas ? " o más" : ""
        } en la carpeta configurada — selecciona un cultivo y sincroniza para traerlas a AgriVision.`,
      );
    }
    cargarConfigs();
    onRepositorioActivoCambio();
  }

  async function handleProbarActivo() {
    if (!activo) return;
    setProbando(true);
    setProbarMensaje(null);
    try {
      const resultado = await testRepositoryConfig(activo.id);
      setProbarMensaje(resultado.mensaje);
    } catch (err: unknown) {
      setProbarMensaje(err instanceof Error ? err.message : "No se pudo probar la conexión.");
    } finally {
      setProbando(false);
      cargarConfigs();
    }
  }

  async function handleActivar(id: number) {
    await activateRepositoryConfig(id);
    setMostrarCambiar(false);
    await cargarConfigs();
    onRepositorioActivoCambio();
  }

  async function handleDesactivar() {
    if (!activo) return;
    await deactivateRepositoryConfig(activo.id);
    await cargarConfigs();
    onRepositorioActivoCambio();
  }

  if (configs === null && !loadError) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-500">
        Cargando configuración de repositorio...
      </div>
    );
  }

  if (loadError) {
    return <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{loadError}</div>;
  }

  if (mostrarFormulario) {
    return (
      <RepositoryConfigForm
        initialValues={editando}
        onSaved={handleSaved}
        onCancel={() => {
          setMostrarFormulario(false);
          setEditando(null);
        }}
      />
    );
  }

  if (!activo) {
    return (
      <div className="space-y-3 rounded-lg border border-dashed border-gray-300 bg-gray-50 px-4 py-5 text-center">
        <p className="text-sm font-medium text-gray-700">No tienes un repositorio de imágenes configurado.</p>
        <button
          type="button"
          onClick={() => setMostrarFormulario(true)}
          className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
        >
          Configurar repositorio
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-gray-900">{activo.nombre}</p>
          <p className="text-xs text-gray-500">
            Cloudinary · {activo.cantidad_imagenes} imagen(es) registrada(s)
            {activo.ultimo_sync ? ` · última sincronización ${new Date(activo.ultimo_sync).toLocaleString()}` : " · sin sincronizar aún"}
          </p>
        </div>
        <span className={`rounded-full px-2 py-1 text-xs font-medium ${ESTADO_CONEXION_BADGE[activo.estado_conexion]}`}>
          {ESTADO_CONEXION_LABEL[activo.estado_conexion]}
        </span>
      </div>

      {descubrimientoMensaje && (
        <div className="rounded-md border border-green-200 bg-green-50 px-3 py-2 text-xs text-green-700">
          {descubrimientoMensaje}
        </div>
      )}
      {probarMensaje && (
        <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-700">{probarMensaje}</div>
      )}

      <div className="space-y-2 rounded-md border border-gray-200 bg-gray-50 p-3">
        <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Carpeta de Cloudinary</p>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleActualizarCarpetas}
            disabled={folderState === "loading"}
            className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {folderState === "loading" ? "Actualizando..." : "Actualizar carpetas"}
          </button>

          <select
            value={carpetaSeleccionada}
            onChange={(e) => setCarpetaSeleccionada(e.target.value)}
            disabled={folders.length === 0}
            className="min-w-[10rem] rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400"
          >
            {folders.length === 0 ? (
              <option value="">
                {folderState === "loaded" ? "No hay carpetas disponibles" : "Actualiza para ver las carpetas"}
              </option>
            ) : (
              folders.map((carpeta) => (
                <option key={carpeta} value={carpeta}>
                  {carpeta}
                </option>
              ))
            )}
          </select>

          <button
            type="button"
            onClick={handleSincronizarCarpetaClick}
            disabled={syncing || cultivoSeleccionadoId == null || !carpetaSeleccionada}
            title={cultivoSeleccionadoId == null ? "Selecciona un cultivo para sincronizar" : undefined}
            className="rounded-md bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {syncing ? "Sincronizando..." : "Sincronizar carpeta"}
          </button>
        </div>

        {folderError && <p className="text-xs text-red-600">{folderError}</p>}
        {!folderError && carpetaSeleccionada && (
          <p className="text-xs text-gray-500">Carpeta seleccionada: {carpetaSeleccionada}</p>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onSincronizar}
          disabled={syncing || cultivoSeleccionadoId == null}
          title={cultivoSeleccionadoId == null ? "Selecciona un cultivo para sincronizar" : undefined}
          className="rounded-md bg-gray-800 px-3 py-2 text-sm font-medium text-white hover:bg-gray-900 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {syncing ? "Sincronizando..." : "Sincronizar"}
        </button>
        <button
          type="button"
          onClick={() => {
            setEditando(activo);
            setMostrarFormulario(true);
          }}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Editar configuración
        </button>
        <button
          type="button"
          onClick={handleProbarActivo}
          disabled={probando}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {probando ? "Probando..." : "Probar conexión"}
        </button>
        <button
          type="button"
          onClick={() => setMostrarCambiar((v) => !v)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Cambiar repositorio
        </button>
        <button
          type="button"
          onClick={handleDesactivar}
          className="rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
        >
          Desactivar
        </button>
      </div>

      {mostrarCambiar && (
        <div className="space-y-2 rounded-md border border-gray-200 bg-gray-50 p-3">
          {otros.length > 0 ? (
            <ul className="space-y-1">
              {otros.map((c) => (
                <li key={c.id} className="flex items-center justify-between gap-2 text-sm">
                  <span className="text-gray-700">{c.nombre}</span>
                  <button
                    type="button"
                    onClick={() => handleActivar(c.id)}
                    className="rounded-md border border-gray-300 bg-white px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-100"
                  >
                    Activar
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-gray-500">No tienes otros repositorios guardados.</p>
          )}
          <button
            type="button"
            onClick={() => {
              setEditando(null);
              setMostrarFormulario(true);
            }}
            className="text-xs font-medium text-green-700 hover:underline"
          >
            + Configurar otro repositorio
          </button>
        </div>
      )}
    </div>
  );
}
