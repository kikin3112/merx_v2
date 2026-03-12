import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/** Colombia = UTC-5, sin horario de verano */
function getColombiaHour(): number {
  const utcHour = new Date().getUTCHours();
  return (utcHour - 5 + 24) % 24;
}

/** Light de 6:00 a 17:59 hora Colombia; dark el resto */
function computeColombiaTheme(): 'dark' | 'light' {
  const h = getColombiaHour();
  return h >= 6 && h < 18 ? 'light' : 'dark';
}

function applyThemeToDom(theme: 'dark' | 'light') {
  document.documentElement.classList.toggle('dark', theme === 'dark');
  document.documentElement.classList.toggle('light', theme === 'light');
}

interface ThemeStore {
  theme: 'dark' | 'light';
  autoSync: boolean;
  toggleTheme: () => void;
  setTheme: (theme: 'dark' | 'light') => void;
  syncColombiaTheme: () => void;
  setAutoSync: (enabled: boolean) => void;
}

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set, get) => ({
      theme: computeColombiaTheme(),
      autoSync: true,

      toggleTheme: () => {
        const next = get().theme === 'dark' ? 'light' : 'dark';
        set({ theme: next, autoSync: false }); // manual override desactiva auto
        applyThemeToDom(next);
      },

      setTheme: (theme) => {
        set({ theme });
        applyThemeToDom(theme);
      },

      syncColombiaTheme: () => {
        if (!get().autoSync) return;
        const theme = computeColombiaTheme();
        if (get().theme !== theme) {
          set({ theme });
          applyThemeToDom(theme);
        }
      },

      setAutoSync: (enabled) => {
        set({ autoSync: enabled });
        if (enabled) {
          const theme = computeColombiaTheme();
          set({ theme });
          applyThemeToDom(theme);
        }
      },
    }),
    {
      name: 'merx_theme',
      partialize: (s) => ({ theme: s.theme, autoSync: s.autoSync }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          // Si autoSync activo, sobrescribir con hora actual de Colombia
          const theme = state.autoSync ? computeColombiaTheme() : state.theme;
          applyThemeToDom(theme);
          if (state.autoSync && state.theme !== theme) {
            state.theme = theme;
          }
        }
      },
    }
  )
);
