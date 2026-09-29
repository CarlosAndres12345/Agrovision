"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { logout, getAuthUser } from "@/lib/api";
import type { User } from "@/types/auth";

export default function Topbar() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [showMenu, setShowMenu] = useState(false);

  useEffect(() => {
    const authUser = getAuthUser();
    setUser(authUser);
  }, []);

  async function handleLogout() {
    try {
      await logout();
      router.push("/login");
    } catch (err) {
      console.error("Error al cerrar sesión:", err);
      // Aún así limpia localStorage y redirecciona
      router.push("/login");
    }
  }

  return (
    <header className="sticky top-0 z-20 flex h-20 w-full items-center justify-between border-b border-slate-200 bg-white/90 px-8 backdrop-blur-sm">
      <div className="flex min-w-0 items-center gap-4">
        <div className="w-[22rem] max-w-full">
          <input
            aria-label="Buscar"
            placeholder="Buscar cultivos, lotes..."
            className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-700 placeholder:text-slate-400 shadow-sm outline-none transition focus:border-emerald-500 focus:bg-white focus:ring-4 focus:ring-emerald-500/10"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="rounded-full border border-slate-200 bg-white p-2.5 text-slate-500 shadow-sm transition hover:border-slate-300 hover:bg-slate-50">
          <span>🔔</span>
        </button>
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex items-center gap-3 rounded-full border border-slate-200 bg-white px-3 py-2 shadow-sm hover:bg-slate-50 transition"
          >
            <div className="text-sm font-medium text-slate-700">{user?.username || "Usuario"}</div>
            <div className="av-avatar ring-2 ring-emerald-500/20" />
          </button>

          {showMenu && (
            <div className="absolute right-0 mt-2 w-40 rounded-md bg-white border border-slate-200 shadow-lg">
              <div className="px-4 py-2 border-b border-slate-100">
                <p className="text-sm font-medium text-slate-700">{user?.username}</p>
                <p className="text-xs text-slate-500">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                Cerrar sesión
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
