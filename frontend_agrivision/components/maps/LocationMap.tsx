"use client";

import dynamic from "next/dynamic";

type Props = {
  latitud: number;
  longitud: number;
  className?: string;
  label?: string;
};

// Leaflet toca `window`/`document` al importarse — debe cargar solo en cliente.
const LeafletLocationMap = dynamic(() => import("./LeafletLocationMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-80 w-full items-center justify-center rounded-lg border border-gray-200 bg-gray-50">
      <p className="text-sm text-gray-500">Cargando mapa...</p>
    </div>
  ),
});

export default function LocationMap(props: Props) {
  return <LeafletLocationMap {...props} />;
}
