/** Skeleton screens para estados de carga. */

function SkeletonBox({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse cv-elevated rounded ${className}`} />;
}

export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="cv-card overflow-hidden">
      <div className="cv-card-elevated border-b cv-divider px-4 py-3">
        <SkeletonBox className="h-4 w-48" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3 border-b cv-divider last:border-0">
          <SkeletonBox className="h-4 w-24" />
          <SkeletonBox className="h-4 flex-1" />
          <SkeletonBox className="h-4 w-20" />
          <SkeletonBox className="h-4 w-16" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonCard({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="cv-card p-4 space-y-2">
          <SkeletonBox className="h-5 w-40" />
          <SkeletonBox className="h-4 w-24" />
          <div className="flex gap-4 mt-2">
            <SkeletonBox className="h-4 w-20" />
            <SkeletonBox className="h-4 w-20" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function SkeletonKPI() {
  return (
    <div className="cv-card p-5 space-y-2">
      <SkeletonBox className="h-4 w-32" />
      <SkeletonBox className="h-8 w-24" />
      <SkeletonBox className="h-3 w-20" />
    </div>
  );
}

export default SkeletonBox;
