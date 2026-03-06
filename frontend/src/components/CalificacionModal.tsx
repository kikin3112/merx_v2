import { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { calificaciones } from '../api/endpoints';
import type { CalificacionResponse } from '../types';

interface Props {
  onClose: () => void;
}

export default function CalificacionModal({ onClose }: Props) {
  const qc = useQueryClient();
  const [estrellas, setEstrellas] = useState(5);
  const [hovered, setHovered] = useState(0);
  const [titulo, setTitulo] = useState('');
  const [comentario, setComentario] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const { data: miCalificacion } = useQuery<CalificacionResponse | null>({
    queryKey: ['mi-calificacion'],
    queryFn: () =>
      calificaciones.miCalificacion().then((r) => r.data).catch(() => null),
  });

  // Pre-fill form if already rated
  useEffect(() => {
    if (miCalificacion) {
      setEstrellas(miCalificacion.estrellas);
      setTitulo(miCalificacion.titulo || '');
      setComentario(miCalificacion.comentario || '');
    }
  }, [miCalificacion]);

  const crearMut = useMutation({
    mutationFn: () =>
      calificaciones.crear({ estrellas, titulo: titulo || undefined, comentario: comentario || undefined }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['mi-calificacion'] });
      setSubmitted(true);
    },
  });

  const displayEstrellas = hovered || estrellas;

  if (submitted) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
        <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8 text-center">
          <div className="text-5xl mb-4">⭐</div>
          <h3 className="text-lg font-bold text-gray-900 mb-2">¡Gracias por tu calificación!</h3>
          <p className="text-sm text-gray-500 mb-6">
            Tu opinión está en revisión y será publicada pronto.
          </p>
          <button
            onClick={onClose}
            className="rounded-lg bg-primary-500 text-white px-6 py-2 text-sm font-medium hover:bg-primary-600 transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-2">
          <h2 className="text-lg font-bold text-gray-900">Califica chandelierp</h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="px-6 pb-6 space-y-4">
          {miCalificacion && (
            <p className="text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2">
              Ya tienes una calificación ({miCalificacion.estrellas} ★ — {miCalificacion.estado}). Puedes actualizarla.
            </p>
          )}

          {/* Stars */}
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">¿Cómo calificarías el sistema?</p>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setEstrellas(n)}
                  onMouseEnter={() => setHovered(n)}
                  onMouseLeave={() => setHovered(0)}
                  className="text-3xl transition-transform hover:scale-110 focus:outline-none"
                  aria-label={`${n} estrellas`}
                >
                  <span className={n <= displayEstrellas ? 'text-amber-400' : 'text-gray-300'}>★</span>
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-1">
              {estrellas === 1 ? 'Muy malo' : estrellas === 2 ? 'Malo' : estrellas === 3 ? 'Regular' : estrellas === 4 ? 'Bueno' : 'Excelente'}
            </p>
          </div>

          {/* Titulo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Título <span className="text-gray-400 font-normal">(opcional)</span>
            </label>
            <input
              type="text"
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
              maxLength={200}
              placeholder="Ej: Muy fácil de usar"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Comentario */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Comentario <span className="text-gray-400 font-normal">(opcional)</span>
            </label>
            <textarea
              value={comentario}
              onChange={(e) => setComentario(e.target.value)}
              rows={3}
              placeholder="Cuéntanos tu experiencia..."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            />
          </div>

          {crearMut.isError && (
            <p className="text-xs text-red-600">Error al enviar. Inténtalo de nuevo.</p>
          )}

          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-300 text-gray-700 px-4 py-2 text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={() => crearMut.mutate()}
              disabled={crearMut.isPending}
              className="rounded-lg bg-primary-500 text-white px-6 py-2 text-sm font-medium hover:bg-primary-600 transition-colors disabled:opacity-50"
            >
              {crearMut.isPending ? 'Enviando...' : 'Enviar calificación'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
