import { useState, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productos, terceros, facturas } from '../api/endpoints';
import { formatCurrency } from '../utils/format';
import type { Producto, Tercero, Factura } from '../types';
import { usePOSStore } from '../stores/posStore';
import { useAuthStore } from '../stores/authStore';
import { useBreakpoint } from '../hooks/useMediaQuery';
import { trackPOSSale, trackInvoiceCreated } from '../hooks/useAnalytics';

interface QuickClientForm {
  nombre: string;
  tipo_documento: string;
  numero_documento: string;
  telefono: string;
  email: string;
}

const CATEGORIAS = ['Todas', 'Insumo', 'Producto_Propio', 'Producto_Tercero', 'Servicio'];
const TIPOS_DOCUMENTO = ['CC', 'NIT', 'CE', 'PAS', 'TI'];

const emptyClientForm: QuickClientForm = {
  nombre: '',
  tipo_documento: 'CC',
  numero_documento: '',
  telefono: '',
  email: '',
};

export default function POSPage() {
  const queryClient = useQueryClient();
  const { isDesktop } = useBreakpoint();
  const tenantId = useAuthStore((s) => s.tenantId);

  // POS Store persistente
  const {
    cart,
    clienteId,
    cartTenantId,
    descuentoGlobal,
    addToCart: addToCartStore,
    removeFromCart,
    updateQuantity,
    setCliente,
    setDescuento,
    clearCart,
    reset: resetCart,
    setCartTenant,
  } = usePOSStore();

  // Cross-tenant guard: reset cart if tenant changed
  useEffect(() => {
    if (tenantId && cartTenantId && cartTenantId !== tenantId) {
      resetCart();
    }
    if (tenantId && cartTenantId !== tenantId) {
      setCartTenant(tenantId);
    }
  }, [tenantId, cartTenantId, resetCart, setCartTenant]);

  const [busqueda, setBusqueda] = useState('');
  const [categoriaFiltro, setCategoriaFiltro] = useState('Todas');
  const [mobileTab, setMobileTab] = useState<'productos' | 'carrito'>('productos');
  const [checkoutOk, setCheckoutOk] = useState(false);
  const [lastFactura, setLastFactura] = useState<Factura | null>(null);
  const [showQuickClient, setShowQuickClient] = useState(false);
  const [clientForm, setClientForm] = useState<QuickClientForm>(emptyClientForm);

  const { data: productosData } = useQuery<Producto[]>({
    queryKey: ['productos'],
    queryFn: () => productos.list({ estado: true, limit: 500 }).then(r => r.data),
  });

  const { data: tercerosData } = useQuery<Tercero[]>({
    queryKey: ['terceros-clientes'],
    queryFn: () => terceros.list({ tipo_tercero: 'CLIENTE' }).then(r => r.data),
  });

  const isMostrador = useMemo(() => {
    if (!clienteId || !tercerosData) return false;
    const selected = tercerosData.find(t => t.id === clienteId);
    return selected?.numero_documento === '222222222222' ||
      selected?.nombre.toLowerCase().includes('mostrador');
  }, [clienteId, tercerosData]);

  const createClientMutation = useMutation({
    mutationFn: (data: QuickClientForm) =>
      terceros.create({
        nombre: data.nombre,
        tipo_documento: data.tipo_documento,
        numero_documento: data.numero_documento,
        tipo_tercero: 'CLIENTE',
        telefono: data.telefono || null,
        email: data.email || null,
      }),
    onSuccess: (response) => {
      const newClient = response.data;
      setCliente(newClient.id);
      setShowQuickClient(false);
      setClientForm(emptyClientForm);
      queryClient.invalidateQueries({ queryKey: ['terceros-clientes'] });
      queryClient.invalidateQueries({ queryKey: ['terceros'] });
    },
  });

  // Set default client — also invalidates stale clienteId from a previous tenant session.
  // posStore persists clienteId across sessions; on tenant switch the UUID may belong
  // to a different tenant and the backend will 404 on "Tercero no encontrado".
  useEffect(() => {
    if (!tercerosData?.length) return;
    const clienteValido = clienteId && tercerosData.some(t => t.id === clienteId);
    if (!clienteValido) {
      const mostrador = tercerosData.find(t =>
        t.nombre.toLowerCase().includes('mostrador') || t.numero_documento === '222222222222'
      );
      setCliente(mostrador?.id || tercerosData[0].id);
    }
  }, [tercerosData, clienteId, setCliente]);

  const productosFiltrados = useMemo(() => {
    if (!productosData) return [];
    return productosData.filter(p => {
      const matchBusqueda = !busqueda ||
        p.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
        p.codigo_interno.toLowerCase().includes(busqueda.toLowerCase());
      const matchCategoria = categoriaFiltro === 'Todas' || p.categoria === categoriaFiltro;
      return matchBusqueda && matchCategoria && p.estado;
    });
  }, [productosData, busqueda, categoriaFiltro]);

  const handleAddToCart = (producto: Producto) => {
    addToCartStore(producto);
    // Switch to cart on mobile
    if (!isDesktop) setMobileTab('carrito');
  };

  const handleUpdateQty = (productoId: string, newQuantity: number) => {
    updateQuantity(productoId, newQuantity);
  };

  const handleRemoveItem = (productoId: string) => {
    removeFromCart(productoId);
  };

  const totals = useMemo(() => {
    let subtotal = 0;
    let totalIva = 0;
    for (const item of cart) {
      const linea = item.cantidad * item.producto.precio_venta;
      const iva = linea * (item.producto.porcentaje_iva / 100);
      subtotal += linea;
      totalIva += iva;
    }
    const dg = descuentoGlobal || 0;
    const montoDescGlobal = dg > 0 ? subtotal * (dg / 100) : 0;
    const factor = dg > 0 ? (100 - dg) / 100 : 1;
    const ivaAjustado = totalIva * factor;
    const total = subtotal - montoDescGlobal + ivaAjustado;
    return { subtotal, montoDescGlobal, totalIva: ivaAjustado, total };
  }, [cart, descuentoGlobal]);

  const descargarPdf = async (facturaId: string, numero: string) => {
    try {
      const response = await facturas.descargarPdf(facturaId);
      const blob = new Blob([response.data as BlobPart], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `factura-${numero}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      // PDF download failed silently - factura was still created
    }
  };

  const posMutation = useMutation({
    mutationFn: () => {
      const hoy = new Date().toISOString().split('T')[0];
      return facturas.pos({
        tercero_id: clienteId,
        fecha_venta: hoy,
        descuento_global: descuentoGlobal || 0,
        detalles: cart.map(item => ({
          producto_id: item.producto.id,
          cantidad: item.cantidad,
          precio_unitario: item.producto.precio_venta,
          descuento: 0,
          porcentaje_iva: item.producto.porcentaje_iva,
        })),
      });
    },
    onSuccess: (response) => {
      const factura = response.data;
      trackPOSSale(totals.total, cart.length);
      trackInvoiceCreated(totals.total);
      clearCart();
      setCheckoutOk(true);
      setLastFactura(factura);
      setTimeout(() => { setCheckoutOk(false); setLastFactura(null); }, 10000);
      queryClient.invalidateQueries({ queryKey: ['ventas'] });
      queryClient.invalidateQueries({ queryKey: ['facturas'] });
      queryClient.invalidateQueries({ queryKey: ['reportes'] });
    },
  });

  // --- Render sections ---

  const productGrid = (
    <div>
      {/* Search */}
      <input
        type="text"
        placeholder="Buscar producto..."
        value={busqueda}
        onChange={e => setBusqueda(e.target.value)}
        className="cv-input mb-3"
      />

      {/* Category tabs */}
      <div className="flex gap-1.5 mb-4 overflow-x-auto pb-1">
        {CATEGORIAS.map(cat => (
          <button
            key={cat}
            onClick={() => setCategoriaFiltro(cat)}
            className={`whitespace-nowrap cv-badge cursor-pointer transition-colors ${
              categoriaFiltro === cat
                ? 'cv-badge-primary'
                : 'cv-badge-neutral'
            }`}
          >
            {cat === 'Todas' ? 'Todas' : cat.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Product grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
        {productosFiltrados.map(p => (
          <button
            key={p.id}
            onClick={() => handleAddToCart(p)}
            className="flex flex-col items-start cv-card-hover p-3 text-left active:scale-95 transition-all min-h-[80px]"
          >
            <p className="text-sm font-medium cv-text line-clamp-2 leading-tight">{p.nombre}</p>
            <p className="text-xs cv-muted mt-0.5">{p.codigo_interno}</p>
            <p className="text-sm font-bold cv-primary mt-auto pt-1">{formatCurrency(p.precio_venta)}</p>
          </button>
        ))}
        {productosFiltrados.length === 0 && (
          <p className="col-span-full text-center cv-muted py-8">
            No se encontraron productos
          </p>
        )}
      </div>
    </div>
  );

  const cartPanel = (
    <div className="flex flex-col h-full">
      {/* Client selector */}
      <div className="mb-3">
        <label className="text-xs font-medium cv-muted mb-1 block">Cliente</label>
        <select
          value={clienteId}
          onChange={e => { setCliente(e.target.value); setShowQuickClient(false); }}
          className="cv-input"
        >
          {tercerosData?.map(t => (
            <option key={t.id} value={t.id}>{t.nombre}</option>
          ))}
        </select>
        {isMostrador && !showQuickClient && (
          <button
            onClick={() => setShowQuickClient(true)}
            className="mt-1.5 text-xs font-medium cv-primary hover:opacity-80 transition-opacity"
          >
            + Registrar nuevo cliente
          </button>
        )}
      </div>

      {/* Quick client registration */}
      {showQuickClient && (
        <div className="mb-3 cv-card p-3 space-y-2" style={{ borderColor: 'var(--cv-primary)' }}>
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-semibold cv-text">Nuevo cliente</p>
            <button
              onClick={() => { setShowQuickClient(false); setClientForm(emptyClientForm); }}
              className="cv-icon-btn p-0.5"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <input
            placeholder="Nombre *"
            value={clientForm.nombre}
            onChange={e => setClientForm(f => ({ ...f, nombre: e.target.value }))}
            className="cv-input"
          />
          <div className="flex gap-2">
            <select
              value={clientForm.tipo_documento}
              onChange={e => setClientForm(f => ({ ...f, tipo_documento: e.target.value }))}
              className="cv-input w-auto"
            >
              {TIPOS_DOCUMENTO.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <input
              placeholder="No. documento *"
              value={clientForm.numero_documento}
              onChange={e => setClientForm(f => ({ ...f, numero_documento: e.target.value }))}
              className="flex-1 rounded border border-gray-200 px-2.5 py-1.5 text-sm focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <input
            placeholder="Telefono (opcional)"
            value={clientForm.telefono}
            onChange={e => setClientForm(f => ({ ...f, telefono: e.target.value }))}
            className="cv-input"
          />
          <input
            placeholder="Email (opcional)"
            type="email"
            value={clientForm.email}
            onChange={e => setClientForm(f => ({ ...f, email: e.target.value }))}
            className="cv-input"
          />
          {createClientMutation.isError && (
            <p className="text-xs text-red-600">
              {(createClientMutation.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error creando cliente'}
            </p>
          )}
          <button
            onClick={() => createClientMutation.mutate(clientForm)}
            disabled={!clientForm.nombre.trim() || !clientForm.numero_documento.trim() || createClientMutation.isPending}
            className="w-full py-2 rounded-lg bg-primary-500 text-white text-sm font-medium hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {createClientMutation.isPending ? 'Guardando...' : 'Guardar cliente'}
          </button>
        </div>
      )}

      {/* Cart items */}
      <div className="flex-1 overflow-y-auto space-y-2 mb-3">
        {cart.length === 0 ? (
          <div className="text-center py-8 cv-muted">
            <p className="text-lg mb-1">Carrito vacío</p>
            <p className="text-sm">Agrega productos para comenzar</p>
          </div>
        ) : (
          cart.map(item => (
            <div key={item.producto.id} className="cv-card p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium cv-text truncate">{item.producto.nombre}</p>
                  <p className="text-xs cv-muted">{formatCurrency(item.producto.precio_venta)} c/u</p>
                </div>
                <button
                  onClick={() => handleRemoveItem(item.producto.id)}
                  className="cv-muted hover:text-red-500 p-1 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="flex items-center justify-between mt-2">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleUpdateQty(item.producto.id, item.cantidad - 1)}
                    className="w-8 h-8 rounded-lg cv-elevated hover:cv-bg flex items-center justify-center cv-text font-bold transition-colors"
                  >
                    -
                  </button>
                  <span className="w-8 text-center text-sm font-semibold">{item.cantidad}</span>
                  <button
                    onClick={() => handleUpdateQty(item.producto.id, item.cantidad + 1)}
                    className="w-8 h-8 rounded-lg cv-elevated hover:cv-bg flex items-center justify-center cv-text font-bold transition-colors"
                  >
                    +
                  </button>
                </div>
                <p className="text-sm font-bold cv-text">
                  {formatCurrency(item.cantidad * item.producto.precio_venta)}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Totals + Checkout */}
      <div className="border-t cv-divider pt-3 space-y-2">
        <div className="flex justify-between text-sm cv-muted">
          <span>Subtotal</span>
          <span>{formatCurrency(totals.subtotal)}</span>
        </div>
        {/* Global discount */}
        <div className="flex items-center justify-between text-sm cv-muted">
          <div className="flex items-center gap-2">
            <span>Descuento global</span>
            <input
              type="number"
              min={0}
              max={100}
              step={1}
              value={descuentoGlobal}
              onChange={e => setDescuento(Math.min(100, Math.max(0, Number(e.target.value))))}
              className="w-14 text-right cv-input px-1.5 py-0.5 text-sm"
            />
            <span className="text-xs cv-muted">%</span>
          </div>
          {totals.montoDescGlobal > 0 && (
            <span className="text-red-600">-{formatCurrency(totals.montoDescGlobal)}</span>
          )}
        </div>
        {totals.totalIva > 0 && (
          <div className="flex justify-between text-sm cv-muted">
            <span>IVA</span>
            <span>{formatCurrency(totals.totalIva)}</span>
          </div>
        )}
        <div className="flex justify-between text-lg font-bold cv-text">
          <span>TOTAL</span>
          <span>{formatCurrency(totals.total)}</span>
        </div>

        <button
          onClick={() => posMutation.mutate()}
          disabled={cart.length === 0 || !clienteId || posMutation.isPending}
          className="w-full py-4 rounded-xl bg-primary-500 text-white text-lg font-bold hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors active:scale-[0.98]"
        >
          {posMutation.isPending ? 'Procesando...' : `COBRAR ${formatCurrency(totals.total)}`}
        </button>

        {checkoutOk && lastFactura && (
          <div className="text-center space-y-2">
            <p className="text-sm font-medium text-green-600">
              ¡Factura {lastFactura.numero_venta} emitida!
            </p>
            <button
              onClick={() => descargarPdf(lastFactura.id, lastFactura.numero_venta)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-green-50 px-3 py-1.5 text-xs font-medium text-green-700 hover:bg-green-100 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Descargar PDF
            </button>
          </div>
        )}

        {posMutation.isError && (
          <p className="text-center text-sm text-red-600">
            {(posMutation.error as any)?.response?.data?.detail || 'Error procesando venta'}
          </p>
        )}
      </div>
    </div>
  );

  return (
    <div className="h-[calc(100vh-4rem)]">
      {/* Desktop layout */}
      <div className="hidden lg:grid lg:grid-cols-5 gap-4 h-full">
        <div className="col-span-3 overflow-y-auto pr-2">
          <h1 className="font-brand text-xl font-medium cv-text mb-4">Punto de Venta</h1>
          {productGrid}
        </div>
        <div className="col-span-2 cv-card-elevated rounded-xl p-4 flex flex-col">
          <h2 className="text-sm font-semibold cv-text mb-3">Carrito ({cart.length})</h2>
          {cartPanel}
        </div>
      </div>

      {/* Mobile layout */}
      <div className="lg:hidden flex flex-col h-full">
        {/* Mobile tabs */}
        <div className="flex border-b cv-divider mb-3">
          <button
            onClick={() => setMobileTab('productos')}
            className={`flex-1 py-3 text-sm font-medium text-center transition-colors ${
              mobileTab === 'productos'
                ? 'cv-primary border-b-2 border-[var(--cv-primary)]'
                : 'cv-muted'
            }`}
          >
            Productos
          </button>
          <button
            onClick={() => setMobileTab('carrito')}
            className={`flex-1 py-3 text-sm font-medium text-center transition-colors relative ${
              mobileTab === 'carrito'
                ? 'cv-primary border-b-2 border-[var(--cv-primary)]'
                : 'cv-muted'
            }`}
          >
            Carrito
            {cart.length > 0 && (
              <span className="absolute top-2 right-1/4 bg-primary-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {cart.length}
              </span>
            )}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {mobileTab === 'productos' ? productGrid : cartPanel}
        </div>
      </div>
    </div>
  );
}
