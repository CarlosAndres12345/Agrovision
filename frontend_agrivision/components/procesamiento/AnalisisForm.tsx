"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { getCultivos, getLotesByCultivo, BACKEND_BASE_URL } from "../../lib/api";
import type { Cultivo } from "../../types/cultivo";
import type { Lote } from "../../types/lote";
import type { Analisis } from "../../types/metrica";

type Props = {
  initialCultivoId?: number | null;
  initialLoteId?: number | null;
};

export default function AnalisisForm({ initialCultivoId, initialLoteId }: Props) {
  const [cultivos, setCultivos] = useState<Cultivo[]>([]);
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [cultivoId, setCultivoId] = useState<number | null>(initialCultivoId || null);
  const [loteId, setLoteId] = useState<number | null>(initialLoteId || null);

  const [imagenes, setImagenes] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);

  const [notas, setNotas] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultado, setResultado] = useState<Analisis | null>(null);

  const isFirstLoteLoad = useRef(true);

  useEffect(() => {
    getCultivos()
      .then(setCultivos)
      .catch(() => setError("No se pudieron cargar los cultivos."));
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
      .catch(() => {
        setLotes([]);
        isFirstLoteLoad.current = false;
      });
  }, [cultivoId]);

  // Manejar preview de imágenes
  useEffect(() => {
    const urls: string[] = [];
    imagenes.forEach((img) => {
      urls.push(URL.createObjectURL(img));
    });
    setPreviewUrls(urls);

    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [imagenes]);

  function handleArchivos(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files ? Array.from(e.target.files) : [];
    setImagenes(files);
    setError(null);
  }

  function handleReset() {
    setResultado(null);
    setImagenes([]);
    setNotas("");
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (cultivoId == null) {
      setError("Selecciona un cultivo.");
      return;
    }
    if (imagenes.length === 0) {
      setError("Carga al menos una imagen.");
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("cultivo_id", String(cultivoId));
      if (loteId != null) formData.append("lote_id", String(loteId));
      if (notas) formData.append("notas", notas);
      for (const img of imagenes) {
        formData.append("imagenes", img, img.name);
      }

      const response = await fetch(`${BACKEND_BASE_URL}/api/metricas/analisis/manual/`, {
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
      const responseData = await response.json();
      setResultado(responseData.analisis ?? responseData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al crear el análisis.");
    } finally {
      setLoading(false);
    }
  }

  // Resultado
  if (resultado) {
    const metricas = resultado.resultado_json || {};
    const metricasArray = Object.entries(metricas)
      .filter(([tipo]) => tipo !== "debug")
      .map(([tipo, datos]) => ({
        tipo,
        valor: datos.valor,
        unidad: datos.unidad,
      }));

    return (
      <div className="space-y-5">
        <div className="rounded-md bg-green-50 border border-green-200 px-4 py-3">
          <p className="text-sm font-semibold text-green-800">
            Análisis registrado correctamente
          </p>
          <p className="text-xs text-green-700 mt-0.5">Origen: Subida manual</p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {metricasArray.map((m) => (
            <div
              key={m.tipo}
              className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500">
                    {m.tipo.replace("_", " ")}
                  </div>
                  <div className="mt-1 flex items-end gap-1 text-2xl font-semibold text-gray-900">
                    <span>{m.valor}</span>
                    {m.unidad && (
                      <span className="text-sm font-medium text-gray-500">{m.unidad}</span>
                    )}
                  </div>
                </div>
                <div className="h-9 w-9 rounded-lg bg-green-600 opacity-90 shrink-0" />
              </div>
            </div>
          ))}
        </div>

        {resultado.imagen_urls && resultado.imagen_urls.length > 0 && (
          <div className="space-y-3">
            <p className="text-sm font-medium text-gray-700">Imágenes analizadas:</p>
            <div className="grid grid-cols-3 gap-3">
              {resultado.imagen_urls.map((entry, i) => {
                const src = typeof entry === "string" ? entry : entry.url;
                if (!src) return null;
                return (
                  <img
                    key={i}
                    src={src}
                    alt={`Imagen ${i + 1}`}
                    className="h-24 w-full object-cover rounded-md border border-gray-200"
                  />
                );
              })}
            </div>
          </div>
        )}

        <div className="flex flex-wrap gap-3 pt-1">
          <button
            onClick={handleReset}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Nuevo análisis
          </button>
          {resultado.lote_id ? (
            <a
              href={`/lotes/${resultado.lote_id}`}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 transition-colors"
            >
              Ver lote
            </a>
          ) : (
            <a
              href={`/cultivos/${resultado.cultivo_id}`}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 transition-colors"
            >
              Ver cultivo
            </a>
          )}
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">
        Este formulario analiza imágenes subidas directamente y de forma inmediata. Para
        procesar imágenes ya guardadas en Cloudinary, usa el módulo{" "}
        <Link href="/repositorio" className="font-medium underline">
          Repositorio
        </Link>
        .
      </div>

      {/* Cultivo */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Cultivo <span className="text-red-500">*</span>
        </label>
        <select
          value={cultivoId ?? ""}
          onChange={(e) => setCultivoId(e.target.value ? Number(e.target.value) : null)}
          className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
          required
        >
          <option value="">Seleccionar cultivo...</option>
          {cultivos.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre} — {c.tipo_fruto}
            </option>
          ))}
        </select>
      </div>

      {/* Lote (optional) */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Lote <span className="text-gray-400 font-normal">(opcional)</span>
        </label>
        <select
          value={loteId ?? ""}
          onChange={(e) => setLoteId(e.target.value ? Number(e.target.value) : null)}
          disabled={cultivoId == null || lotes.length === 0}
          className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
        >
          <option value="">Sin lote específico</option>
          {lotes.map((l) => (
            <option key={l.id} value={l.id}>
              {l.nombre}
            </option>
          ))}
        </select>
        {cultivoId != null && lotes.length === 0 && (
          <p className="mt-1 text-xs text-gray-400">
            Este cultivo no tiene lotes registrados.
          </p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">
          Imágenes del cultivo <span className="text-red-500">*</span>
        </label>
        <label className="mt-1 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-gray-300 px-6 py-10 text-center transition-colors hover:border-green-400 hover:bg-green-50/30">
          <svg
            className="h-10 w-10 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
            aria-hidden="true"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className="text-sm text-gray-600">
            <span className="font-medium text-green-600">Seleccionar imágenes</span>{" "}
            o arrastra aquí
          </span>
          <span className="text-xs text-gray-400">JPG, PNG, WEBP, BMP — múltiples archivos</span>
          {imagenes.length > 0 && (
            <span className="mt-1 text-sm font-semibold text-green-700">
              {imagenes.length} imagen{imagenes.length !== 1 ? "es" : ""} seleccionada
              {imagenes.length !== 1 ? "s" : ""}
            </span>
          )}
          <input
            type="file"
            multiple
            accept=".jpg,.jpeg,.png,.webp,.bmp"
            onChange={handleArchivos}
            className="sr-only"
          />
        </label>

        {previewUrls.length > 0 && (
          <div className="mt-3 grid grid-cols-4 gap-2">
            {previewUrls.map((url, i) => (
              <img
                key={i}
                src={url}
                alt={`Preview ${i + 1}`}
                className="h-20 w-full object-cover rounded-md border border-gray-200"
              />
            ))}
          </div>
        )}
      </div>

      {/* Notas */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Notas <span className="text-gray-400 font-normal">(opcional)</span>
        </label>
        <textarea
          value={notas}
          onChange={(e) => setNotas(e.target.value)}
          placeholder="Observaciones adicionales..."
          rows={3}
          className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
        />
      </div>

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading || cultivoId == null || imagenes.length === 0}
        className="w-full rounded-md bg-green-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? "Procesando..." : "Ejecutar análisis"}
      </button>
    </form>
  );
}
