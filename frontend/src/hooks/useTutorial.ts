import { useCallback, useState } from 'react';

const STORAGE_KEY = 'socia_tutorial_v1';

interface TutorialState {
  completed: boolean;
  pasoActual: number;
  omitido: boolean;
}

export function useTutorial(userId: string, tenantId: string) {
  const key = `${STORAGE_KEY}_${tenantId}_${userId}`;

  const [state, setState] = useState<TutorialState>(() => {
    try {
      const stored = localStorage.getItem(key);
      return stored ? JSON.parse(stored) : { completed: false, pasoActual: 0, omitido: false };
    } catch {
      return { completed: false, pasoActual: 0, omitido: false };
    }
  });

  const save = useCallback(
    (next: TutorialState) => {
      setState(next);
      try { localStorage.setItem(key, JSON.stringify(next)); } catch { /* noop */ }
    },
    [key]
  );

  const avanzar = useCallback(() => {
    save({ ...state, pasoActual: state.pasoActual + 1 });
  }, [state, save]);

  const completar = useCallback(() => {
    save({ ...state, completed: true, pasoActual: 0 });
  }, [state, save]);

  const omitir = useCallback(() => {
    save({ ...state, omitido: true, completed: true });
  }, [state, save]);

  const reiniciar = useCallback(() => {
    save({ completed: false, pasoActual: 0, omitido: false });
  }, [save]);

  const debesMostrar = !state.completed && !state.omitido;

  return { state, avanzar, completar, omitir, reiniciar, debesMostrar };
}
