import { NextRequest, NextResponse } from "next/server";

/**
 * Next.js 16 — Proxy (equivalente al middleware de versiones anteriores).
 * La función debe llamarse `proxy` y el archivo `proxy.ts`.
 *
 * Protege rutas basándose en la cookie 'sessionid' que Django establece
 * al hacer login. Solo verifica EXISTENCIA de la cookie; la validez real
 * se comprueba en ProtectedRoute → GET /api/auth/me/.
 *
 * NOTA: Se elimina la redirección automática de /login y /register
 * cuando hay cookie, para evitar redirecciones con cookies expiradas.
 * La verificación de sesión activa se hace en el cliente (ProtectedRoute).
 */

const PUBLIC_ROUTES = ["/login", "/register"];

const PROTECTED_PREFIXES = [
  "/dashboard",
  "/cultivos",
  "/lotes",
  "/metricas",
  "/configuracion",
  "/procesamiento",
];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const sessionId = request.cookies.get("sessionid")?.value;

  // Ruta raíz → redirige según estado de sesión
  if (pathname === "/") {
    return NextResponse.redirect(
      new URL(sessionId ? "/dashboard" : "/login", request.url),
    );
  }

  // Rutas públicas → se permite el acceso sin importar el estado de sesión
  // La redirección se hace en el cliente si la sesión es válida
  if (PUBLIC_ROUTES.some((r) => pathname === r)) {
    return NextResponse.next();
  }

  // Rutas protegidas → sin cookie de sesión, redirigir a login
  const isProtected = PROTECTED_PREFIXES.some((prefix) =>
    pathname.startsWith(prefix),
  );
  if (isProtected && !sessionId) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};