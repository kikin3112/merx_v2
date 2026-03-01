import React, { useEffect, useState } from 'react';
import { getLogroInfo } from '../achievements';

interface SociaAchievementProps {
  logroId: string;
  onDismiss: () => void;
}

export function SociaAchievement({ logroId, onDismiss }: SociaAchievementProps) {
  const [visible, setVisible] = useState(false);
  const logro = getLogroInfo(logroId);

  useEffect(() => {
    const t1 = setTimeout(() => setVisible(true), 50);
    const t2 = setTimeout(() => {
      setVisible(false);
      setTimeout(onDismiss, 300);
    }, 4000);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [onDismiss]);

  if (!logro) return null;

  return (
    <div
      className={`fixed bottom-6 right-6 z-50 transition-all duration-300 ${
        visible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'
      }`}
    >
      <div className="bg-white rounded-2xl shadow-xl border border-amber-200 p-4 flex items-center gap-3 max-w-xs">
        <span className="text-4xl">{logro.emoji}</span>
        <div>
          <p className="text-xs text-amber-600 font-semibold uppercase tracking-wide">¡Logro desbloqueado!</p>
          <p className="text-sm font-bold text-gray-800">{logro.titulo}</p>
          {logro.mensaje && <p className="text-xs text-gray-500 mt-0.5">{logro.mensaje}</p>}
        </div>
        <button
          onClick={() => { setVisible(false); setTimeout(onDismiss, 300); }}
          className="ml-auto text-gray-300 hover:text-gray-500"
        >
          ×
        </button>
      </div>
    </div>
  );
}
