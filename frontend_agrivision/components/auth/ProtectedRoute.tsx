"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser, setAuthUser, clearAuthData } from "@/lib/api";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * Verifica la sesión con el backend (GET /api/auth/me/) antes de renderizar.
 * Si la cookie 'sessionid' es válida → renderiza children.
 * Si la sesión expiró o no existe → redirige a /login.
 *
 * La fuente de verdad es Django, no localStorage.
 */
export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const [verified, setVerified] = useState(false);

  useEffect(() => {
    getCurrentUser()
      .then((user) => {
        setAuthUser(user);  // Actualiza caché de UI con datos frescos del backend
        setVerified(true);
      })
      .catch(() => {
        clearAuthData();
        router.push("/login");
      });
  }, [router]);

  if (!verified) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-emerald-600 border-r-transparent" />
          <p className="mt-3 text-sm text-slate-500">Verificando sesión...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
