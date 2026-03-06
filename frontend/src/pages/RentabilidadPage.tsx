/**
 * RentabilidadPage — Comparador de rentabilidad multi-producto.
 * Muestra ranking de recetas por margen de contribución.
 */

import { useComparadorRentabilidad } from '../hooks/useAnalisisPrecios';
import { SociaInsight } from '../socia/components/SociaInsight';
import { MargenIndicator } from '../components/recetas/MargenIndicator';
import type { RentabilidadItem } from '../types';

function formatCOP(v: number) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(v);
}

function RentabilidadRow({ item, rank }: { item: RentabilidadItem; rank: number }) {
  const rankEmoji = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : `#${rank}`;

  return (
    <tr>
      <td className="text-center font-bold cv-muted">{rankEmoji}</td>
      <td><span className="font-semibold cv-text">{item.receta_nombre}</span></td>
      <td className="text-right text-sm cv-muted">{formatCOP(item.costo_unitario)}</td>
      <td className="text-right text-sm cv-muted">{formatCOP(item.precio_venta)}</td>
      <td className="text-right">
        <span className={`font-semibold text-sm ${item.margen_contribucion >= 0 ? 'cv-positive' : 'cv-negative'}`}>
          {formatCOP(item.margen_contribucion)}
        </span>
      </td>
      <td className="text-center"><MargenIndicator margen={item.margen_porcentaje} /></td>
      <td className="text-right text-sm cv-muted">
        {item.tiempo_produccion_minutos > 0 ? `${item.tiempo_produccion_minutos} min` : '—'}
      </td>
      <td className="text-right text-sm cv-muted">
        {item.mc_por_minuto != null ? formatCOP(item.mc_por_minuto) + '/min' : '—'}
      </td>
    </tr>
  );
}

export function RentabilidadPage() {
  const { data: items, isLoading, error } = useComparadorRentabilidad();

  const mejorProducto = items?.[0];
  const productoMejorable = items?.find((i) => i.margen_porcentaje < 30);

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <span className="text-3xl">📊</span>
        <div>
          <h1 className="font-brand text-2xl font-medium cv-text">Comparador de Rentabilidad</h1>
          <p className="cv-muted text-sm">¿Cuál vela te conviene más hacer? Aquí lo ves de un vistazo.</p>
        </div>
      </div>

      {/* Insights de Socia */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {mejorProducto && (
          <SociaInsight
            mensaje={`Tu "${mejorProducto.receta_nombre}" es la más rentable de tu catálogo. ¡Ponle amor a esa! 💛`}
            tipo="success"
          />
        )}
        {productoMejorable && (
          <SociaInsight
            mensaje={`La "${productoMejorable.receta_nombre}" puede mejorar. Con un ajuste de precio podrías ganar mucho más 📈`}
            tipo="warning"
          />
        )}
      </div>

      {/* Tabla */}
      {isLoading ? (
        <div className="text-center py-12 cv-muted">
          <span className="text-4xl animate-spin block mb-2">🕯️</span>
          <p>Calculando rentabilidad de tus recetas...</p>
        </div>
      ) : error ? (
        <div className="text-center py-12 cv-negative">
          <p>No se pudo cargar la comparación. Verifica que tengas recetas activas con precio de venta configurado.</p>
        </div>
      ) : !items || items.length === 0 ? (
        <div className="text-center py-12 cv-muted cv-elevated rounded-2xl">
          <span className="text-5xl block mb-3">🕯️</span>
          <p className="font-medium">Aún no tienes recetas con precio de venta</p>
          <p className="text-sm mt-1">Agrega el precio de venta a tus productos para ver el comparador.</p>
        </div>
      ) : (
        <div className="cv-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="cv-table-header">
                <tr>
                  <th className="text-center">#</th>
                  <th className="text-left">Receta</th>
                  <th className="text-right">Costo</th>
                  <th className="text-right">Precio venta</th>
                  <th className="text-right">MC unitario</th>
                  <th className="text-center">Margen</th>
                  <th className="text-right">Tiempo</th>
                  <th className="text-right">MC/min</th>
                </tr>
              </thead>
              <tbody className="cv-table-body">
                {items.map((item, idx) => (
                  <RentabilidadRow key={item.receta_id} item={item} rank={idx + 1} />
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 cv-elevated border-t cv-divider">
            <p className="text-xs cv-muted">
              MC = Margen de Contribución (precio − costo variable). Ordenado de mayor a menor margen.
            </p>
          </div>
        </div>
      )}

      {/* Nota sobre MC/minuto */}
      {items && items.some((i) => i.mc_por_minuto != null) && (
        <div className="bg-[var(--cv-primary-dim)] border border-[var(--cv-primary)] rounded-xl p-4">
          <p className="text-sm cv-text">
            <strong>💡 MC/minuto</strong> te dice cuánto ganas por cada minuto de trabajo. Una vela que lleva más tiempo pero tiene bajo MC puede ser menos eficiente que una más sencilla con buen margen.
          </p>
        </div>
      )}
    </div>
  );
}
