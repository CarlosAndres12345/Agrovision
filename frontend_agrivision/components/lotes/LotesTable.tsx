"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useState } from "react";

import type { Lote } from "../../types/lote";
import { deleteLote } from "../../lib/api";
import ConfirmDelete from "../ui/ConfirmDelete";

type Props = {
  lotes: Lote[];
};

export default function LotesTable({ lotes }: Props) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [cultivoFilter, setCultivoFilter] = useState<string>("all");
  const [search, setSearch] = useState<string>("");

  const cultivosDisponibles = Array.from(new Set(lotes.map((lote) => lote.cultivo_id))).sort(
    (a, b) => a - b,
  );

  const lotesFiltrados = lotes.filter((lote) => {
    const matchesCultivo = cultivoFilter === "all" || String(lote.cultivo_id) === cultivoFilter;
    const searchable = `${lote.id} ${lote.nombre} ${lote.descripcion}`.toLowerCase();
    const matchesSearch = search.trim() === "" || searchable.includes(search.trim().toLowerCase());
    return matchesCultivo && matchesSearch;
  });

  async function handleDelete(id: number) {
    setError(null);
    try {
      await deleteLote(id);
      router.refresh();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "No se pudo eliminar el lote.");
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 md:grid-cols-2">
        <label className="space-y-1 text-sm">
          <span className="font-medium text-slate-700">Buscar</span>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Nombre, descripción o ID"
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          />
        </label>

        <label className="space-y-1 text-sm">
          <span className="font-medium text-slate-700">Cultivo</span>
          <select
            value={cultivoFilter}
            onChange={(event) => setCultivoFilter(event.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          >
            <option value="all">Todos</option>
            {cultivosDisponibles.map((cultivoId) => (
              <option key={cultivoId} value={cultivoId}>
                Cultivo #{cultivoId}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}

      {lotes.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-500">
          No hay lotes registrados todavía.
        </div>
      ) : lotesFiltrados.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-500">
          No hay lotes que coincidan con los filtros actuales.
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50/90 text-left text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                <tr>
                  <th className="px-5 py-4">ID</th>
                  <th className="px-5 py-4">Nombre</th>
                  <th className="px-5 py-4">Área</th>
                  <th className="px-5 py-4">Cultivo</th>
                  <th className="px-5 py-4">Descripción</th>
                  <th className="px-5 py-4">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {lotesFiltrados.map((lote) => (
                  <tr key={lote.id} className="transition hover:bg-slate-50/60">
                    <td className="whitespace-nowrap px-5 py-4 font-medium text-slate-900">{lote.id}</td>
                    <td className="px-5 py-4 text-slate-900">
                      <div className="font-medium">{lote.nombre}</div>
                      <div className="text-xs text-slate-400">
                        {lote.ancho && lote.largo ? `${lote.ancho} x ${lote.largo} m` : "Sin dimensiones"}
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-600">
                      {lote.area_lote} ha
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-600">Cultivo #{lote.cultivo_id}</td>
                    <td className="px-5 py-4 text-slate-600">{lote.descripcion || "Sin descripción."}</td>
                    <td className="px-5 py-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <Link
                          href={`/lotes/${lote.id}`}
                          className="inline-flex items-center rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:border-slate-300 hover:bg-slate-50"
                        >
                          Ver detalle
                        </Link>
                        <Link
                          href={`/lotes/${lote.id}/editar`}
                          className="inline-flex items-center rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 shadow-sm transition hover:bg-emerald-100"
                        >
                          Editar
                        </Link>
                        <ConfirmDelete
                          label="Eliminar"
                          message={`¿Deseas eliminar el lote \"${lote.nombre}\"? Esta acción no se puede deshacer.`}
                          onConfirm={() => handleDelete(lote.id)}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
