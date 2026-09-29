import React from "react";
import Link from "next/link";
import StatusBadge from "../ui/StatusBadge";
import type { RegistroReciente } from "../../types/dashboard";

type Props = {
  records: RegistroReciente[];
};

export default function RecentRecordsTable({ records }: Props) {
  return (
    <div className="av-card p-4">
      <div className="text-lg font-medium mb-3">Registros recientes</div>
      {records.length === 0 ? (
        <p className="text-sm text-gray-400">No hay análisis registrados todavía.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500">
                <th className="pb-2">ID</th>
                <th className="pb-2">Cultivo</th>
                <th className="pb-2">Lote</th>
                <th className="pb-2">Estado</th>
                <th className="pb-2">Fecha</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.id} className="border-t">
                  <td className="py-3 font-medium">
                    <Link href={`/cultivos/${r.cultivo_id}`} className="hover:text-emerald-700 hover:underline">
                      #{r.id}
                    </Link>
                  </td>
                  <td className="py-3">{r.cultivo}</td>
                  <td className="py-3">{r.lote ?? "—"}</td>
                  <td className="py-3">
                    <StatusBadge status={r.estado} />
                  </td>
                  <td className="py-3">{new Date(r.fecha).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
