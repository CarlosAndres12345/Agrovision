"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getCurrentUser, login, setAuthUser } from "@/lib/api";

interface Props {
  redirectTo?: string;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    // Errores de red
    if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
      return "No se puede conectar al servidor. Verifica que el backend está corriendo en http://localhost:8000";
    }
    return error.message;
  }
  return "Error al iniciar sesión";
}

export default function LoginForm({ redirectTo = "/cultivos" }: Props) {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [authenticating, setAuthenticating] = useState(true);

  // Verificar si ya existe sesión activa al montar
  useEffect(() => {
    getCurrentUser()
      .then((user) => {
        setAuthUser(user);
        router.push("/dashboard");
      })
      .catch(() => {
        setAuthenticating(false);
      });
  }, [router]);

  async function onSubmit(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await login(username, password);
      setAuthUser(response.user);

      window.location.href = redirectTo;
    } catch (err: unknown) {
      setError(getErrorMessage(err));
      setLoading(false);
    }
  }

  // Mostrar loading mientras verifica sesión - centrado en pantalla
  if (authenticating) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-white to-green-50">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-emerald-600 border-r-transparent" />
          <p className="mt-3 text-sm text-slate-500">Verificando sesión...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-white to-green-50">
      <form onSubmit={onSubmit} className="w-full max-w-md bg-white av-card p-8">
        <div className="mb-6 flex flex-col items-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-md bg-green-100 font-bold text-green-700">
            AV
          </div>
          <h1 className="mt-4 text-2xl font-semibold">AgriVision OS</h1>
          <div className="text-sm text-gray-500">Precision Farming Monitoring</div>
        </div>

        <p className="mb-4 text-sm text-gray-600">
          Bienvenido — ingresa tus credenciales para continuar.
        </p>

        {error && (
          <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        <label className="mb-3 block">
          <div className="mb-1 text-sm text-gray-600">Usuario</div>
          <input
            type="text"
            required
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={loading}
            className="w-full rounded-md border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-400 disabled:opacity-50"
          />
        </label>

        <label className="mb-3 block">
          <div className="mb-1 text-sm text-gray-600">Contraseña</div>
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
            className="w-full rounded-md border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-400 disabled:opacity-50"
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          className="av-btn-primary mb-4 w-full rounded-md py-2 font-medium disabled:opacity-50"
        >
          {loading ? "Iniciando sesión..." : "Iniciar sesión"}
        </button>

        <div className="text-center text-sm text-gray-500">
          ¿No tienes cuenta?{" "}
          <Link href="/register" className="font-medium text-green-600 hover:underline">
            Regístrate aquí
          </Link>
        </div>

        <div className="mt-4 space-y-1 text-xs text-gray-400">
          <div>Al usar AgriVision aceptas los términos y la política de privacidad.</div>
          <div>Soporte: soporte@agrovision.local</div>
        </div>
      </form>
    </div>
  );
}