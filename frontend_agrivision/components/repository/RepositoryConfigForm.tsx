"use client";

import React, { useState } from "react";

import { createRepositoryConfig, testRepositoryConfigPayload, updateRepositoryConfig } from "../../lib/api";
import type { RepositorioImagen } from "../../types/repository";

type Props = {
  /** Si se define, el formulario edita ese repositorio en vez de crear uno nuevo. */
  initialValues?: RepositorioImagen | null;
  onSaved: (config: RepositorioImagen, descubrimiento?: { cantidad_encontradas: number; hay_mas: boolean }) => void;
  onCancel: () => void;
};

type TestState = "idle" | "testing" | "ok" | "error";

export default function RepositoryConfigForm({ initialValues, onSaved, onCancel }: Props) {
  const editando = initialValues != null;

  const [nombre, setNombre] = useState(initialValues?.nombre ?? "");
  const [cloudName, setCloudName] = useState(initialValues?.cloud_name ?? "");
  const [apiKey, setApiKey] = useState(initialValues?.api_key ?? "");
  const [apiSecret, setApiSecret] = useState("");
  const [carpetaRaiz, setCarpetaRaiz] = useState(initialValues?.carpeta_raiz ?? "");

  const [testState, setTestState] = useState<TestState>("idle");
  const [testMessage, setTestMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const camposBasicosCompletos = nombre.trim() !== "" && cloudName.trim() !== "" && apiKey.trim() !== "";
  const puedeProbar = camposBasicosCompletos && apiSecret.trim() !== "";

  async function handleProbarConexion() {
    if (!puedeProbar) return;
    setTestState("testing");
    setTestMessage(null);
    try {
      const resultado = await testRepositoryConfigPayload({
        nombre: nombre.trim(),
        proveedor: "CLOUDINARY",
        cloud_name: cloudName.trim(),
        api_key: apiKey.trim(),
        api_secret: apiSecret.trim(),
        carpeta_raiz: carpetaRaiz.trim(),
      });
      setTestState(resultado.ok ? "ok" : "error");
      setTestMessage(resultado.mensaje);
    } catch (err: unknown) {
      setTestState("error");
      setTestMessage(err instanceof Error ? err.message : "No se pudo probar la conexión.");
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!camposBasicosCompletos || (!editando && apiSecret.trim() === "")) return;

    setSaving(true);
    setSaveError(null);
    try {
      if (editando && initialValues) {
        const actualizado = await updateRepositoryConfig(initialValues.id, {
          nombre: nombre.trim(),
          proveedor: "CLOUDINARY",
          cloud_name: cloudName.trim(),
          api_key: apiKey.trim(),
          api_secret: apiSecret.trim() || undefined,
          carpeta_raiz: carpetaRaiz.trim(),
        });
        onSaved(actualizado);
      } else {
        const resultado = await createRepositoryConfig({
          nombre: nombre.trim(),
          proveedor: "CLOUDINARY",
          cloud_name: cloudName.trim(),
          api_key: apiKey.trim(),
          api_secret: apiSecret.trim(),
          carpeta_raiz: carpetaRaiz.trim(),
        });
        onSaved(resultado.repositorio, resultado.descubrimiento);
      }
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : "No se pudo guardar la configuración.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="text-sm font-semibold text-gray-900">
        {editando ? "Editar repositorio" : "Configurar repositorio"}
      </h3>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="space-y-1">
          <span className="text-xs font-medium uppercase tracking-wide text-gray-500">Nombre del repositorio</span>
          <input
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
            placeholder="Mi cuenta de Cloudinary"
            required
          />
        </label>

        <label className="space-y-1">
          <span className="text-xs font-medium uppercase tracking-wide text-gray-500">Proveedor</span>
          <select
            value="CLOUDINARY"
            disabled
            className="w-full rounded-md border border-gray-300 bg-gray-50 px-3 py-2 text-sm text-gray-600"
          >
            <option value="CLOUDINARY">Cloudinary</option>
          </select>
        </label>

        <label className="space-y-1">
          <span className="text-xs font-medium uppercase tracking-wide text-gray-500">Cloud name</span>
          <input
            value={cloudName}
            onChange={(e) => setCloudName(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
            required
          />
        </label>

        <label className="space-y-1">
          <span className="text-xs font-medium uppercase tracking-wide text-gray-500">API key</span>
          <input
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
            required
          />
        </label>

        <label className="space-y-1">
          <span className="text-xs font-medium uppercase tracking-wide text-gray-500">API secret</span>
          <input
            type="password"
            value={apiSecret}
            onChange={(e) => setApiSecret(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
            placeholder={editando ? "Dejar vacío para conservar el actual" : ""}
            required={!editando}
          />
        </label>

        <label className="space-y-1 sm:col-span-2">
          <span className="text-xs font-medium uppercase tracking-wide text-gray-500">
            Carpeta inicial (opcional)
          </span>
          <input
            value={carpetaRaiz}
            onChange={(e) => setCarpetaRaiz(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
            placeholder="agrovision"
          />
          <span className="block text-xs text-gray-400">
            Solo un punto de partida — una vez guardado, elige y cambia de carpeta cuando quieras desde
            &quot;Carpeta de Cloudinary&quot; en el panel del repositorio, sin volver a editar esta configuración.
          </span>
        </label>
      </div>

      {testMessage && (
        <div
          className={`rounded-md border px-3 py-2 text-xs ${
            testState === "ok" ? "border-green-200 bg-green-50 text-green-700" : "border-red-200 bg-red-50 text-red-700"
          }`}
        >
          {testMessage}
        </div>
      )}
      {saveError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">{saveError}</div>
      )}

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={handleProbarConexion}
          disabled={!puedeProbar || testState === "testing"}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {testState === "testing" ? "Probando..." : "Probar conexión"}
        </button>
        <button
          type="submit"
          disabled={saving || !camposBasicosCompletos || (!editando && apiSecret.trim() === "")}
          className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? "Guardando..." : editando ? "Guardar cambios" : "Guardar y activar"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={saving}
          className="rounded-md px-3 py-2 text-sm font-medium text-gray-500 hover:bg-gray-50"
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}
