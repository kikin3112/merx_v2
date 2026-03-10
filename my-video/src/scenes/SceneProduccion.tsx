import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, Easing, Img, staticFile } from 'remotion';
import { C } from '../tokens';
import { F } from '../fonts';

const INGREDIENTES = [
  { name: 'Cera de soya', qty: '150 g', icon: '🫙' },
  { name: 'Esencia lavanda', qty: '30 ml', icon: '💧' },
  { name: 'Mecha #3', qty: '× 10', icon: '🧵' },
];

// 120 frames (4s) — Módulo de Producción
export const SceneProduccion: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Header
  const headerOpacity = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: 'clamp' });
  const ssePulse = interpolate(frame % 60, [0, 30, 59], [1, 0.35, 1]);

  // Recipe card slides up
  const cardSpring = spring({ frame: frame - 12, fps, config: { damping: 200 }, durationInFrames: 28 });
  const cardOpacity = interpolate(frame, [12, 26], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Ingredients stagger in
  const ingSpring = INGREDIENTES.map((_, i) => ({
    sp: spring({ frame: frame - (38 + i * 12), fps, config: { damping: 200 }, durationInFrames: 22 }),
    op: interpolate(frame, [38 + i * 12, 50 + i * 12], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
  }));

  // Progress bar fills
  const progressVal = interpolate(frame, [72, 108], [0, 100], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.quad),
  });
  const progressOpacity = interpolate(frame, [70, 82], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // "Lote completado" badge
  const badgeScale = spring({ frame: frame - 108, fps, config: { damping: 12, stiffness: 300 }, durationInFrames: 15 });
  const badgeOpacity = interpolate(frame, [108, 116], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  const px = 46;

  return (
    <div style={{
      width: '100%', height: '100%',
      background: C.bg,
      display: 'flex', flexDirection: 'column',
      fontFamily: F.sans,
      position: 'relative', overflow: 'hidden',
    }}>
      {/* Header — logo + En vivo */}
      <div style={{
        height: 161, flexShrink: 0,
        background: C.surface,
        borderBottom: `1px solid ${C.border}`,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        paddingLeft: px, paddingRight: px,
        opacity: headerOpacity,
      }}>
        <Img
          src={staticFile('logo-grande-white.png')}
          style={{ height: 69, objectFit: 'contain' }}
        />
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 12,
          background: C.positiveDim,
          borderRadius: 9999,
          padding: '10px 24px',
        }}>
          <div style={{
            width: 17, height: 17, borderRadius: '50%',
            background: C.positive,
            opacity: ssePulse,
          }} />
          <span style={{
            fontFamily: F.mono, fontSize: 28, fontWeight: 500,
            color: C.positive, letterSpacing: '0.04em',
          }}>
            En vivo
          </span>
        </div>
      </div>

      {/* Content */}
      <div style={{
        flex: 1,
        paddingLeft: px, paddingRight: px,
        paddingTop: 48,
        display: 'flex', flexDirection: 'column',
        gap: 32,
        overflow: 'hidden',
      }}>
        {/* Recipe card */}
        <div style={{
          opacity: cardOpacity,
          transform: `translateY(${(1 - cardSpring) * 40}px)`,
          background: C.surface,
          borderRadius: 32,
          padding: '40px 46px',
          border: `1px solid ${C.accentDim}`,
          position: 'relative', overflow: 'hidden',
        }}>
          {/* Accent glow */}
          <div style={{
            position: 'absolute', right: -60, top: -60,
            width: 250, height: 250, borderRadius: '50%',
            background: `radial-gradient(circle, ${C.accent}20 0%, transparent 70%)`,
            pointerEvents: 'none',
          }} />
          <div style={{ fontFamily: F.mono, fontSize: 24, color: C.muted, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 12 }}>
            Orden de producción
          </div>
          <div style={{ fontFamily: F.brand, fontSize: 64, fontWeight: 700, color: C.text, letterSpacing: '-0.02em', marginBottom: 16 }}>
            Velas Lavanda
          </div>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 10,
            background: C.accentDim,
            border: `1px solid ${C.accent}40`,
            borderRadius: 100, padding: '8px 24px',
          }}>
            <span style={{ fontFamily: F.mono, fontSize: 26, color: C.accent, fontWeight: 600 }}>Lote × 10 und</span>
          </div>
        </div>

        {/* Ingredients section */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ fontFamily: F.mono, fontSize: 24, color: C.muted, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 10 }}>
            Ingredientes
          </div>
          {INGREDIENTES.map((ing, i) => (
            <div key={ing.name} style={{
              opacity: ingSpring[i].op,
              transform: `translateX(${(1 - ingSpring[i].sp) * -40}px)`,
              background: C.surface,
              borderRadius: 24,
              padding: '28px 40px',
              border: `1px solid ${C.border}`,
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
                <span style={{ fontSize: 44 }}>{ing.icon}</span>
                <span style={{ fontFamily: F.sans, fontSize: 38, color: C.text, fontWeight: 500 }}>
                  {ing.name}
                </span>
              </div>
              <span style={{ fontFamily: F.mono, fontSize: 34, color: C.muted, fontWeight: 600 }}>
                {ing.qty}
              </span>
            </div>
          ))}
        </div>

        {/* Progress bar */}
        <div style={{ opacity: progressOpacity, display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontFamily: F.mono, fontSize: 24, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Progreso
            </span>
            <span style={{ fontFamily: F.mono, fontSize: 40, fontWeight: 600, color: C.accent }}>
              {Math.round(progressVal)}%
            </span>
          </div>
          <div style={{
            height: 16, background: C.elevated,
            borderRadius: 100, overflow: 'hidden',
          }}>
            <div style={{
              height: '100%',
              width: `${progressVal}%`,
              background: `linear-gradient(90deg, ${C.accent}88, ${C.accent})`,
              borderRadius: 100,
              boxShadow: `0 0 16px ${C.accent}60`,
            }} />
          </div>
        </div>

        {/* "Lote completado" badge */}
        <div style={{
          opacity: badgeOpacity,
          transform: `scale(${badgeScale})`,
          background: C.positiveDim,
          border: `2px solid ${C.positive}`,
          borderRadius: 24,
          padding: '40px 48px',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 24,
          boxShadow: `0 0 40px ${C.positive}25`,
        }}>
          <svg width="52" height="52" fill="none" viewBox="0 0 24 24" stroke={C.positive} strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span style={{ fontFamily: F.brand, fontSize: 52, fontWeight: 700, color: C.positive }}>
            ¡Lote completado!
          </span>
        </div>
      </div>
    </div>
  );
};
