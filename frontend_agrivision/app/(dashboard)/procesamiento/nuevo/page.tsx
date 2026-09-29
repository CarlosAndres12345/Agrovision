import PageContainer from "../../../../components/layout/PageContainer";
import SectionCard from "../../../../components/ui/SectionCard";
import ProcesamientoTabs from "../../../../components/procesamiento/ProcesamientoTabs";

export const dynamic = "force-dynamic";

export default async function ProcesamientoNuevoPage({
  searchParams,
}: {
  searchParams: Promise<{ cultivo_id?: string; lote_id?: string }>;
}) {
  const params = await searchParams;
  const initialCultivoId = params.cultivo_id ? Number(params.cultivo_id) : null;
  const initialLoteId = params.lote_id ? Number(params.lote_id) : null;

  return (
    <PageContainer title="Procesamiento de cultivo">
      <div className="mx-auto max-w-xl">
        <SectionCard title="Seleccionar flujo de trabajo">
          <ProcesamientoTabs
            initialCultivoId={initialCultivoId}
            initialLoteId={initialLoteId}
          />
        </SectionCard>
      </div>
    </PageContainer>
  );
}