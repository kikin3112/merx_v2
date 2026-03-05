import { useState, useEffect, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productos, terceros, ventas, facturas, cotizaciones } from '../api/endpoints';
import { formatCurrency, formatDate, statusColor } from '../utils/format';
import type { Producto, Tercero, Venta, Cotizacion } from '../types';

type DocType = 'venta' | 'factura' | 'cotizacion';

interface Props {
  tipo: DocType;
  doc: Venta | Cotizacion | null;
  open: boolean;
  onClose: () => void;
  onUpdated: () => void;
}

interface EditLinea {
  producto_id: string;
  nombre: string;
  categoria?: string;
  cantidad: number;
  precio_unitario: number;
  descuento: number;
  porcentaje_iva: number;
}

function calcLinea(l: EditLinea) {
  const sub = l.cantidad * l.precio_unitario;
  const desc = sub * (l.descuento / 100);
  const base = sub - desc;
  const iva = base * (l.porcentaje_iva / 100);
  return { sub, desc, base, iva, total: base + iva };
}

export default function DocumentDetail({ tipo, doc, open, onClose, onUpdated }: Props) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [lineas, setLineas] = useState<EditLinea[]>([]);
  const [descuentoGlobal, setDescuentoGlobal] = useState(0);
  const [observaciones, setObservaciones] = useState('');
  const [busquedaProducto, setBusquedaProducto] = useState('');
  const [showProductSearch, setShowProductSearch] = useState(false);

  const { data: productosData } = useQuery<Producto[]>({
    queryKey: ['productos-detail'],
    queryFn: () => productos.list({ estado: true, limit: 500 }).then((r) => r.data),
    enabled: open,
  });

  const { data: tercerosData } = useQuery<Tercero[]>({
    queryKey: ['terceros-detail'],
    queryFn: () => terceros.list().then((r) => r.data),
    enabled: open,
  });

  const productMap = useMemo(() => {
    const m = new Map<string, Producto>();
    productosData?.forEach((p) => m.set(p.id, p));
    return m;
  }, [productosData]);

  const terceroNombre = useMemo(() => {
    if (!doc || !tercerosData) return '';
    const t = tercerosData.find((t) => t.id === doc.tercero_id);
    return t ? `${t.nombre} (${t.tipo_documento}: ${t.numero_documento})` : doc.tercero_id;
  }, [doc, tercerosData]);

  // Init edit state from doc
  useEffect(() => {
    if (!doc || !open) return;
    const detalles = doc.detalles || [];
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLineas(
      detalles.map((d) => ({
        producto_id: d.producto_id,
        nombre: d.nombre || productMap.get(d.producto_id)?.nombre || d.producto_id,
        categoria: d.categoria || productMap.get(d.producto_id)?.categoria,
        cantidad: d.cantidad,
        precio_unitario: d.precio_unitario,
        descuento: d.descuento,
        porcentaje_iva: d.porcentaje_iva,
      }))
    );
    setDescuentoGlobal(doc.descuento_global || 0);
    setObservaciones(doc.observaciones || '');
    setEditing(false);
  }, [doc, open, productMap]);

  const productosFiltrados = useMemo(() => {
    if (!productosData || !busquedaProducto) return [];
    const q = busquedaProducto.toLowerCase();
    return productosData.filter(
      (p) => p.nombre.toLowerCase().includes(q) || p.codigo_interno.toLowerCase().includes(q)
    );
  }, [productosData, busquedaProducto]);

  const agregarProducto = useCallback(
    (producto: Producto) => {
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
    },
    [lineas]
  );

  const totales = useMemo(() => {
    let subtotal = 0;
    let descLineas = 0;
    let ivaLineas = 0;
    for (const l of lineas) {
      const c = calcLinea(l);
      subtotal += c.sub;
      descLineas += c.desc;
      ivaLineas += c.iva;
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

  // Mutations for actions
  const saveMutation = useMutation({
    mutationFn: () => {
      if (!doc) return Promise.reject();
      const payload = {
        tercero_id: doc.tercero_id,
        fecha_venta: 'fecha_venta' in doc ? doc.fecha_venta : (doc as Cotizacion).fecha_cotizacion,
        observaciones: observaciones || null,
        descuento_global: descuentoGlobal || 0,
        detalles: lineas.map((l) => ({
          producto_id: l.producto_id,
          cantidad: l.cantidad,
          precio_unitario: l.precio_unitario,
          descuento: l.descuento,
          porcentaje_iva: l.porcentaje_iva,
        })),
      };
      return ventas.update(doc.id, payload);
    },
    onSuccess: () => {
      setEditing(false);
      onUpdated();
    },
  });

  const confirmarMut = useMutation({
    mutationFn: (id: string) => ventas.confirmar(id),
    onSuccess: onUpdated,
  });

  const emitirMut = useMutation({
    mutationFn: (id: string) => facturas.emitir(id),
    onSuccess: onUpdated,
  });

  const facturarMut = useMutation({
    mutationFn: (id: string) => ventas.facturar(id),
    onSuccess: () => {
      onUpdated();
      queryClient.invalidateQueries({ queryKey: ['facturas'] });
    },
  });

  const anularMut = useMutation({
    mutationFn: (id: string) => {
      if (tipo === 'factura') return facturas.anular(id, 'Anulada desde detalle');
      return ventas.anular(id, 'Anulada desde detalle');
    },
    onSuccess: onUpdated,
  });

  const convertirMut = useMutation({
    mutationFn: (id: string) => cotizaciones.convertir(id),
    onSuccess: () => {
      onUpdated();
      queryClient.invalidateQueries({ queryKey: ['facturas'] });
    },
  });

  const descargarPdf = (id: string, numero: string) => {
    const fn = tipo === 'cotizacion' ? cotizaciones.descargarPdf : facturas.descargarPdf;
    fn(id).then((res) => {
      const blob = new Blob([res.data as BlobPart], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${tipo}-${numero}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    });
  };

  if (!open || !doc) return null;

  const isVenta = 'numero_venta' in doc;
  const isCotizacion = 'numero_cotizacion' in doc;
  const numero = isVenta ? doc.numero_venta : (doc as Cotizacion).numero_cotizacion;
  const fecha = isVenta ? doc.fecha_venta : (doc as Cotizacion).fecha_cotizacion;
  const isPendiente = doc.estado === 'PENDIENTE';
  const canEdit = isPendiente && (tipo === 'venta' || tipo === 'factura');

  const inlineInputClass = 'w-full rounded border border-[var(--cv-divider)] px-1 py-0.5 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--cv-primary)] bg-[var(--cv-bg)] text-[var(--cv-text)]';

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-start justify-center bg-black/50 md:overflow-y-auto md:py-8">
      <div className="cv-card w-full h-full md:h-auto md:rounded-xl shadow-xl md:max-w-3xl md:mx-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 md:px-6 md:py-4 border-b border-[var(--cv-divider)]">
          <div>
            <h2 className="text-lg font-semibold cv-text">
              {tipo === 'cotizacion' ? 'Cotizacion' : tipo === 'factura' ? 'Factura' : 'Venta'}{' '}
              <span className="font-mono">{numero}</span>
            </h2>
            <div className="flex items-center gap-3 mt-1">
              <span className={`cv-badge ${statusColor(doc.estado)}`}>
                {doc.estado}
              </span>
              <span className="text-sm cv-muted">{formatDate(fecha)}</span>
            </div>
          </div>
          <button onClick={onClose} className="cv-icon-btn text-xl leading-none">
            &times;
          </button>
        </div>

        <div className="px-4 py-4 md:px-6 space-y-4 flex-1 overflow-y-auto md:max-h-[70vh]">
          {/* Client info */}
          <div className="cv-card p-3">
            <p className="text-xs cv-muted mb-0.5">Cliente</p>
            <p className="text-sm font-medium cv-text">{terceroNombre}</p>
          </div>

          {/* Detail lines */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium cv-text">Detalle</h3>
              {editing && (
                <button
                  onClick={() => setShowProductSearch(true)}
                  className="text-xs font-medium"
                  style={{ color: 'var(--cv-primary)' }}
                >
                  + Agregar producto
                </button>
              )}
            </div>

            {editing && showProductSearch && (
              <div className="mb-3">
                <input
                  type="text"
                  placeholder="Buscar producto..."
                  value={busquedaProducto}
                  onChange={(e) => setBusquedaProducto(e.target.value)}
                  autoFocus
                  className="cv-input"
                />
                {productosFiltrados.length > 0 && (
                  <div className="mt-1 cv-card max-h-40 overflow-y-auto shadow-md">
                    {productosFiltrados.slice(0, 10).map((p) => (
                      <button
                        key={p.id}
                        onClick={() => agregarProducto(p)}
                        className="cv-nav-item w-full text-left px-3 py-2 text-sm border-b border-[var(--cv-divider)] last:border-0 flex items-center justify-between"
                      >
                        <span className="font-medium cv-text">{p.nombre}</span>
                        <span className="cv-muted text-xs">{formatCurrency(p.precio_venta)}</span>
                      </button>
                    ))}
                  </div>
                )}
                <button
                  onClick={() => {
                    setShowProductSearch(false);
                    setBusquedaProducto('');
                  }}
                  className="mt-1 text-xs cv-muted hover:text-[var(--cv-text)]"
                >
                  Cancelar
                </button>
              </div>
            )}

            <>
              {/* Desktop table */}
              <div className="hidden md:block border border-[var(--cv-divider)] rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--cv-divider)]" style={{ background: 'var(--cv-surface)' }}>
                      <th className="text-left px-3 py-2 font-medium cv-muted">Producto</th>
                      <th className="text-left px-2 py-2 font-medium cv-muted w-28">Categoría</th>
                      <th className="text-center px-2 py-2 font-medium cv-muted w-20">Cant.</th>
                      <th className="text-right px-2 py-2 font-medium cv-muted w-24">Precio</th>
                      <th className="text-right px-2 py-2 font-medium cv-muted w-20">Desc.%</th>
                      <th className="text-right px-2 py-2 font-medium cv-muted w-16">IVA%</th>
                      <th className="text-right px-3 py-2 font-medium cv-muted w-28">Total</th>
                      {editing && <th className="w-8"></th>}
                    </tr>
                  </thead>
                  <tbody>
                    {lineas.map((l, i) => {
                      const c = calcLinea(l);
                      return (
                        <tr key={i} className="border-b border-[var(--cv-divider)]">
                          <td className="px-3 py-2 text-xs font-medium cv-text">{l.nombre}</td>
                          <td className="px-2 py-2 text-xs cv-muted">{l.categoria ?? '-'}</td>
                          <td className="px-2 py-2 text-center">
                            {editing ? (
                              <input
                                type="number"
                                min={1}
                                value={l.cantidad}
                                onChange={(e) =>
                                  setLineas((prev) =>
                                    prev.map((ll, j) =>
                                      j === i ? { ...ll, cantidad: Math.max(1, Number(e.target.value)) } : ll
                                    )
                                  )
                                }
                                className={`text-center ${inlineInputClass}`}
                              />
                            ) : (
                              <span className="text-sm cv-text">{l.cantidad}</span>
                            )}
                          </td>
                          <td className="px-2 py-2 text-right">
                            {editing ? (
                              <input
                                type="number"
                                min={0}
                                step={100}
                                value={l.precio_unitario}
                                onChange={(e) =>
                                  setLineas((prev) =>
                                    prev.map((ll, j) =>
                                      j === i ? { ...ll, precio_unitario: Math.max(0, Number(e.target.value)) } : ll
                                    )
                                  )
                                }
                                className={`text-right ${inlineInputClass}`}
                              />
                            ) : (
                              <span className="text-sm cv-text">{formatCurrency(l.precio_unitario)}</span>
                            )}
                          </td>
                          <td className="px-2 py-2 text-right">
                            {editing ? (
                              <input
                                type="number"
                                min={0}
                                max={100}
                                value={l.descuento}
                                onChange={(e) =>
                                  setLineas((prev) =>
                                    prev.map((ll, j) =>
                                      j === i
                                        ? { ...ll, descuento: Math.min(100, Math.max(0, Number(e.target.value))) }
                                        : ll
                                    )
                                  )
                                }
                                className={`text-right ${inlineInputClass}`}
                              />
                            ) : (
                              <span className="text-sm cv-text">{l.descuento}%</span>
                            )}
                          </td>
                          <td className="px-2 py-2 text-right text-sm cv-muted">{l.porcentaje_iva}%</td>
                          <td className="px-3 py-2 text-right font-medium cv-text text-xs">
                            {formatCurrency(c.total)}
                          </td>
                          {editing && (
                            <td className="px-1 py-2">
                              <button
                                onClick={() => setLineas((prev) => prev.filter((_, j) => j !== i))}
                                className="text-red-400 hover:text-red-600 text-lg leading-none"
                              >
                                &times;
                              </button>
                            </td>
                          )}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Mobile line cards */}
              <div className="md:hidden space-y-2">
                {lineas.map((l, i) => {
                  const c = calcLinea(l);
                  return (
                    <div key={i} className="cv-card p-3 space-y-2">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-sm font-medium cv-text">{l.nombre}</p>
                          {l.categoria && <p className="text-xs cv-muted">{l.categoria}</p>}
                        </div>
                        {editing && (
                          <button
                            onClick={() => setLineas((prev) => prev.filter((_, j) => j !== i))}
                            className="p-1 text-red-400 hover:text-red-600"
                          >
                            &times;
                          </button>
                        )}
                      </div>
                      {editing ? (
                        <div className="grid grid-cols-3 gap-2">
                          <div>
                            <label className="text-[10px] cv-muted">Cant.</label>
                            <input
                              type="number"
                              inputMode="numeric"
                              min={1}
                              value={l.cantidad}
                              onChange={(e) =>
                                setLineas((prev) =>
                                  prev.map((ll, j) =>
                                    j === i ? { ...ll, cantidad: Math.max(1, Number(e.target.value)) } : ll
                                  )
                                )
                              }
                              className={`text-center ${inlineInputClass}`}
                            />
                          </div>
                          <div>
                            <label className="text-[10px] cv-muted">Precio</label>
                            <input
                              type="number"
                              inputMode="decimal"
                              min={0}
                              step={100}
                              value={l.precio_unitario}
                              onChange={(e) =>
                                setLineas((prev) =>
                                  prev.map((ll, j) =>
                                    j === i ? { ...ll, precio_unitario: Math.max(0, Number(e.target.value)) } : ll
                                  )
                                )
                              }
                              className={`text-right ${inlineInputClass}`}
                            />
                          </div>
                          <div>
                            <label className="text-[10px] cv-muted">Desc.%</label>
                            <input
                              type="number"
                              inputMode="numeric"
                              min={0}
                              max={100}
                              value={l.descuento}
                              onChange={(e) =>
                                setLineas((prev) =>
                                  prev.map((ll, j) =>
                                    j === i
                                      ? { ...ll, descuento: Math.min(100, Math.max(0, Number(e.target.value))) }
                                      : ll
                                  )
                                )
                              }
                              className={`text-right ${inlineInputClass}`}
                            />
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-between text-sm cv-muted">
                          <span>{l.cantidad} x {formatCurrency(l.precio_unitario)}</span>
                          <span>IVA {l.porcentaje_iva}% {l.descuento > 0 && `/ Desc ${l.descuento}%`}</span>
                        </div>
                      )}
                      <div className="text-right text-sm font-semibold cv-text">
                        {formatCurrency(c.total)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          </div>

          {/* Totals */}
          <div className="cv-card p-4 space-y-1.5">
            <div className="flex justify-between text-sm cv-muted">
              <span>Subtotal</span>
              <span>{formatCurrency(totales.subtotal)}</span>
            </div>
            {totales.descLineas > 0 && (
              <div className="flex justify-between text-sm cv-muted">
                <span>Desc. lineas</span>
                <span className="text-red-500">-{formatCurrency(totales.descLineas)}</span>
              </div>
            )}
            {editing ? (
              <div className="flex items-center justify-between text-sm cv-muted">
                <div className="flex items-center gap-2">
                  <span>Desc. global</span>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    step={1}
                    value={descuentoGlobal}
                    onChange={(e) =>
                      setDescuentoGlobal(Math.min(100, Math.max(0, Number(e.target.value))))
                    }
                    className="w-16 text-right rounded border border-[var(--cv-divider)] px-1.5 py-0.5 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--cv-primary)] bg-[var(--cv-bg)] text-[var(--cv-text)]"
                  />
                  <span className="text-xs cv-muted">%</span>
                </div>
                {totales.montoDescGlobal > 0 && (
                  <span className="text-red-500">-{formatCurrency(totales.montoDescGlobal)}</span>
                )}
              </div>
            ) : (
              descuentoGlobal > 0 && (
                <div className="flex justify-between text-sm cv-muted">
                  <span>Desc. global ({descuentoGlobal}%)</span>
                  <span className="text-red-500">-{formatCurrency(totales.montoDescGlobal)}</span>
                </div>
              )
            )}
            <div className="flex justify-between text-sm cv-muted">
              <span>IVA</span>
              <span>{formatCurrency(totales.totalIva)}</span>
            </div>
            <div className="flex justify-between text-base font-bold cv-text pt-1.5 border-t border-[var(--cv-divider)]">
              <span>Total</span>
              <span>{formatCurrency(totales.total)}</span>
            </div>
          </div>

          {/* Observaciones */}
          {editing ? (
            <div>
              <label className="block text-sm font-medium cv-text mb-1">Observaciones</label>
              <textarea
                value={observaciones}
                onChange={(e) => setObservaciones(e.target.value)}
                rows={2}
                className="cv-input resize-none"
              />
            </div>
          ) : (
            doc.observaciones && (
              <div className="cv-card p-3">
                <p className="text-xs cv-muted mb-0.5">Observaciones</p>
                <p className="text-sm cv-text">{doc.observaciones}</p>
              </div>
            )
          )}
        </div>

        {/* Footer - Actions */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 px-4 py-3 md:px-6 md:py-4 border-t border-[var(--cv-divider)]">
          <div className="flex flex-wrap gap-2">
            {/* Edit / Save */}
            {canEdit && !editing && (
              <button
                onClick={() => setEditing(true)}
                className="cv-btn cv-btn-ghost"
                style={{ color: 'var(--cv-primary)' }}
              >
                Editar
              </button>
            )}
            {editing && (
              <>
                <button
                  onClick={() => saveMutation.mutate()}
                  disabled={saveMutation.isPending || lineas.length === 0}
                  className="cv-btn cv-btn-primary"
                >
                  {saveMutation.isPending ? 'Guardando...' : 'Guardar'}
                </button>
                <button
                  onClick={() => {
                    setEditing(false);
                    if (doc) {
                      setLineas(
                        (doc.detalles || []).map((d) => ({
                          producto_id: d.producto_id,
                          nombre: productMap.get(d.producto_id)?.nombre || d.producto_id,
                          cantidad: d.cantidad,
                          precio_unitario: d.precio_unitario,
                          descuento: d.descuento,
                          porcentaje_iva: d.porcentaje_iva,
                        }))
                      );
                      setDescuentoGlobal(doc.descuento_global || 0);
                      setObservaciones(doc.observaciones || '');
                    }
                  }}
                  className="cv-btn cv-btn-ghost"
                >
                  Cancelar
                </button>
              </>
            )}

            {/* Status actions */}
            {!editing && (
              <>
                {tipo === 'venta' && doc.estado === 'PENDIENTE' && (
                  <button
                    onClick={() => confirmarMut.mutate(doc.id)}
                    disabled={confirmarMut.isPending}
                    className="cv-btn cv-btn-ghost"
                    style={{ color: 'var(--cv-primary)' }}
                  >
                    Confirmar
                  </button>
                )}
                {tipo === 'venta' && (doc.estado === 'PENDIENTE' || doc.estado === 'CONFIRMADA') && (
                  <button
                    onClick={() => facturarMut.mutate(doc.id)}
                    disabled={facturarMut.isPending}
                    className="cv-btn cv-btn-secondary"
                  >
                    {facturarMut.isPending ? 'Facturando...' : 'Facturar'}
                  </button>
                )}
                {tipo === 'factura' && doc.estado === 'PENDIENTE' && (
                  <button
                    onClick={() => emitirMut.mutate(doc.id)}
                    disabled={emitirMut.isPending}
                    className="cv-btn cv-btn-secondary"
                  >
                    Emitir
                  </button>
                )}
                {isCotizacion && ['VIGENTE', 'ACEPTADA'].includes(doc.estado) && (
                  <button
                    onClick={() => {
                      if (confirm('Convertir a factura?')) convertirMut.mutate(doc.id);
                    }}
                    disabled={convertirMut.isPending}
                    className="cv-btn cv-btn-ghost"
                    style={{ color: 'var(--cv-primary)' }}
                  >
                    Convertir a Factura
                  </button>
                )}
                {doc.estado !== 'ANULADA' && !isCotizacion && (
                  <button
                    onClick={() => {
                      if (confirm('Anular este documento?')) anularMut.mutate(doc.id);
                    }}
                    disabled={anularMut.isPending}
                    className="cv-btn cv-btn-danger"
                  >
                    Anular
                  </button>
                )}
              </>
            )}
          </div>

          <div className="flex gap-2">
            {/* PDF */}
            {!editing && (tipo === 'factura' || tipo === 'cotizacion') && (
              <button
                onClick={() => descargarPdf(doc.id, numero)}
                className="cv-btn cv-btn-ghost"
              >
                PDF
              </button>
            )}
            <button onClick={onClose} className="cv-btn cv-btn-ghost">
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
