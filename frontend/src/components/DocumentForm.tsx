import { useState, useEffect, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { productos, terceros } from '../api/endpoints';
import { formatCurrency } from '../utils/format';
import type { Producto, Tercero } from '../types';

export interface LineaDetalle {
  producto_id: string;
  nombre: string;
  cantidad: number;
  precio_unitario: number;
  descuento: number;
  porcentaje_iva: number;
}

export interface DocumentFormData {
  tercero_id: string;
  fecha: string;
  fecha_vencimiento?: string;
  observaciones: string;
  descuento_global: number;
  detalles: LineaDetalle[];
}

interface Props {
  tipo: 'venta' | 'factura' | 'cotizacion';
  open: boolean;
  onClose: () => void;
  onSubmit: (data: DocumentFormData) => void;
  loading?: boolean;
}

function calcularLinea(linea: LineaDetalle) {
  const subtotal = linea.cantidad * linea.precio_unitario;
  const montoDescuento = subtotal * (linea.descuento / 100);
  const baseGravable = subtotal - montoDescuento;
  const iva = baseGravable * (linea.porcentaje_iva / 100);
  const total = baseGravable + iva;
  return { subtotal, montoDescuento, baseGravable, iva, total };
}

const titulos: Record<string, string> = {
  venta: 'Nueva Venta',
  factura: 'Nueva Factura',
  cotizacion: 'Nueva Cotizacion',
};

export default function DocumentForm({ tipo, open, onClose, onSubmit, loading }: Props) {
  const [terceroId, setTerceroId] = useState('');
  const [fecha, setFecha] = useState(() => new Date().toISOString().split('T')[0]);
  const [fechaVencimiento, setFechaVencimiento] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 30);
    return d.toISOString().split('T')[0];
  });
  const [observaciones, setObservaciones] = useState('');
  const [descuentoGlobal, setDescuentoGlobal] = useState(0);
  const [lineas, setLineas] = useState<LineaDetalle[]>([]);
  const [busquedaProducto, setBusquedaProducto] = useState('');
  const [busquedaTercero, setBusquedaTercero] = useState('');
  const [showProductSearch, setShowProductSearch] = useState(false);

  const { data: listaProductos } = useQuery<Producto[]>({
    queryKey: ['productos-form'],
    queryFn: () => productos.list({ estado: true }).then((r) => r.data),
    enabled: open,
  });

  const { data: listaTerceros } = useQuery<Tercero[]>({
    queryKey: ['terceros-form'],
    queryFn: () => terceros.list({ estado: true }).then((r) => r.data),
    enabled: open,
  });

  const tercerosFiltrados = useMemo(() => {
    if (!listaTerceros) return [];
    const base = busquedaTercero
      ? listaTerceros.filter((t) => {
          const q = busquedaTercero.toLowerCase();
          return t.nombre.toLowerCase().includes(q) || t.numero_documento.includes(q);
        })
      : listaTerceros;
    return [...base].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'));
  }, [listaTerceros, busquedaTercero]);

  const productosFiltrados = useMemo(() => {
    if (!listaProductos) return [];
    const base = busquedaProducto
      ? listaProductos.filter((p) => {
          const q = busquedaProducto.toLowerCase();
          return p.nombre.toLowerCase().includes(q) || p.codigo_interno.toLowerCase().includes(q);
        })
      : listaProductos;
    return [...base].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'));
  }, [listaProductos, busquedaProducto]);

  // Reset form when closing
  useEffect(() => {
    if (!open) {
      setTerceroId('');
      setFecha(new Date().toISOString().split('T')[0]);
      setObservaciones('');
      setDescuentoGlobal(0);
      setLineas([]);
      setBusquedaProducto('');
      setBusquedaTercero('');
      setShowProductSearch(false);
    }
  }, [open]);

  const agregarProducto = useCallback((producto: Producto) => {
    const existente = lineas.findIndex((l) => l.producto_id === producto.id);
    if (existente >= 0) {
      setLineas((prev) =>
        prev.map((l, i) => (i === existente ? { ...l, cantidad: l.cantidad + 1 } : l))
      );
    } else {
      setLineas((prev) => [
        ...prev,
        {
          producto_id: producto.id,
          nombre: producto.nombre,
          cantidad: 1,
          precio_unitario: producto.precio_venta,
          descuento: 0,
          porcentaje_iva: producto.porcentaje_iva,
        },
      ]);
    }
    setBusquedaProducto('');
    setShowProductSearch(false);
  }, [lineas]);

  const actualizarLinea = useCallback((index: number, campo: keyof LineaDetalle, valor: number) => {
    setLineas((prev) =>
      prev.map((l, i) => (i === index ? { ...l, [campo]: valor } : l))
    );
  }, []);

  const eliminarLinea = useCallback((index: number) => {
    setLineas((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const totales = useMemo(() => {
    let subtotal = 0;
    let descLineas = 0;
    let ivaLineas = 0;
    for (const linea of lineas) {
      const calc = calcularLinea(linea);
      subtotal += calc.subtotal;
      descLineas += calc.montoDescuento;
      ivaLineas += calc.iva;
    }
    const dg = descuentoGlobal || 0;
    const baseAfterLineas = subtotal - descLineas;
    const montoDescGlobal = dg > 0 ? baseAfterLineas * (dg / 100) : 0;
    const totalDescuento = descLineas + montoDescGlobal;
    const factor = dg > 0 ? (100 - dg) / 100 : 1;
    const totalIva = ivaLineas * factor;
    const total = subtotal - totalDescuento + totalIva;
    return { subtotal, descLineas, montoDescGlobal, totalDescuento, totalIva, total };
  }, [lineas, descuentoGlobal]);

  const handleSubmit = () => {
    if (!terceroId || lineas.length === 0) return;
    onSubmit({
      tercero_id: terceroId,
      fecha,
      fecha_vencimiento: tipo === 'cotizacion' ? fechaVencimiento : undefined,
      observaciones,
      descuento_global: descuentoGlobal,
      detalles: lineas,
    });
  };

  const terceroSeleccionado = listaTerceros?.find((t) => t.id === terceroId);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-start justify-center bg-black/50 md:overflow-y-auto md:py-8">
      <div className="bg-white w-full h-full md:h-auto md:rounded-xl shadow-xl md:max-w-3xl md:mx-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 md:px-6 md:py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">{titulos[tipo]}</h2>
          <button onClick={onClose} className="p-2 -mr-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors text-xl leading-none">&times;</button>
        </div>

        <div className="px-4 py-4 md:px-6 space-y-5 flex-1 overflow-y-auto md:max-h-[70vh]">
          {/* Cliente */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cliente / Tercero</label>
            {terceroSeleccionado ? (
              <div className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                <div>
                  <p className="text-sm font-medium text-gray-900">{terceroSeleccionado.nombre}</p>
                  <p className="text-xs text-gray-500">{terceroSeleccionado.tipo_documento}: {terceroSeleccionado.numero_documento}</p>
                </div>
                <button onClick={() => setTerceroId('')} className="text-xs text-red-500 hover:text-red-700">Cambiar</button>
              </div>
            ) : (
              <div>
                <input
                  type="text"
                  placeholder="Buscar por nombre o documento..."
                  value={busquedaTercero}
                  onChange={(e) => setBusquedaTercero(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                {busquedaTercero && tercerosFiltrados.length > 0 && (
                  <div className="mt-1 border border-gray-200 rounded-lg max-h-40 overflow-y-auto bg-white shadow-md">
                    {tercerosFiltrados.slice(0, 10).map((t) => (
                      <button
                        key={t.id}
                        onClick={() => { setTerceroId(t.id); setBusquedaTercero(''); }}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-50 last:border-0"
                      >
                        <span className="font-medium text-gray-900">{t.nombre}</span>
                        <span className="text-gray-500 ml-2 text-xs">{t.numero_documento}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Fechas */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Fecha</label>
              <input
                type="date"
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            {tipo === 'cotizacion' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Vencimiento</label>
                <input
                  type="date"
                  value={fechaVencimiento}
                  onChange={(e) => setFechaVencimiento(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            )}
          </div>

          {/* Productos */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">Productos</label>
              <button
                onClick={() => setShowProductSearch(true)}
                className="text-xs font-medium text-primary-600 hover:text-primary-700"
              >
                + Agregar producto
              </button>
            </div>

            {showProductSearch && (
              <div className="mb-3">
                <input
                  type="text"
                  placeholder="Buscar producto por nombre o codigo..."
                  value={busquedaProducto}
                  onChange={(e) => setBusquedaProducto(e.target.value)}
                  autoFocus
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                {productosFiltrados.length > 0 && (
                  <div className="mt-1 border border-gray-200 rounded-lg max-h-48 overflow-y-auto bg-white shadow-md">
                    {productosFiltrados.slice(0, 15).map((p) => (
                      <button
                        key={p.id}
                        onClick={() => agregarProducto(p)}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-50 last:border-0 flex items-center justify-between"
                      >
                        <div>
                          <span className="font-medium text-gray-900">{p.nombre}</span>
                          <span className="text-gray-500 ml-2 text-xs">{p.codigo_interno}</span>
                        </div>
                        <span className="text-gray-600 text-xs">{formatCurrency(p.precio_venta)}</span>
                      </button>
                    ))}
                  </div>
                )}
                <button
                  onClick={() => { setShowProductSearch(false); setBusquedaProducto(''); }}
                  className="mt-1 text-xs text-gray-500 hover:text-gray-700"
                >
                  Cancelar
                </button>
              </div>
            )}

            {/* Line items */}
            {lineas.length > 0 ? (
              <>
                {/* Desktop table */}
                <div className="hidden md:block border border-gray-200 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-b border-gray-100">
                        <th className="text-left px-3 py-2 font-medium text-gray-500">Producto</th>
                        <th className="text-center px-2 py-2 font-medium text-gray-500 w-20">Cant.</th>
                        <th className="text-right px-2 py-2 font-medium text-gray-500 w-28">Precio</th>
                        <th className="text-right px-2 py-2 font-medium text-gray-500 w-24">Desc. %</th>
                        <th className="text-right px-3 py-2 font-medium text-gray-500 w-28">Total</th>
                        <th className="w-8"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {lineas.map((linea, i) => {
                        const calc = calcularLinea(linea);
                        return (
                          <tr key={i} className="border-b border-gray-50">
                            <td className="px-3 py-2">
                              <p className="text-gray-900 font-medium text-xs">{linea.nombre}</p>
                              <p className="text-gray-400 text-xs">IVA: {linea.porcentaje_iva}%</p>
                            </td>
                            <td className="px-2 py-2">
                              <input
                                type="number"
                                min={1}
                                value={linea.cantidad}
                                onChange={(e) => actualizarLinea(i, 'cantidad', Math.max(1, Number(e.target.value)))}
                                className="w-full text-center rounded border border-gray-200 px-1 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
                              />
                            </td>
                            <td className="px-2 py-2">
                              <input
                                type="number"
                                min={0}
                                step={100}
                                value={linea.precio_unitario}
                                onChange={(e) => actualizarLinea(i, 'precio_unitario', Math.max(0, Number(e.target.value)))}
                                className="w-full text-right rounded border border-gray-200 px-1 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
                              />
                            </td>
                            <td className="px-2 py-2">
                              <input
                                type="number"
                                min={0}
                                max={100}
                                step={1}
                                value={linea.descuento}
                                onChange={(e) => actualizarLinea(i, 'descuento', Math.min(100, Math.max(0, Number(e.target.value))))}
                                className="w-full text-right rounded border border-gray-200 px-1 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
                              />
                            </td>
                            <td className="px-3 py-2 text-right font-medium text-gray-900 text-xs">
                              {formatCurrency(calc.total)}
                            </td>
                            <td className="px-1 py-2">
                              <button
                                onClick={() => eliminarLinea(i)}
                                className="text-red-400 hover:text-red-600 text-lg leading-none"
                              >
                                &times;
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Mobile line cards */}
                <div className="md:hidden space-y-2">
                  {lineas.map((linea, i) => {
                    const calc = calcularLinea(linea);
                    return (
                      <div key={i} className="border border-gray-200 rounded-lg p-3 space-y-2">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="text-sm font-medium text-gray-900">{linea.nombre}</p>
                            <p className="text-xs text-gray-400">IVA: {linea.porcentaje_iva}%</p>
                          </div>
                          <button
                            onClick={() => eliminarLinea(i)}
                            className="p-1 text-red-400 hover:text-red-600"
                          >
                            &times;
                          </button>
                        </div>
                        <div className="grid grid-cols-3 gap-2">
                          <div>
                            <label className="text-[10px] text-gray-400">Cant.</label>
                            <input
                              type="number"
                              inputMode="numeric"
                              min={1}
                              value={linea.cantidad}
                              onChange={(e) => actualizarLinea(i, 'cantidad', Math.max(1, Number(e.target.value)))}
                              className="w-full text-center rounded border border-gray-200 px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
                            />
                          </div>
                          <div>
                            <label className="text-[10px] text-gray-400">Precio</label>
                            <input
                              type="number"
                              inputMode="decimal"
                              min={0}
                              step={100}
                              value={linea.precio_unitario}
                              onChange={(e) => actualizarLinea(i, 'precio_unitario', Math.max(0, Number(e.target.value)))}
                              className="w-full text-right rounded border border-gray-200 px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
                            />
                          </div>
                          <div>
                            <label className="text-[10px] text-gray-400">Desc. %</label>
                            <input
                              type="number"
                              inputMode="numeric"
                              min={0}
                              max={100}
                              value={linea.descuento}
                              onChange={(e) => actualizarLinea(i, 'descuento', Math.min(100, Math.max(0, Number(e.target.value))))}
                              className="w-full text-right rounded border border-gray-200 px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
                            />
                          </div>
                        </div>
                        <div className="text-right text-sm font-semibold text-gray-900">
                          {formatCurrency(calc.total)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            ) : (
              <div className="border border-dashed border-gray-300 rounded-lg py-8 text-center text-sm text-gray-400">
                Agrega productos para comenzar
              </div>
            )}
          </div>

          {/* Global Discount + Totals */}
          {lineas.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4 space-y-1.5">
              <div className="flex justify-between text-sm text-gray-600">
                <span>Subtotal</span>
                <span>{formatCurrency(totales.subtotal)}</span>
              </div>
              {totales.descLineas > 0 && (
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Desc. lineas</span>
                  <span className="text-red-600">-{formatCurrency(totales.descLineas)}</span>
                </div>
              )}
              {/* Global discount input */}
              <div className="flex items-center justify-between text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <span>Desc. global</span>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    step={1}
                    value={descuentoGlobal}
                    onChange={(e) => setDescuentoGlobal(Math.min(100, Math.max(0, Number(e.target.value))))}
                    className="w-16 text-right rounded border border-gray-200 px-1.5 py-0.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
                  />
                  <span className="text-xs text-gray-400">%</span>
                </div>
                {totales.montoDescGlobal > 0 && (
                  <span className="text-red-600">-{formatCurrency(totales.montoDescGlobal)}</span>
                )}
              </div>
              <div className="flex justify-between text-sm text-gray-600">
                <span>IVA</span>
                <span>{formatCurrency(totales.totalIva)}</span>
              </div>
              <div className="flex justify-between text-base font-bold text-gray-900 pt-1.5 border-t border-gray-200">
                <span>Total</span>
                <span>{formatCurrency(totales.total)}</span>
              </div>
            </div>
          )}

          {/* Observaciones */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Observaciones</label>
            <textarea
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
              rows={2}
              placeholder="Notas u observaciones (opcional)"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-4 py-3 md:px-6 md:py-4 border-t border-gray-100 bg-white">
          <button
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={!terceroId || lineas.length === 0 || loading}
            className="rounded-lg bg-primary-500 px-5 py-2 text-sm font-semibold text-white hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Guardando...' : 'Crear'}
          </button>
        </div>
      </div>
    </div>
  );
}
