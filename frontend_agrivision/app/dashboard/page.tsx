"use client";

import React, { useCallback, useEffect, useState } from "react";
import AuthLayout from "../../components/layout/AuthLayout";
import ProtectedRoute from "../../components/auth/ProtectedRoute";
import DashboardHeader from "../../components/dashboard/DashboardHeader";
import MetricCard from "../../components/ui/MetricCard";
import MetricsTrendPanel from "../../components/dashboard/MetricsTrendPanel";
import RadialProgressCard from "../../components/dashboard/RadialProgressCard";
import RecentRecordsTable from "../../components/dashboard/RecentRecordsTable";
import { getDashboardSummary } from "../../lib/api";
import type { DashboardSummary } from "../../types/dashboard";

function DashboardContent() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resumen = await getDashboardSummary();
      setData(resumen);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "No se pudo conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargar();
  }, [cargar]);

  return (
    <div className="w-full">
      <div className="mb-6">
        <DashboardHeader />
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-green-600 border-r-transparent" />
          Cargando resumen...
        </div>
      ) : error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <p className="font-medium">Error de conexión</p>
          <p className="mt-1 text-xs">{error}</p>
          <button
            type="button"
            onClick={cargar}
            className="mt-2 rounded-md border border-red-300 bg-white px-3 py-1 text-xs font-medium text-red-700 hover:bg-red-50"
          >
            Reintentar
          </button>
        </div>
      ) : data && data.total_analisis === 0 ? (
        <div className="av-card flex flex-col items-center justify-center gap-2 py-12 text-center">
          <p className="text-sm font-medium text-gray-700">Todavía no hay análisis registrados</p>
          <p className="text-xs text-gray-400">Procesa imágenes de un cultivo para ver el resumen aquí.</p>
        </div>
      ) : data ? (
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-12 lg:col-span-8 space-y-6">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <MetricCard title="Cantidad de frutos" value={data.cantidad_frutos} />
              <MetricCard title="Frutos maduros" value={data.frutos_maduros} />
              <MetricCard title="Estimación de cosecha" value={`${data.estimacion_cosecha} kg`} />
              <MetricCard
                title="Porcentaje de madurez"
                value={data.porcentaje_madurez !== null ? `${data.porcentaje_madurez}%` : "Sin datos"}
              />
            </div>

            <MetricsTrendPanel evolucion={data.evolucion} />

            <RecentRecordsTable records={data.registros_recientes} />
          </div>

          <div className="col-span-12 lg:col-span-4 space-y-4">
            <RadialProgressCard percent={data.porcentaje_madurez} />
            <div className="av-card p-4">
              <div className="text-sm text-gray-500">Total de análisis</div>
              <div className="mt-2 text-2xl font-semibold text-gray-900">{data.total_analisis}</div>
              <div className="mt-1 text-xs text-gray-400">Histórico completo, todos los cultivos.</div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <AuthLayout>
        <DashboardContent />
      </AuthLayout>
    </ProtectedRoute>
  );
}
