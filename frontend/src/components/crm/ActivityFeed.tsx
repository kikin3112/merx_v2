import type { CrmActivity } from '../../types';

interface ActivityFeedProps {
  activities: CrmActivity[];
}

export default function ActivityFeed({ activities }: ActivityFeedProps) {
  if (activities.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg mb-2">📝</p>
        <p>No hay actividades registradas</p>
        <p className="text-sm mt-1">Agrega la primera actividad para comenzar</p>
      </div>
    );
  }

  // Íconos por tipo de actividad
  const getActivityIcon = (tipo: string) => {
    switch (tipo) {
      case 'NOTA':
        return '📝';
      case 'LLAMADA':
        return '📞';
      case 'EMAIL':
        return '📧';
      case 'REUNION':
        return '👥';
      case 'WHATSAPP':
        return '💬';
      case 'TAREA':
        return '✓';
      default:
        return '•';
    }
  };

  // Color por tipo de actividad
  const getActivityColor = (tipo: string) => {
    switch (tipo) {
      case 'NOTA':
        return 'bg-blue-100 text-blue-800';
      case 'LLAMADA':
        return 'bg-green-100 text-green-800';
      case 'EMAIL':
        return 'bg-purple-100 text-purple-800';
      case 'REUNION':
        return 'bg-orange-100 text-orange-800';
      case 'WHATSAPP':
        return 'bg-emerald-100 text-emerald-800';
      case 'TAREA':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Formatear fecha relativa
  const formatRelativeDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Hace un momento';
    if (diffMins < 60) return `Hace ${diffMins} min`;
    if (diffHours < 24) return `Hace ${diffHours}h`;
    if (diffDays === 1) return 'Ayer';
    if (diffDays < 7) return `Hace ${diffDays} días`;

    return date.toLocaleDateString('es-CO', {
      day: 'numeric',
      month: 'short',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
  };

  return (
    <div className="space-y-4">
      {activities.map((activity) => (
        <div
          key={activity.id}
          className="flex gap-3 p-4 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
        >
          {/* Icon */}
          <div className="flex-shrink-0">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${getActivityColor(
                activity.tipo
              )}`}
            >
              {getActivityIcon(activity.tipo)}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-1">
              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-0.5 text-xs font-medium rounded ${getActivityColor(
                    activity.tipo
                  )}`}
                >
                  {activity.tipo}
                </span>
                {activity.asunto && (
                  <h4 className="text-sm font-semibold text-gray-900">{activity.asunto}</h4>
                )}
              </div>
              <time className="text-xs text-gray-500 whitespace-nowrap">
                {formatRelativeDate(activity.fecha_actividad)}
              </time>
            </div>

            {/* Contenido */}
            {activity.contenido && (
              <p className="text-sm text-gray-700 mb-2 whitespace-pre-wrap">{activity.contenido}</p>
            )}

            {/* Footer */}
            <div className="flex items-center gap-3 text-xs text-gray-500">
              {activity.usuario_nombre && (
                <span>👤 {activity.usuario_nombre}</span>
              )}
              {activity.es_automatica && (
                <span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">
                  Automático
                </span>
              )}
              {activity.duracion_minutos > 0 && (
                <span>⏱️ {activity.duracion_minutos} min</span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
