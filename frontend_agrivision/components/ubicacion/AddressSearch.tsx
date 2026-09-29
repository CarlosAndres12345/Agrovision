"use client";

import React, { useState } from "react";

import { buscarDireccion } from "../../lib/geolocationApi";
import type { AddressSearchResult } from "../../types/locationTypes";

const MIN_QUERY_LENGTH = 3;

type Props = {
  onResults: (results: AddressSearchResult[]) => void;
};

/**
 * Campo de búsqueda de dirección/lugar. La búsqueda solo se dispara al
 * pulsar "Buscar" o Enter — nunca mientras el usuario escribe (sin
 * autocompletado por tecla, para respetar el límite de Nominatim).
 */
export default function AddressSearch({ onResults }: Props) {
  const [query, setQuery] = useState("");
  const [buscando, setBuscando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ejecutarBusqueda() {
    const texto = query.trim();
    if (texto.length < MIN_QUERY_LENGTH) {
      setError(`Escribe al menos ${MIN_QUERY_LENGTH} caracteres.`);
      return;
    }
    setBuscando(true);
    setError(null);
    try {
      const resultados = await buscarDireccion(texto);
      onResults(resultados);
      if (resultados.length === 0) {
        setError("No se encontraron resultados para esa búsqueda.");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "No se pudo buscar la dirección.");
      onResults([]);
    } finally {
      setBuscando(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      ejecutarBusqueda();
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Buscar dirección o lugar"
          className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
        />
        <button
          type="button"
          onClick={ejecutarBusqueda}
          disabled={buscando}
          className="shrink-0 rounded-md bg-gray-800 px-4 py-2 text-sm font-medium text-white hover:bg-gray-900 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {buscando ? "Buscando..." : "Buscar"}
        </button>
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
