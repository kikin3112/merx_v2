import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { productos } from '../api/endpoints';
import type { Producto } from '../types';
import { formatCurrency } from '../utils/format';

export default function CatalogoPage() {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [isGenerating, setIsGenerating] = useState(false);

  const { data, isLoading } = useQuery<Producto[]>({
    queryKey: ['productos-catalogo'],
    queryFn: () => productos.list({ estado: true }).then((r) => r.data),
  });

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (!data) return;
    if (selected.size === data.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(data.map((p) => p.id)));
    }
  };

  const handleGenerar = async () => {
    if (selected.size === 0) return;
    setIsGenerating(true);
    try {
      const res = await productos.generarCatalogoPdf(Array.from(selected));
      const blob = new Blob([res.data as ArrayBuffer], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    } catch {
      alert('Error al generar catálogo');
    } finally {
      setIsGenerating(false);
    }
  };

  if (isLoading) {
    return <div className="cv-card p-12 text-center cv-muted">Cargando productos...</div>;
  }

  const productList = data ?? [];

  return (
    <div className="pb-24">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-brand text-xl font-medium cv-text">Catálogo</h1>
        <label className="flex items-center gap-2 text-sm cv-muted cursor-pointer">
          <input
            type="checkbox"
            checked={selected.size === productList.length && productList.length > 0}
            onChange={toggleAll}
            className="rounded"
          />
          Seleccionar todos
        </label>
      </div>

      {productList.length === 0 ? (
        <div className="cv-card p-12 text-center cv-muted">
          <p>No hay productos activos.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {productList.map((p) => (
            <div
              key={p.id}
              onClick={() => toggle(p.id)}
              className={`cv-card cursor-pointer p-4 space-y-2 transition-all ${
                selected.has(p.id) ? 'ring-2' : ''
              }`}
              style={
                selected.has(p.id)
                  ? ({ '--tw-ring-color': 'var(--cv-primary)' } as React.CSSProperties)
                  : undefined
              }
            >
              {/* Product image or placeholder */}
              <div className="w-full h-24 rounded flex items-center justify-center cv-surface">
                {p.imagen_s3_key ? (
                  <span className="text-xs cv-muted">IMG</span>
                ) : (
                  <span className="text-xs cv-muted">Sin imagen</span>
                )}
              </div>
              <p className="text-sm font-medium cv-text leading-tight line-clamp-2">{p.nombre}</p>
              <p className="text-xs cv-muted">{p.categoria}</p>
              <p className="text-sm font-semibold" style={{ color: 'var(--cv-primary)' }}>
                {formatCurrency(p.precio_venta)}
              </p>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selected.has(p.id)}
                  onChange={() => toggle(p.id)}
                  onClick={(e) => e.stopPropagation()}
                  className="rounded"
                />
                <span className="text-xs cv-muted">
                  {selected.has(p.id) ? 'Seleccionado' : 'Seleccionar'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Sticky bottom bar */}
      {selected.size > 0 && (
        <div
          className="fixed bottom-0 left-0 right-0 p-4 border-t cv-divider z-20"
          style={{ backgroundColor: 'var(--cv-surface)' }}
        >
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <span className="text-sm cv-muted">
              {selected.size} producto{selected.size !== 1 ? 's' : ''} seleccionado
              {selected.size !== 1 ? 's' : ''}
            </span>
            <button onClick={handleGenerar} disabled={isGenerating} className="cv-btn cv-btn-primary">
              {isGenerating ? 'Generando...' : `Generar PDF (${selected.size})`}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
