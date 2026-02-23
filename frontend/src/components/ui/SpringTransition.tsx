/**
 * Wrapper React Spring para micro-interacciones y transiciones de estado.
 * Usa @react-spring/web para animaciones físicamente realistas.
 */
import React from 'react';
import { useSpring, animated } from '@react-spring/web';

interface FadeInProps {
  children: React.ReactNode;
  delay?: number;
}

/** Fade-in suave al montar un componente. */
export function FadeIn({ children, delay = 0 }: FadeInProps) {
  const style = useSpring({
    from: { opacity: 0, transform: 'translateY(8px)' },
    to: { opacity: 1, transform: 'translateY(0px)' },
    delay,
    config: { tension: 280, friction: 24 },
  });
  return <animated.div style={style}>{children}</animated.div>;
}

interface PulseOnChangeProps {
  children: React.ReactNode;
  trigger: unknown; // Cambia para activar la animación
}

/** Pulso visual cuando cambia un valor (ej. contador de eventos SSE). */
export function PulseOnChange({ children, trigger }: PulseOnChangeProps) {
  const [style, api] = useSpring(() => ({
    scale: 1,
    config: { tension: 400, friction: 10 },
  }));

  React.useEffect(() => {
    api.start({ scale: 1.06, immediate: false });
    const t = setTimeout(() => api.start({ scale: 1 }), 200);
    return () => clearTimeout(t);
  }, [trigger, api]);

  return <animated.div style={style}>{children}</animated.div>;
}

interface SuccessBadgeProps {
  show: boolean;
  message: string;
}

/** Badge verde que aparece y desaparece para confirmar éxito. */
export function SuccessBadge({ show, message }: SuccessBadgeProps) {
  const style = useSpring({
    opacity: show ? 1 : 0,
    transform: show ? 'translateY(0px)' : 'translateY(-4px)',
    config: { tension: 300, friction: 20 },
  });
  if (!show) return null;
  return (
    <animated.span
      style={style}
      className="inline-flex items-center gap-1 rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700"
    >
      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
      {message}
    </animated.span>
  );
}
