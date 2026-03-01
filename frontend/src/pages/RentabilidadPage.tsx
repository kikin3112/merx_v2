/**
 * RentabilidadPage — Comparador de rentabilidad multi-producto.
 * Muestra ranking de recetas por margen de contribución.
 */
import React from 'react';
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
    <tr className="border-b border-gray-100 hover:bg-amber-50 transition-colors">
      <td className="px-4 py-3 text-center font-bold text-gray-500">{rankEmoji}</td>
      <td className="px-4 py-3">
        <span className="font-semibold text-gray-800">{item.receta_nombre}</span>
      </td>
      <td className="px-4 py-3 text-right text-sm text-gray-600">{formatCOP(item.costo_unitario)}</td>
      <td className="px-4 py-3 text-right text-sm text-gray-600">{formatCOP(item.precio_venta)}</td>
      <td className="px-4 py-3 text-right">
        <span className={`font-semibold text-sm ${item.margen_contribucion >= 0 ? 'text-green-700' : 'text-red-600'}`}>
          {formatCOP(item.margen_contribucion)}
        </span>
      </td>
      <td className="px-4 py-3 text-center">
        <MargenIndicator margen={item.margen_porcentaje} />
      </td>
      <td className="px-4 py-3 text-right text-sm text-gray-500">
        {item.tiempo_produccion_minutos > 0 ? `${item.tiempo_produccion_minutos} min` : '—'}
      </td>
      <td className="px-4 py-3 text-right text-sm text-gray-600">
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
          <h1 className="text-2xl font-black text-gray-900">Comparador de Rentabilidad</h1>
          <p className="text-gray-500 text-sm">¿Cuál vela te conviene más hacer? Aquí lo ves de un vistazo.</p>
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
        <div className="text-center py-12 text-gray-400">
          <span className="text-4xl animate-spin block mb-2">🕯️</span>
          <p>Calculando rentabilidad de tus recetas...</p>
        </div>
      ) : error ? (
        <div className="text-center py-12 text-red-500">
          <p>No se pudo cargar la comparación. Verifica que tengas recetas activas con precio de venta configurado.</p>
        </div>
      ) : !items || items.length === 0 ? (
        <div className="text-center py-12 text-gray-400 bg-gray-50 rounded-2xl">
          <span className="text-5xl block mb-3">🕯️</span>
          <p className="font-medium">Aún no tienes recetas con precio de venta</p>
          <p className="text-sm mt-1">Agrega el precio de venta a tus productos para ver el comparador.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide">#</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Receta</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Costo</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Precio venta</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">MC unitario</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide">Margen</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Tiempo</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">MC/min</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item, idx) => (
                  <RentabilidadRow key={item.receta_id} item={item} rank={idx + 1} />
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
            <p className="text-xs text-gray-400">
              MC = Margen de Contribución (precio − costo variable). Ordenado de mayor a menor margen.
            </p>
          </div>
        </div>
      )}

      {/* Nota sobre MC/minuto */}
      {items && items.some((i) => i.mc_por_minuto != null) && (
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
          <p className="text-sm text-purple-800">
            <strong>💡 MC/minuto</strong> te dice cuánto ganas por cada minuto de trabajo. Una vela que lleva más tiempo pero tiene bajo MC puede ser menos eficiente que una más sencilla con buen margen.
          </p>
        </div>
      )}
    </div>
  );
}
