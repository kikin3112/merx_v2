import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, Easing, Img, staticFile } from 'remotion';
import { C } from '../tokens';
import { F } from '../fonts';

// 90 frames (3s) — Brand reveal
export const SceneHook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Logo spring entrance
  const logoScale = spring({ frame, fps, config: { damping: 18, stiffness: 160 }, durationInFrames: 40 });
  const logoOpacity = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: 'clamp' });

  // Tagline slides up
  const taglineY = interpolate(frame, [22, 52], [60, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.out(Easing.quad),
  });
  const taglineOpacity = interpolate(frame, [22, 48], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const line2Y = interpolate(frame, [32, 62], [60, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.out(Easing.quad),
  });
  const line2Opacity = interpolate(frame, [32, 58], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Background glow breathes
  const glowOpacity = interpolate(frame, [0, 45, 90], [0.25, 0.45, 0.35], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const glowScale = interpolate(frame, [0, 90], [0.85, 1.05], { extrapolateRight: 'clamp' });

  return (
    <div
      style={{
        width: '100%', height: '100%',
        background: C.bg,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        position: 'relative', overflow: 'hidden',
        fontFamily: F.sans,
      }}
    >
      {/* Coral radial glow */}
      <div style={{
        position: 'absolute',
        width: 1100, height: 1100,
        borderRadius: '50%',
        background: `radial-gradient(circle, ${C.primary}50 0%, ${C.primary}18 40%, transparent 70%)`,
        opacity: glowOpacity,
        transform: `scale(${glowScale})`,
        top: '50%', left: '50%',
        marginTop: -550, marginLeft: -550,
        pointerEvents: 'none',
      }} />

      {/* Main content */}
      <div style={{
        position: 'relative', zIndex: 1,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', gap: 56,
      }}>
        {/* Logo — versión blanca directo sobre fondo oscuro */}
        <div style={{
          opacity: logoOpacity,
          transform: `scale(${logoScale})`,
        }}>
          <Img
            src={staticFile('logo-grande-white.png')}
            style={{ width: 860, display: 'block' }}
          />
        </div>

        {/* Tagline — dos líneas escalonadas */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
          {/* Línea 1 */}
          <div style={{
            opacity: taglineOpacity,
            transform: `translateY(${taglineY}px)`,
            fontFamily: F.mono,
            fontSize: 36,
            fontWeight: 400,
            color: C.muted,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            textAlign: 'center',
          }}>
            asistente administrativo para
          </div>
          {/* Línea 2 */}
          <div style={{
            opacity: line2Opacity,
            transform: `translateY(${line2Y}px)`,
            fontFamily: F.mono,
            fontSize: 36,
            fontWeight: 500,
            color: C.primary,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            textAlign: 'center',
          }}>
            emprendedor@s solitari@s
          </div>
        </div>
      </div>
    </div>
  );
};
