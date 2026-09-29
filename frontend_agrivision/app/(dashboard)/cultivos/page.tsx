import PageContainer from "../../../components/layout/PageContainer";
import SectionCard from "../../../components/ui/SectionCard";
import { getCultivosWithCookie } from "../../../lib/api";
import CultivosTable from "../../../components/cultivos/CultivosTable";
import Link from "next/link";
import { getCookieHeader } from "../../../lib/server-cookies";

export const dynamic = "force-dynamic";

export default async function CultivosPage() {
  const cookieHeader = await getCookieHeader();
  const cultivos = await getCultivosWithCookie(cookieHeader);

  return (
    <PageContainer title="Cultivos">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Lista de cultivos reales</h2>
          <p className="text-sm text-gray-500">Gestiona cultivos, edición y eliminación desde la demo.</p>
        </div>
        <Link
          href="/cultivos/nuevo"
          className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
        >
          Nuevo cultivo
        </Link>
      </div>
      <SectionCard>
        <CultivosTable cultivos={cultivos} />
      </SectionCard>
    </PageContainer>
  );
}
