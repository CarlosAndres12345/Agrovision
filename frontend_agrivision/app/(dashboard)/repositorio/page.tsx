import PageContainer from "../../../components/layout/PageContainer";
import SectionCard from "../../../components/ui/SectionCard";
import RepositoryModule from "../../../components/repository/RepositoryModule";

export default function RepositorioPage() {
  return (
    <PageContainer title="Repositorio">
      <SectionCard title="Imágenes en Cloudinary">
        <RepositoryModule />
      </SectionCard>
    </PageContainer>
  );
}
