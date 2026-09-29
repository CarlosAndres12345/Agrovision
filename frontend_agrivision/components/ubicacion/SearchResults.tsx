"use client";

import React from "react";

import type { AddressSearchResult } from "../../types/locationTypes";

type Props = {
  results: AddressSearchResult[];
  onSelect: (result: AddressSearchResult) => void;
};

/** Lista de resultados de búsqueda (máximo 5, ya limitados por el backend). */
export default function SearchResults({ results, onSelect }: Props) {
  if (results.length === 0) return null;

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200">
      <p className="border-b border-gray-100 bg-gray-50 px-3 py-1.5 text-xs font-medium uppercase tracking-wide text-gray-500">
        Resultados encontrados
      </p>
      <ul className="divide-y divide-gray-100">
        {results.map((result, index) => (
          <li key={`${result.lat}-${result.lon}-${index}`}>
            <button
              type="button"
              onClick={() => onSelect(result)}
              className="block w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-green-50"
            >
              {result.displayName}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
