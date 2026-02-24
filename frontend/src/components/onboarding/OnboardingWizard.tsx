import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { productos, recetas, terceros } from '../../api/endpoints';
import StepProgress from './StepProgress';

interface OnboardingWizardProps {
  currentStep: number;
  completedSteps: number[];
  totalSteps: number;
  onCompleteStep: (step: number) => void;
  onDismiss: () => void;
}

export default function OnboardingWizard({
  currentStep,
  completedSteps,
  totalSteps,
  onCompleteStep,
  onDismiss,
}: OnboardingWizardProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Step 1: Producto
  const [prodNombre, setProdNombre] = useState('');
  const [prodPrecio, setProdPrecio] = useState('');
  const [prodCategoria, setProdCategoria] = useState('TERMINADO');

  // Step 2: Receta
  const [recetaNombre, setRecetaNombre] = useState('');

  // Step 3: Venta (simplified — just mark as done via POS redirect)

  // Step 5: Cliente
  const [clienteNombre, setClienteNombre] = useState('');
  const [clienteDoc, setClienteDoc] = useState('');

  const [error, setError] = useState('');

  const crearProducto = useMutation({
    mutationFn: () =>
      productos.create({
        codigo_interno: `PROD-001`,
        nombre: prodNombre.trim(),
        categoria: prodCategoria,
        unidad_medida: 'UNIDAD',
        tipo_iva: 'GRAVADO',
        porcentaje_iva: 19,
        precio_venta: parseFloat(prodPrecio) || 0,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding-check'] });
      onCompleteStep(1);
      setError('');
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Error al crear producto');
    },
  });

  const crearReceta = useMutation({
    mutationFn: async () => {
      // Get first product to use as resultado
      const { data: prods } = await productos.list({ limit: 1 });
      if (prods.length === 0) throw new Error('Crea un producto primero');
      return recetas.create({
        nombre: recetaNombre.trim(),
        producto_resultado_id: prods[0].id,
        cantidad_resultado: 1,
        costo_mano_obra: 0,
        ingredientes: [],
      });
    },
    onSuccess: () => {
      onCompleteStep(2);
      setError('');
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Error al crear receta');
    },
  });

  const crearCliente = useMutation({
    mutationFn: () =>
      terceros.create({
        tipo_documento: 'CC',
        numero_documento: clienteDoc.trim() || '0000000000',
        nombre: clienteNombre.trim(),
        tipo_tercero: 'CLIENTE',
      }),
    onSuccess: () => {
      onCompleteStep(5);
      setError('');
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Error al crear cliente');
    },
  });

  const inputClass =
    'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none';

  if (currentStep > totalSteps) {
    return (
      <div className="mb-6 bg-green-50 border border-green-200 rounded-xl p-6 text-center">
        <div className="text-3xl mb-2">🎉</div>
        <h2 className="text-lg font-bold text-green-800 mb-2">¡Onboarding completado!</h2>
        <p className="text-sm text-green-700 mb-4">Ya configuraste lo básico de tu ERP. Explora todas las funciones del menú.</p>
        <button onClick={onDismiss} className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 transition-colors">
          Cerrar guía
        </button>
      </div>
    );
  }

  return (
    <div className="mb-6 bg-primary-50 border border-primary-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Primeros pasos</h2>
          <p className="text-sm text-gray-500">Configura lo básico para empezar a usar ChandeliERP</p>
        </div>
        <button onClick={onDismiss} className="text-xs text-gray-400 hover:text-gray-600 underline">
          Saltar
        </button>
      </div>

      <div className="flex justify-center mb-5">
        <StepProgress currentStep={currentStep} totalSteps={totalSteps} completedSteps={completedSteps} />
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700 mb-4">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg p-4 border border-gray-200">
        {/* Step 1: Primer producto */}
        {currentStep === 1 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-900">Paso 1: Carga tu primer producto</h3>
            <p className="text-xs text-gray-500">Agrega un producto terminado (ej: una vela) para empezar.</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <input type="text" value={prodNombre} onChange={(e) => setProdNombre(e.target.value)} placeholder="Nombre del producto" className={inputClass} />
              <input type="number" value={prodPrecio} onChange={(e) => setProdPrecio(e.target.value)} placeholder="Precio de venta" className={inputClass} />
              <select value={prodCategoria} onChange={(e) => setProdCategoria(e.target.value)} className={inputClass}>
                <option value="TERMINADO">Producto Terminado</option>
                <option value="MATERIA_PRIMA">Materia Prima</option>
                <option value="INSUMO">Insumo</option>
              </select>
            </div>
            <button
              onClick={() => crearProducto.mutate()}
              disabled={!prodNombre.trim() || crearProducto.isPending}
              className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 disabled:opacity-50 transition-colors"
            >
              {crearProducto.isPending ? 'Creando...' : 'Crear producto'}
            </button>
          </div>
        )}

        {/* Step 2: Primera receta */}
        {currentStep === 2 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-900">Paso 2: Crea tu primera receta</h3>
            <p className="text-xs text-gray-500">Una receta define la fórmula de producción (ingredientes + costos). Los ingredientes los puedes agregar después.</p>
            <input type="text" value={recetaNombre} onChange={(e) => setRecetaNombre(e.target.value)} placeholder="Nombre de la receta (ej: Vela Aromática)" className={inputClass} />
            <button
              onClick={() => crearReceta.mutate()}
              disabled={!recetaNombre.trim() || crearReceta.isPending}
              className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 disabled:opacity-50 transition-colors"
            >
              {crearReceta.isPending ? 'Creando...' : 'Crear receta'}
            </button>
          </div>
        )}

        {/* Step 3: Primera venta */}
        {currentStep === 3 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-900">Paso 3: Registra tu primera venta</h3>
            <p className="text-xs text-gray-500">Usa el Punto de Venta (POS) para hacer una venta rápida con el producto que creaste.</p>
            <button
              onClick={() => { onCompleteStep(3); navigate('/pos'); }}
              className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 transition-colors"
            >
              Ir al POS
            </button>
          </div>
        )}

        {/* Step 4: Dashboard */}
        {currentStep === 4 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-900">Paso 4: Revisa tu dashboard</h3>
            <p className="text-xs text-gray-500">El dashboard muestra tus métricas en tiempo real. Ya lo estás viendo — continúa al siguiente paso.</p>
            <button
              onClick={() => onCompleteStep(4)}
              className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 transition-colors"
            >
              Entendido, continuar
            </button>
          </div>
        )}

        {/* Step 5: Primer cliente */}
        {currentStep === 5 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-900">Paso 5: Agrega tu primer cliente</h3>
            <p className="text-xs text-gray-500">Registra un cliente para asociar ventas y dar seguimiento.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <input type="text" value={clienteNombre} onChange={(e) => setClienteNombre(e.target.value)} placeholder="Nombre del cliente" className={inputClass} />
              <input type="text" value={clienteDoc} onChange={(e) => setClienteDoc(e.target.value)} placeholder="No. documento (opcional)" className={inputClass} />
            </div>
            <button
              onClick={() => crearCliente.mutate()}
              disabled={!clienteNombre.trim() || crearCliente.isPending}
              className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 disabled:opacity-50 transition-colors"
            >
              {crearCliente.isPending ? 'Creando...' : 'Crear cliente'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
