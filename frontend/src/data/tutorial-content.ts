export interface TutorialConcepto {
  titulo: string;
  explicacion: string;
  ejemplo: string;
}

export const TUTORIALES: Record<string, TutorialConcepto> = {
  costoIngredientes: {
    titulo: 'Costo de ingredientes',
    explicacion: 'Es cuánto te costó todo lo que le pusiste a tu producto: los materiales, insumos o ingredientes que usaste.',
    ejemplo: 'Si usaste 500g de harina a $4.000/kg, eso son $2.000 de ingredientes. O 200g de cera de soya a $8.000/kg → $1.600.',
  },
  costoManoObra: {
    titulo: 'Mano de obra',
    explicacion: 'Lo que te pagas por hacer TODA esta tanda. Pon el total de la tanda — el sistema divide solo entre la cantidad de unidades.',
    ejemplo: '10 unidades en 2 horas, te pagas $25.000/hora → 2 × $25.000 = $50.000. Escribes 50000. El sistema calcula $5.000 por unidad.',
  },
  costosIndirectos: {
    titulo: 'Gastos adicionales',
    explicacion: 'Los gastos del negocio que no son solo de un producto, pero que también cuentan: el gas, el empaque, la electricidad.',
    ejemplo: 'Si gastas $50.000 en empaques y produces 100 unidades al mes, son $500 por unidad.',
  },
  margenContribucion: {
    titulo: 'Lo que te "queda" de cada producto',
    explicacion: 'Después de pagar los materiales y tu trabajo, esto es lo que contribuye a cubrir tus gastos fijos del negocio.',
    ejemplo: 'Si vendes a $15.000 y te costó $8.000 producirlo, te quedan $7.000 de contribución.',
  },
  puntoEquilibrio: {
    titulo: '¿Cuántas unidades necesitas vender?',
    explicacion: 'El punto de equilibrio es la cantidad mínima de unidades que tienes que vender para no perder dinero en el mes.',
    ejemplo: 'Si tus gastos fijos son $300.000 y te quedan $7.000 por unidad, necesitas vender 43 para no perder.',
  },
  margenSeguridad: {
    titulo: 'Qué tan segura estás',
    explicacion: 'Si ya alcanzaste tu punto de equilibrio, el margen de seguridad te dice cuántas unidades más puedes dejar de vender antes de empezar a perder.',
    ejemplo: 'Si vendes 80 y tu punto de equilibrio es 43, tienes 37 unidades de "colchón".',
  },
  analisisSensibilidad: {
    titulo: '¿Qué pasa si...?',
    explicacion: 'Te ayuda a ver cómo cambian tus ganancias si los precios de tus materiales suben o bajan.',
    ejemplo: 'Si tu materia prima sube 20%, ¿cuántas unidades más tendrías que vender para ganar lo mismo?',
  },
  economiasEscala: {
    titulo: 'Hacer más sale más barato',
    explicacion: 'Cuando produces más unidades de una vez, algunos gastos se reparten entre más productos y el costo por unidad baja.',
    ejemplo: 'Si haces 50 unidades en vez de 5, el costo de preparar los insumos se divide entre 50, no entre 5.',
  },
  margenObjetivo: {
    titulo: '¿Cuánto quieres ganar?',
    explicacion: 'Es el porcentaje de ganancia que quieres tener sobre el precio de venta. Tú decides cuánto.',
    ejemplo: 'Con un margen del 60%, si tu producto cuesta $6.000 producirlo, el precio sugerido es $15.000.',
  },
  precioSugerido: {
    titulo: 'Precio recomendado',
    explicacion: 'Calculamos automáticamente cuánto deberías cobrar para lograr el margen que quieres.',
    ejemplo: 'Si quieres ganar el 60% y tu costo es $6.000, te sugerimos vender a $15.000.',
  },
  ratioMargenContribucion: {
    titulo: 'Eficiencia de cada peso',
    explicacion: 'De cada $100 que recibes por tu producto, este número te dice cuántos quedan para cubrir tus gastos fijos.',
    ejemplo: 'Con un ratio del 47%, de cada $15.000 vendidos, $7.050 contribuyen a cubrir gastos fijos.',
  },

  // ── FACTURAS ──────────────────────────────────────────────────────────────
  estadoFactura: {
    titulo: 'Estados de la factura',
    explicacion: 'Una factura pasa por varios estados: Borrador (aún editando), Emitida (enviada al cliente), Pagada (dinero recibido), Anulada (cancelada).',
    ejemplo: 'Creas la factura en Borrador, la revisas, la Emites por WhatsApp y cuando te paguen la marcas como Pagada.',
  },
  envioFactura: {
    titulo: 'Enviar factura al cliente',
    explicacion: 'Puedes mandarle la factura al cliente por WhatsApp o por correo directamente desde el sistema, sin salir.',
    ejemplo: 'Abres la factura, tocas el botón de WhatsApp y le llega el link al número del cliente. Así de fácil.',
  },
  impuestosFactura: {
    titulo: 'IVA y otros impuestos',
    explicacion: 'El IVA general en Colombia es del 19%. Algunos productos tienen tarifas especiales (5%) o están exentos (0%).',
    ejemplo: 'Un producto artesanal con IVA del 19%: si cuesta $10.000, el cliente paga $11.900 en total.',
  },
  numeracionFactura: {
    titulo: 'Número de factura',
    explicacion: 'Cada factura tiene un número único y consecutivo. El sistema lo asigna automáticamente — no lo puedes repetir ni saltarte.',
    ejemplo: 'Si la última fue FAC-0042, la siguiente será FAC-0043, siempre.',
  },

  // ── VENTAS ────────────────────────────────────────────────────────────────
  flujoVenta: {
    titulo: 'Cómo fluye una venta',
    explicacion: 'Una venta puede nacer como cotización, convertirse en factura al aceptarse y quedar pagada cuando el cliente cancele.',
    ejemplo: 'Le mandas una cotización a tu cliente, la acepta, la conviertes en factura y cuando te pague la marcas como pagada.',
  },
  estadoVenta: {
    titulo: 'Estados de una venta',
    explicacion: 'Borrador: aún sin enviar. Emitida: enviada al cliente. Pagada: dinero recibido. Anulada: cancelada por algún motivo.',
    ejemplo: 'Si un cliente te cancela el pedido, anulass la factura. El inventario vuelve a su estado anterior.',
  },
  terceroVenta: {
    titulo: 'Cliente (tercero)',
    explicacion: 'El cliente al que le vendes. Si ya lo tienes registrado en el sistema, el sistema trae sus datos automáticamente.',
    ejemplo: 'La primera vez creas a "Tienda La Palma" con su celular. La próxima venta solo la buscas por nombre.',
  },

  // ── COTIZACIONES ──────────────────────────────────────────────────────────
  estadoCotizacion: {
    titulo: 'Estados de una cotización',
    explicacion: 'Borrador: en preparación. Enviada: el cliente la recibió. Aceptada: aprobó el precio. Rechazada: no quiso. Vencida: expiró el plazo.',
    ejemplo: 'Le mandas la cotización, el cliente dice que sí — la marcas Aceptada y la conviertes en factura.',
  },
  validezCotizacion: {
    titulo: 'Validez de la cotización',
    explicacion: 'Es hasta cuándo es válido el precio que cotizaste. Después de esa fecha, los precios pueden cambiar.',
    ejemplo: 'Cotizas 50 unidades a $15.000 con validez de 15 días. Si el cliente llama en el día 16, puedes reajustar el precio.',
  },
  convertirCotizacion: {
    titulo: 'Convertir a factura',
    explicacion: 'Cuando el cliente acepta, conviertes la cotización en factura con un clic — no tienes que volver a escribir todo.',
    ejemplo: 'Cotización aceptada → botón "Convertir a factura" → todos los productos y precios ya están listos.',
  },

  // ── INVENTARIO ────────────────────────────────────────────────────────────
  stockMinimo: {
    titulo: 'Stock mínimo (alerta)',
    explicacion: 'Es la cantidad mínima que debes tener de un insumo o producto. Cuando bajes de ese nivel, el sistema te avisa.',
    ejemplo: 'Tienes 5kg de materia prima como mínimo. Si bajas de eso, el sistema te avisa para que pidas más.',
  },
  movimientoInventario: {
    titulo: 'Movimientos de inventario',
    explicacion: 'Cada vez que entra o sale mercancía queda registrado: compras que entran, ventas que salen, ajustes manuales.',
    ejemplo: 'Compraste insumos → entran al inventario. Produjiste unidades → salen los materiales del inventario.',
  },
  ajusteInventario: {
    titulo: 'Ajuste de inventario',
    explicacion: 'Cuando el conteo físico no cuadra con el sistema, haces un ajuste para corregir la diferencia.',
    ejemplo: 'El sistema dice que tienes 8kg de insumo pero el físico da 7.5kg. Haces un ajuste de -0.5kg con el motivo.',
  },
  costoProducto: {
    titulo: 'Costo del producto',
    explicacion: 'Es cuánto te costó conseguir o producir una unidad. Este costo sale en los reportes de rentabilidad.',
    ejemplo: 'Tu producto te cuesta $8.000 producirlo. Si lo vendes a $15.000, ganás $7.000 brutos por unidad.',
  },

  // ── CONTABILIDAD ──────────────────────────────────────────────────────────
  causacion: {
    titulo: 'Causación',
    explicacion: 'Registrar un ingreso o gasto en el momento en que ocurre, aunque todavía no haya movido plata.',
    ejemplo: 'Le vendiste a crédito: causas la venta hoy aunque el cliente pague en 30 días.',
  },
  cuentaContable: {
    titulo: 'Cuentas contables',
    explicacion: 'Son las "cajitas" donde se clasifica cada peso del negocio: activos (lo que tienes), pasivos (lo que debes), ingresos y gastos.',
    ejemplo: 'El dinero en tu billetera va a "Caja". Lo que te deben los clientes va a "Cuentas por cobrar".',
  },
  periodoContable: {
    titulo: 'Período contable',
    explicacion: 'El mes o año que estás mirando. Filtras los movimientos por período para ver cómo le fue al negocio en ese tiempo.',
    ejemplo: 'Cierras febrero: ves todos los ingresos y gastos de ese mes y sabes si ganaste o perdiste.',
  },
  utilidadNeta: {
    titulo: 'Utilidad neta',
    explicacion: 'Lo que queda después de pagar todos los gastos — es la ganancia real del negocio en el período.',
    ejemplo: 'Ingresaron $3.000.000, gastos $1.800.000 → utilidad neta $1.200.000. Eso es lo que "te ganó" el negocio.',
  },

  // ── CARTERA ───────────────────────────────────────────────────────────────
  carteraPorCobrar: {
    titulo: 'Cartera por cobrar',
    explicacion: 'Son las facturas que ya emitiste pero que el cliente todavía no ha pagado. Es plata que te deben.',
    ejemplo: 'Vendiste $500.000 a crédito en enero y solo han pagado $200.000. Tienes $300.000 en cartera por cobrar.',
  },
  diasCartera: {
    titulo: 'Días en cartera',
    explicacion: 'Cuántos días lleva una factura sin pagarse. Entre más días, más difícil puede ser cobrar.',
    ejemplo: 'Una factura de hace 45 días sin pagar es cartera vencida. Hay que llamar al cliente.',
  },
  abono: {
    titulo: 'Abono o pago parcial',
    explicacion: 'Cuando el cliente paga una parte de la factura pero no el total. El sistema lleva el saldo pendiente.',
    ejemplo: 'Factura de $300.000, el cliente abona $100.000. Saldo pendiente: $200.000.',
  },

  // ── COMERCIAL / CRM ───────────────────────────────────────────────────────
  pipeline: {
    titulo: 'Pipeline de ventas',
    explicacion: 'Es el embudo que muestra en qué etapa va cada cliente potencial: desde que lo conoces hasta que te compra.',
    ejemplo: 'Prospecto nuevo → Interesado → Cotizando → Cerrado. Así sabes qué clientes necesitan atención.',
  },
  prospectoComercial: {
    titulo: 'Prospecto',
    explicacion: 'Un posible cliente que aún no te ha comprado pero que tiene interés en tus productos.',
    ejemplo: 'La señora que te escribió por Instagram preguntando por tus productos para su evento — es un prospecto.',
  },
  actividadComercial: {
    titulo: 'Actividades de seguimiento',
    explicacion: 'Las acciones que haces con un prospecto: llamadas, mensajes, reuniones. El sistema las registra para no perder el hilo.',
    ejemplo: 'Llamaste a María el lunes, le mandaste muestra el miércoles. Todo queda en el historial del prospecto.',
  },

  // ── POS ───────────────────────────────────────────────────────────────────
  cajaPos: {
    titulo: 'Punto de venta (POS)',
    explicacion: 'Para ventas rápidas en mostrador: buscas el producto, lo agregas al carrito y registras el pago. Sin papeleos.',
    ejemplo: 'Un cliente llega a comprarte 3 productos. Los agregas al carrito, cobras y listo — la venta queda registrada.',
  },
  metodoPago: {
    titulo: 'Métodos de pago',
    explicacion: 'Puedes registrar si el cliente pagó en efectivo, transferencia, Nequi, Daviplata u otro medio.',
    ejemplo: 'El cliente paga mitad en efectivo y mitad por Nequi — registras ambos y el sistema cuadra el total.',
  },
};
