export default function CultivoDetalleLoading() {
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="av-card p-6 lg:col-span-2 space-y-4">
        <div className="h-7 w-72 animate-pulse rounded bg-gray-200" />
        <div className="h-4 w-40 animate-pulse rounded bg-gray-100" />
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="h-20 animate-pulse rounded bg-gray-100" />
          <div className="h-20 animate-pulse rounded bg-gray-100" />
        </div>
        <div className="h-24 animate-pulse rounded bg-gray-100" />
      </div>
      <div className="av-card p-6 space-y-4">
        <div className="h-6 w-40 animate-pulse rounded bg-gray-200" />
        <div className="space-y-3">
          <div className="h-10 animate-pulse rounded bg-gray-100" />
          <div className="h-10 animate-pulse rounded bg-gray-100" />
          <div className="h-10 animate-pulse rounded bg-gray-100" />
        </div>
      </div>
    </div>
  );
}
