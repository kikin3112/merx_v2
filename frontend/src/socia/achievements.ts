export interface Logro {
  id: string;
  titulo: string;
  emoji: string;
  mensaje?: string;
}

export interface Nivel {
  id: string;
  nombre: string;
  descripcion: string;
  requerimientos: string[];
  desbloquea: string;
  emoji: string;
}

export const LOGROS: Logro[] = [
  { id: 'primera_receta', titulo: '¡Primera receta!', emoji: '🕯️', mensaje: '¡Listo! Creaste tu primera receta. Ya empezamos 🕯️' },
  { id: 'primer_calculo_costo', titulo: '¡Calculé tu primer costo!', emoji: '🔢' },
  { id: 'primer_cvu', titulo: '¡Análisis completo!', emoji: '📈' },
  { id: 'primer_punto_equilibrio', titulo: '¡Ya sabes cuánto vender!', emoji: '⚖️' },
  { id: 'primer_costo_indirecto', titulo: '¡Sin gastos escondidos!', emoji: '🔍' },
  { id: 'primer_escenario_precio', titulo: '¡Exploraste opciones!', emoji: '🎲' },
  { id: 'primera_sensibilidad', titulo: '¡Viste el futuro!', emoji: '🔮' },
  { id: '5_recetas_activas', titulo: '¡Catálogo creciendo!', emoji: '🌱' },
  { id: 'equilibrio_real_mes', titulo: '¡Mes en positivo!', emoji: '💰' },
  { id: '10_producciones', titulo: '¡100 velas producidas!', emoji: '✨' },
];

export const NIVELES: Nivel[] = [
  {
    id: 'emprendedora',
    nombre: 'Emprendedora',
    descripcion: 'Empezaste a ordenar tu negocio',
    requerimientos: ['primera_receta', 'primer_calculo_costo'],
    desbloquea: 'Acceso a análisis de punto de equilibrio',
    emoji: '🕯️',
  },
  {
    id: 'conocedora',
    nombre: 'Conocedora',
    descripcion: 'Ya entiendes tus números',
    requerimientos: ['primer_cvu', 'primer_punto_equilibrio', 'primer_costo_indirecto'],
    desbloquea: 'Acceso al comparador de rentabilidad',
    emoji: '📊',
  },
  {
    id: 'estratega',
    nombre: 'Estratega',
    descripcion: 'Tomas decisiones con datos',
    requerimientos: ['primer_escenario_precio', 'primera_sensibilidad', '5_recetas_activas'],
    desbloquea: 'Acceso a análisis de economías de escala',
    emoji: '🎯',
  },
  {
    id: 'empresaria',
    nombre: 'Empresaria',
    descripcion: 'Diriges tu negocio como una pro',
    requerimientos: ['equilibrio_real_mes', 'exportar_analisis', '10_producciones'],
    desbloquea: 'Acceso anticipado a nuevas funciones de Socia',
    emoji: '🏆',
  },
];

export function getNivelInfo(nivelId: string): Nivel {
  return NIVELES.find((n) => n.id === nivelId) ?? NIVELES[0];
}

export function getLogroInfo(logroId: string): Logro | undefined {
  return LOGROS.find((l) => l.id === logroId);
}
