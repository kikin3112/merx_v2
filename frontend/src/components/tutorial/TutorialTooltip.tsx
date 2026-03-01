import React, { useState, useRef, useEffect } from 'react';
import { TUTORIALES } from '../../data/tutorial-content';

interface TutorialTooltipProps {
  concepto: keyof typeof TUTORIALES;
  className?: string;
}

export function TutorialTooltip({ concepto, className = '' }: TutorialTooltipProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const tutorial = TUTORIALES[concepto];

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  if (!tutorial) return null;

  return (
    <div className={`relative inline-block ${className}`} ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((p) => !p)}
        className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-100 text-amber-700 text-xs font-bold hover:bg-amber-200 transition-colors"
        aria-label={`Ayuda: ${tutorial.titulo}`}
      >
        ?
      </button>
      {open && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 bg-white rounded-xl shadow-xl border border-amber-200 p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">🕯️</span>
            <p className="font-bold text-sm text-amber-800">{tutorial.titulo}</p>
          </div>
          <p className="text-sm text-gray-700 mb-2">{tutorial.explicacion}</p>
          <div className="bg-amber-50 rounded-lg p-2">
            <p className="text-xs text-amber-700 italic">📌 {tutorial.ejemplo}</p>
          </div>
          <div className="absolute top-full left-1/2 -translate-x-1/2 w-3 h-3 bg-white border-b border-r border-amber-200 rotate-45 -mt-1.5" />
        </div>
      )}
    </div>
  );
}
