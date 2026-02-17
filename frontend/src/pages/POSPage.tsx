import { useState, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productos, terceros, facturas } from '../api/endpoints';
import { formatCurrency } from '../utils/format';
import type { Producto, Tercero, Factura } from '../types';
import { usePOSStore } from '../stores/posStore';
import { useBreakpoint } from '../hooks/useMediaQuery';

interface QuickClientForm {
  nombre: string;
  tipo_documento: string;
  numero_documento: string;
  telefono: string;
  email: string;
}

const CATEGORIAS = ['Todas', 'Insumo', 'Producto_Propio', 'Producto_Tercero', 'Servicio'];
const TIPOS_DOCUMENTO = ['CC', 'NIT', 'CE', 'TI', 'PP'];

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

  // POS Store persistente
  const {
    cart,
    clienteId,
    descuentoGlobal,
    addToCart: addToCartStore,
    removeFromCart,
    updateQuantity,
    setCliente,
    setDescuento,
    clearCart
  } = usePOSStore();

  const [busqueda, setBusqueda] = useState('');
  const [categoriaFiltro, setCategoriaFiltro] = useState('Todas');
  const [mobileTab, setMobileTab] = useState<'productos' | 'carrito'>('productos');
  const [checkoutOk, setCheckoutOk] = useState(false);
  const [lastFactura, setLastFactura] = useState<Factura | null>(null);
  const [showQuickClient, setShowQuickClient] = useState(false);
  const [clientForm, setClientForm] = useState<QuickClientForm>(emptyClientForm);

  const { data: productosData } = useQuery<Producto[]>({
    queryKey: ['productos'],
    queryFn: () => productos.list({ estado: true }).then(r => r.data),
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

  // Set default client
  useEffect(() => {
    if (tercerosData?.length && !clienteId) {
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
        className="w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 mb-3"
      />

      {/* Category tabs */}
      <div className="flex gap-1.5 mb-4 overflow-x-auto pb-1">
        {CATEGORIAS.map(cat => (
          <button
            key={cat}
            onClick={() => setCategoriaFiltro(cat)}
            className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              categoriaFiltro === cat
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
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
            className="flex flex-col items-start bg-white rounded-xl border border-gray-200 p-3 text-left hover:border-primary-300 hover:shadow-sm active:scale-95 transition-all min-h-[80px]"
          >
            <p className="text-sm font-medium text-gray-900 line-clamp-2 leading-tight">{p.nombre}</p>
            <p className="text-xs text-gray-400 mt-0.5">{p.codigo_interno}</p>
            <p className="text-sm font-bold text-primary-600 mt-auto pt-1">{formatCurrency(p.precio_venta)}</p>
          </button>
        ))}
        {productosFiltrados.length === 0 && (
          <p className="col-span-full text-center text-gray-400 py-8">
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
        <label className="text-xs font-medium text-gray-500 mb-1 block">Cliente</label>
        <select
          value={clienteId}
          onChange={e => { setCliente(e.target.value); setShowQuickClient(false); }}
          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500"
        >
          {tercerosData?.map(t => (
            <option key={t.id} value={t.id}>{t.nombre}</option>
          ))}
        </select>
        {isMostrador && !showQuickClient && (
          <button
            onClick={() => setShowQuickClient(true)}
            className="mt-1.5 text-xs font-medium text-primary-600 hover:text-primary-700 transition-colors"
          >
            + Registrar nuevo cliente
          </button>
        )}
      </div>

      {/* Quick client registration */}
      {showQuickClient && (
        <div className="mb-3 bg-white rounded-lg border border-primary-200 p-3 space-y-2">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-semibold text-gray-700">Nuevo cliente</p>
            <button
              onClick={() => { setShowQuickClient(false); setClientForm(emptyClientForm); }}
              className="text-gray-400 hover:text-gray-600 p-0.5"
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
            className="w-full rounded border border-gray-200 px-2.5 py-1.5 text-sm focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
          />
          <div className="flex gap-2">
            <select
              value={clientForm.tipo_documento}
              onChange={e => setClientForm(f => ({ ...f, tipo_documento: e.target.value }))}
              className="rounded border border-gray-200 px-2 py-1.5 text-sm focus:ring-1 focus:ring-primary-500"
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
            className="w-full rounded border border-gray-200 px-2.5 py-1.5 text-sm focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
          />
          <input
            placeholder="Email (opcional)"
            type="email"
            value={clientForm.email}
            onChange={e => setClientForm(f => ({ ...f, email: e.target.value }))}
            className="w-full rounded border border-gray-200 px-2.5 py-1.5 text-sm focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
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
          <div className="text-center py-8 text-gray-400">
            <p className="text-lg mb-1">Carrito vacio</p>
            <p className="text-sm">Agrega productos para comenzar</p>
          </div>
        ) : (
          cart.map(item => (
            <div key={item.producto.id} className="bg-white rounded-lg border border-gray-200 p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-900 truncate">{item.producto.nombre}</p>
                  <p className="text-xs text-gray-500">{formatCurrency(item.producto.precio_venta)} c/u</p>
                </div>
                <button
                  onClick={() => handleRemoveItem(item.producto.id)}
                  className="text-gray-400 hover:text-red-500 p-1 transition-colors"
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
                    className="w-8 h-8 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-600 font-bold transition-colors"
                  >
                    -
                  </button>
                  <span className="w-8 text-center text-sm font-semibold">{item.cantidad}</span>
                  <button
                    onClick={() => handleUpdateQty(item.producto.id, item.cantidad + 1)}
                    className="w-8 h-8 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-600 font-bold transition-colors"
                  >
                    +
                  </button>
                </div>
                <p className="text-sm font-bold text-gray-900">
                  {formatCurrency(item.cantidad * item.producto.precio_venta)}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Totals + Checkout */}
      <div className="border-t border-gray-200 pt-3 space-y-2">
        <div className="flex justify-between text-sm text-gray-600">
          <span>Subtotal</span>
          <span>{formatCurrency(totals.subtotal)}</span>
        </div>
        {/* Global discount */}
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <span>Desc. global</span>
            <input
              type="number"
              min={0}
              max={100}
              step={1}
              value={descuentoGlobal}
              onChange={e => setDescuento(Math.min(100, Math.max(0, Number(e.target.value))))}
              className="w-14 text-right rounded border border-gray-200 px-1.5 py-0.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
            <span className="text-xs text-gray-400">%</span>
          </div>
          {totals.montoDescGlobal > 0 && (
            <span className="text-red-600">-{formatCurrency(totals.montoDescGlobal)}</span>
          )}
        </div>
        {totals.totalIva > 0 && (
          <div className="flex justify-between text-sm text-gray-600">
            <span>IVA</span>
            <span>{formatCurrency(totals.totalIva)}</span>
          </div>
        )}
        <div className="flex justify-between text-lg font-bold text-gray-900">
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
              Factura {lastFactura.numero_venta} emitida!
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
          <h1 className="text-xl font-bold text-gray-900 mb-4">Punto de Venta</h1>
          {productGrid}
        </div>
        <div className="col-span-2 bg-gray-50 rounded-xl p-4 flex flex-col">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Carrito ({cart.length})</h2>
          {cartPanel}
        </div>
      </div>

      {/* Mobile layout */}
      <div className="lg:hidden flex flex-col h-full">
        {/* Mobile tabs */}
        <div className="flex border-b border-gray-200 mb-3">
          <button
            onClick={() => setMobileTab('productos')}
            className={`flex-1 py-3 text-sm font-medium text-center transition-colors ${
              mobileTab === 'productos'
                ? 'text-primary-600 border-b-2 border-primary-500'
                : 'text-gray-500'
            }`}
          >
            Productos
          </button>
          <button
            onClick={() => setMobileTab('carrito')}
            className={`flex-1 py-3 text-sm font-medium text-center transition-colors relative ${
              mobileTab === 'carrito'
                ? 'text-primary-600 border-b-2 border-primary-500'
                : 'text-gray-500'
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
