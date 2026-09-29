import React from "react";
import type { EvolucionPunto } from "../../types/dashboard";

type Props = {
  evolucion: EvolucionPunto[];
};

export default function MetricsTrendPanel({ evolucion }: Props) {
  const maximo = Math.max(1, ...evolucion.map((p) => p.cantidad_frutos));

  return (
    <div className="av-card p-4">
      <div className="text-lg font-medium mb-3">Evolución de métricas</div>

      {evolucion.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-sm text-gray-400">
          Sin análisis en los últimos 30 días.
        </div>
      ) : (
        <div className="h-48 flex items-end gap-2 border-b border-gray-100 pb-1">
          {evolucion.map((punto) => {
            const alturaTotal = Math.max((punto.cantidad_frutos / maximo) * 100, 2);
            const alturaMaduros =
              punto.cantidad_frutos > 0 ? (punto.frutos_maduros / punto.cantidad_frutos) * alturaTotal : 0;
            return (
              <div key={punto.fecha} className="flex flex-1 flex-col items-center justify-end gap-1" title={punto.fecha}>
                <div className="relative w-full max-w-[28px] rounded-t bg-gray-100" style={{ height: `${alturaTotal}%` }}>
                  <div
                    className="absolute bottom-0 w-full rounded-t bg-emerald-500"
                    style={{ height: `${alturaMaduros}%` }}
                  />
                </div>
                <span className="text-[9px] text-gray-400">{punto.fecha.slice(5)}</span>
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-sm bg-gray-300" /> Frutos totales
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-sm bg-emerald-500" /> Maduros
        </span>
        <span className="ml-auto">Últimos 30 días</span>
      </div>
    </div>
  );
}
