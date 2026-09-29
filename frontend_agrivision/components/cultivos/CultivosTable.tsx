"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useState } from "react";

import type { Cultivo } from "../../types/cultivo";
import { deleteCultivo } from "../../lib/api";
import ConfirmDelete from "../ui/ConfirmDelete";
import StatusBadge from "../ui/StatusBadge";

type Props = {
  cultivos: Cultivo[];
};

export default function CultivosTable({ cultivos }: Props) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  async function handleDelete(id: number) {
    setError(null);
    try {
      await deleteCultivo(id);
      router.refresh();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "No se pudo eliminar el cultivo.");
    }
  }

  return (
    <div className="space-y-4">
      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}

      {cultivos.length === 0 ? (
        <div className="rounded-md border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500">
          No hay cultivos registrados todavía.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500">
                <th className="py-3 pr-4">ID</th>
                <th className="py-3 pr-4">Nombre</th>
                <th className="py-3 pr-4">Tipo de fruto</th>
                <th className="py-3 pr-4">Ubicación</th>
                <th className="py-3 pr-4">Área sembrada</th>
                <th className="py-3 pr-4">Fecha siembra</th>
                <th className="py-3 pr-4">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {cultivos.map((cultivo) => (
                <tr key={cultivo.id} className="border-b border-gray-100 last:border-0">
                  <td className="py-4 pr-4 font-medium">{cultivo.id}</td>
                  <td className="py-4 pr-4">
                    <div className="font-medium text-gray-900">{cultivo.nombre}</div>
                    <div className="max-w-xs truncate text-xs text-gray-500">{cultivo.descripcion}</div>
                  </td>
                  <td className="py-4 pr-4">
                    <StatusBadge status={cultivo.ultimo_analisis_estado ?? null} />
                    <div className="mt-1 text-xs text-gray-500">{cultivo.tipo_fruto}</div>
                  </td>
                  <td className="py-4 pr-4 text-gray-600">{cultivo.ubicacion}</td>
                  <td className="py-4 pr-4 text-gray-600">{cultivo.area_sembrada} ha</td>
                  <td className="py-4 pr-4 text-gray-600">{cultivo.fecha_siembra}</td>
                  <td className="py-4 pr-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <Link
                        href={`/cultivos/${cultivo.id}`}
                        className="rounded-md border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50"
                      >
                        Ver detalle
                      </Link>
                      <Link
                        href={`/cultivos/${cultivo.id}/editar`}
                        className="rounded-md border border-green-200 bg-green-50 px-3 py-2 text-xs font-medium text-green-700 hover:bg-green-100"
                      >
                        Editar
                      </Link>
                      <ConfirmDelete
                        label="Eliminar"
                        message={`¿Deseas eliminar el cultivo \"${cultivo.nombre}\"? Esta acción no se puede deshacer.`}
                        onConfirm={() => handleDelete(cultivo.id)}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
