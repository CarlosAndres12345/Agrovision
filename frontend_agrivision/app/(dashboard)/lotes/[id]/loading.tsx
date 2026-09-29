import PageContainer from "../../../../components/layout/PageContainer";
import SectionCard from "../../../../components/ui/SectionCard";

export default function Loading() {
  return (
    <PageContainer title="Cargando lote">
      <SectionCard title="Cargando lote...">
        <div className="h-24 animate-pulse rounded-md bg-gray-100" />
      </SectionCard>
    </PageContainer>
  );
}