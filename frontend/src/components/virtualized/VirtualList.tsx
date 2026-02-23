/**
 * Wrapper react-window para listas virtualizadas de alto rendimiento.
 * Renderiza solo las filas visibles → 60fps con 100k+ registros.
 * Incluye error boundary y estados de carga/vacío.
 */
import React from 'react';
import { FixedSizeList, type ListChildComponentProps } from 'react-window';

// ---- Error Boundary ----

interface ErrorBoundaryState { hasError: boolean }

class VirtualListErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() { return { hasError: true }; }
  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="text-center py-8 text-gray-400 text-sm">
          Error al renderizar la lista. Recarga la página.
        </div>
      );
    }
    return this.props.children;
  }
}

// ---- VirtualList ----

interface VirtualListProps<T> {
  items: T[];
  itemHeight?: number;
  height?: number;
  renderRow: (item: T, index: number, style: React.CSSProperties) => React.ReactNode;
  emptyMessage?: string;
  isLoading?: boolean;
  loadingRows?: number;
  onLoadMore?: () => void;
  hasMore?: boolean;
}

export function VirtualList<T>({
  items,
  itemHeight = 56,
  height = 480,
  renderRow,
  emptyMessage = 'Sin registros',
  isLoading = false,
  loadingRows = 6,
  onLoadMore,
  hasMore = false,
}: VirtualListProps<T>) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: loadingRows }).map((_, i) => (
          <div key={i} className="h-14 bg-gray-200 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-lg mb-1">{emptyMessage}</p>
      </div>
    );
  }

  const Row = ({ index, style }: ListChildComponentProps) => {
    const item = items[index];
    // Load more trigger: when rendering the last item
    if (index === items.length - 1 && hasMore && onLoadMore) {
      onLoadMore();
    }
    return <>{renderRow(item, index, style)}</>;
  };

  return (
    <VirtualListErrorBoundary>
      <FixedSizeList
        height={height}
        itemCount={items.length}
        itemSize={itemHeight}
        width="100%"
        style={{ overflowX: 'hidden' }}
      >
        {Row}
      </FixedSizeList>
    </VirtualListErrorBoundary>
  );
}
