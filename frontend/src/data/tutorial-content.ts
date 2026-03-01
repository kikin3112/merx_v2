export interface TutorialConcepto {
  titulo: string;
  explicacion: string;
  ejemplo: string;
}

export const TUTORIALES: Record<string, TutorialConcepto> = {
  costoIngredientes: {
    titulo: 'Costo de ingredientes',
    explicacion: 'Es cuánto te costó todo lo que le pusiste a tu vela: la cera, la mecha, la fragancia...',
    ejemplo: 'Si usaste 200g de cera a $8.000/kg, eso son $1.600 de ingredientes.',
  },
  costoManoObra: {
    titulo: 'Mano de obra',
    explicacion: 'Lo que te pagas por hacer TODA esta tanda. Pon el total de la tanda — el sistema divide solo entre la cantidad de velas.',
    ejemplo: '10 velas en 2 horas, te pagas $25.000/hora → 2 × $25.000 = $50.000. Escribes 50000. El sistema calcula $5.000 por vela.',
  },
  costosIndirectos: {
    titulo: 'Gastos adicionales',
    explicacion: 'Los gastos del negocio que no son solo de una vela, pero que también cuentan: el gas, el empaque, la electricidad.',
    ejemplo: 'Si gastas $50.000 en empaques y haces 100 velas al mes, son $500 por vela.',
  },
  margenContribucion: {
    titulo: 'Lo que te "queda" de cada vela',
    explicacion: 'Después de pagar los materiales y tu trabajo, esto es lo que contribuye a cubrir tus gastos fijos del negocio.',
    ejemplo: 'Si vendes a $15.000 y te costó $8.000 hacerla, te quedan $7.000 de contribución.',
  },
  puntoEquilibrio: {
    titulo: '¿Cuántas velas necesitas vender?',
    explicacion: 'El punto de equilibrio es la cantidad mínima de velas que tienes que vender para no perder dinero en el mes.',
    ejemplo: 'Si tus gastos fijos son $300.000 y te quedan $7.000 por vela, necesitas vender 43 velas para no perder.',
  },
  margenSeguridad: {
    titulo: 'Qué tan segura estás',
    explicacion: 'Si ya alcanzaste tu punto de equilibrio, el margen de seguridad te dice cuántas velas más puedes dejar de vender antes de empezar a perder.',
    ejemplo: 'Si vendes 80 y tu punto de equilibrio es 43, tienes 37 velas de "colchón".',
  },
  analisisSensibilidad: {
    titulo: '¿Qué pasa si...?',
    explicacion: 'Te ayuda a ver cómo cambian tus ganancias si los precios de tus materiales suben o bajan.',
    ejemplo: 'Si la cera sube 20%, ¿cuántas velas más tendrías que vender para ganar lo mismo?',
  },
  economiasEscala: {
    titulo: 'Hacer más sale más barato',
    explicacion: 'Cuando produces más velas de una vez, algunos gastos se reparten entre más velas y el costo por vela baja.',
    ejemplo: 'Si haces 50 velas en vez de 5, el costo de preparar los moldes se divide entre 50, no entre 5.',
  },
  margenObjetivo: {
    titulo: '¿Cuánto quieres ganar?',
    explicacion: 'Es el porcentaje de ganancia que quieres tener sobre el precio de venta. Tú decides cuánto.',
    ejemplo: 'Con un margen del 60%, si tu vela cuesta $6.000 hacerla, el precio sugerido es $15.000.',
  },
  precioSugerido: {
    titulo: 'Precio recomendado',
    explicacion: 'Calculamos automáticamente cuánto deberías cobrar para lograr el margen que quieres.',
    ejemplo: 'Si quieres ganar el 60% y tu costo es $6.000, te sugerimos vender a $15.000.',
  },
  ratioMargenContribucion: {
    titulo: 'Eficiencia de cada peso',
    explicacion: 'De cada $100 que recibes por tu vela, este número te dice cuántos quedan para cubrir tus gastos fijos.',
    ejemplo: 'Con un ratio del 47%, de cada $15.000 vendidos, $7.050 contribuyen a cubrir gastos fijos.',
  },
};
