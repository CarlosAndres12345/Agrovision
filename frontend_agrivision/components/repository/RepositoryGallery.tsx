"use client";

import React from "react";

import type { ImagenRepositorio } from "../../types/repository";

type Props = {
  imagenes: ImagenRepositorio[];
  loading: boolean;
  error: string | null;
};

const ESTADO_BADGE: Record<string, string> = {
  disponible: "bg-gray-100 text-gray-600",
  procesando: "bg-amber-100 text-amber-700",
  procesada: "bg-green-100 text-green-700",
  error: "bg-red-100 text-red-700",
};

const ESTADO_LABEL: Record<string, string> = {
  disponible: "Pendiente",
  procesando: "Procesando",
  procesada: "Procesada",
  error: "Error",
};

/** Galería de solo lectura — la selección manual de imágenes ya no forma parte del flujo. */
export default function RepositoryGallery({ imagenes, loading, error }: Props) {
  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center rounded-lg border border-gray-200 bg-gray-50">
        <p className="text-sm text-gray-500">Cargando imágenes...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
    );
  }

  if (imagenes.length === 0) {
    return (
      <div className="flex h-48 flex-col items-center justify-center gap-1 rounded-lg border border-dashed border-gray-300 bg-gray-50 text-center">
        <p className="text-sm font-medium text-gray-600">Sin imágenes</p>
        <p className="text-xs text-gray-400">Sincroniza o sube imágenes para este cultivo.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
      {imagenes.map((img) => (
        <div key={img.id} className="relative overflow-hidden rounded-lg border-2 border-transparent text-left">
          <img
            src={img.secure_url}
            alt={img.nombre_original || img.public_id}
            className="h-28 w-full object-cover"
          />
          <span
            className={`absolute left-1 top-1 rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${
              ESTADO_BADGE[img.estado] ?? "bg-gray-100 text-gray-600"
            }`}
          >
            {ESTADO_LABEL[img.estado] ?? img.estado}
          </span>
          <span className="block truncate bg-white px-2 py-1 text-xs text-gray-600">
            {img.nombre_original || img.public_id}
          </span>
        </div>
      ))}
    </div>
  );
}
