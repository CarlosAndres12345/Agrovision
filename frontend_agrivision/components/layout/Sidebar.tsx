"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavItem = {
  label: string;
  href: string;
};

const nav: NavItem[] = [
  { label: "Inicio", href: "/dashboard" },
  { label: "Cultivos", href: "/cultivos" },
  { label: "Lotes", href: "/lotes" },
  { label: "Métricas", href: "/metricas" },
  { label: "Repositorio", href: "/repositorio" },
  { label: "Configuración", href: "/configuracion" },
];

export default function Sidebar() {
  const pathname = usePathname() || "/";

  return (
    <aside className="fixed left-0 top-0 bottom-0 z-30 flex w-64 min-h-screen flex-col border-r border-slate-800 bg-slate-950 px-4 py-6 text-white shadow-2xl shadow-slate-950/20">
      <div className="mb-8">
        <Link
          href="/dashboard"
          className="flex items-center gap-3 rounded-2xl px-2 py-1 transition-colors hover:bg-white/5"
        >
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500/15 font-semibold text-emerald-300 ring-1 ring-emerald-400/20">
            AV
          </div>
          <div>
            <div className="text-sm font-semibold tracking-wide text-white">AgriVision OS</div>
            <div className="text-xs text-slate-400">Precision Farming</div>
          </div>
        </Link>
      </div>

      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto pr-1">
        {nav.map((item) => {
          // Exact match for /dashboard; prefix match for everything else
          const active =
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors ${
                active
                  ? "bg-emerald-500/15 text-emerald-200 ring-1 ring-inset ring-emerald-400/20"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              <span className="w-4 text-center">●</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-xs text-slate-400">
        <div className="font-medium text-slate-200">v0.1 • Local</div>
        <div className="mt-1 leading-5">Monitoreo de cultivos en entorno local.</div>
      </div>
    </aside>
  );
}
