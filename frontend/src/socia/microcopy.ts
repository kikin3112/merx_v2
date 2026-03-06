export const SOCIA_MESSAGES = {
  primeraReceta: "¡Listo! Creaste tu primera receta. Ya empezamos 🌱",
  margenAlto: (pct: number) => `¡Bacana! Este producto te deja el ${pct}% de ganancia 💚`,
  puntoEquilibrio: (pe: number) => `Vendiendo ${pe} unidades ya cubres los gastos. Lo que sobrepases es ganancia pura 🎉`,
  precioSugerido: (precio: string) => `Tu Socia te sugiere vender a ${precio}. ¿Qué te parece?`,
  margenBajo: "Ojo con este, linda... estás ganando muy poco. Te ayudo a ajustar el precio ⚡",
  sinCostosIndirectos: "Psst... no has agregado tus gastos del negocio (arriendo, empaques, servicios...). Sin ellos tu precio puede quedar corto 🤫",
  stockBajo: "Te falta material para producir. ¿Revisamos el inventario juntas?",
  mejorProducto: (nombre: string) => `Tu "${nombre}" es el más rentable de tu catálogo. ¡Ponle amor a ese! 💛`,
  productoMejorable: (nombre: string) => `El "${nombre}" puede mejorar. Con un ajuste de precio podrías ganar mucho más 📈`,
  logrosDesbloqueados: (n: number) => `¡Desbloqueaste ${n} logro${n > 1 ? 's' : ''}! Míralo 👇`,
  bienvenida: "¡Hola! Soy Socia, tu asistente de precios ✨ Te ayudo a ponerle el precio justo a cada producto para que tu negocio crezca y nunca trabajes a pérdida.",
  primerCalculo: "¡Calculé tu primer costo! Ahora ya sabes cuánto te cuesta hacer cada producto 🔢",
  margenEquilibrado: "Este producto tiene un margen sano. ¡Sigue así! 📊",
};

export const SOCIA_THEME = {
  primary: '#F59E0B',
  primaryLight: '#FEF3C7',
  accent: '#8B5CF6',
  accentLight: '#EDE9FE',
  success: '#10B981',
  warning: '#F97316',
  danger: '#EF4444',
  background: '#FFFBF0',
};
