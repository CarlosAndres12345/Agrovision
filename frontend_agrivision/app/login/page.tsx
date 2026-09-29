import LoginForm from "../../components/auth/LoginForm";

export const metadata = {
  title: "AgriVision OS — Iniciar sesión",
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;
  const safePaths = ["/cultivos", "/lotes", "/metricas", "/configuracion", "/procesamiento", "/dashboard"];
  const redirectTo =
    next && safePaths.some((p) => next.startsWith(p)) ? next : "/cultivos";

  return <LoginForm redirectTo={redirectTo} />;
}