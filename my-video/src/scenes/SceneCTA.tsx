import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, Easing, Img, staticFile } from 'remotion';
import { C } from '../tokens';
import { F } from '../fonts';

// 90 frames (3s) — CTA final
export const SceneCTA: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Background gradient reveal
  const bgOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  // Logo spring
  const logoScale = spring({ frame: frame - 8, fps, config: { damping: 200 } });
  const logoOpacity = interpolate(frame, [8, 28], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Divider line
  const lineWidth = interpolate(frame, [28, 50], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.out(Easing.quad),
  });

  // Price
  const priceY = interpolate(frame, [35, 58], [40, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.out(Easing.quad),
  });
  const priceOpacity = interpolate(frame, [35, 55], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // CTA button
  const btnScale = spring({ frame: frame - 52, fps, config: { damping: 12, stiffness: 250 }, durationInFrames: 22 });
  const btnOpacity = interpolate(frame, [52, 65], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Arrow bounce
  const arrowX = interpolate(frame, [65, 75, 85], [0, 10, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.quad),
  });

  // Link in bio
  const linkOpacity = interpolate(frame, [68, 82], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <div style={{
      width: '100%', height: '100%',
      position: 'relative', overflow: 'hidden',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      fontFamily: F.sans,
    }}>
      {/* Background igual a SceneHook */}
      <div style={{ position: 'absolute', inset: 0, background: C.bg }} />
      <div style={{
        position: 'absolute',
        width: 1100, height: 1100,
        borderRadius: '50%',
        background: `radial-gradient(circle, ${C.primary}50 0%, ${C.primary}18 40%, transparent 70%)`,
        opacity: bgOpacity,
        top: '50%', left: '50%',
        marginTop: -550, marginLeft: -550,
        pointerEvents: 'none',
      }} />

      {/* Content */}
      <div style={{
        position: 'relative', zIndex: 1,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', gap: 48,
        width: '100%',
        paddingLeft: 80, paddingRight: 80,
      }}>
        {/* Logo */}
        <div style={{
          opacity: logoOpacity,
          transform: `scale(${logoScale})`,
        }}>
          <Img
            src={staticFile('logo-pequeno-white.png')}
            style={{ width: 420, display: 'block' }}
          />
        </div>

        {/* Divider */}
        <div style={{
          width: `${lineWidth * 240}px`,
          height: 2,
          background: `linear-gradient(90deg, transparent, ${C.primary}, transparent)`,
          borderRadius: 1,
        }} />

        {/* Price */}
        <div style={{
          opacity: priceOpacity,
          transform: `translateY(${priceY}px)`,
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12,
        }}>
          <div style={{ fontFamily: F.mono, fontSize: 30, color: C.muted, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Bueno · Bonito · Barato
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
            <span style={{ fontFamily: F.brand, fontSize: 100, fontWeight: 700, color: C.primary, letterSpacing: '-0.04em', lineHeight: 1 }}>
              $15.000
            </span>
            <span style={{ fontFamily: F.mono, fontSize: 36, color: C.muted }}>/mes</span>
          </div>
          <div style={{ fontFamily: F.mono, fontSize: 26, color: C.muted }}>
            Inventario · Ventas · Contabilidad · Producción
          </div>
        </div>

        {/* CTA button */}
        <div style={{
          opacity: btnOpacity,
          transform: `scale(${btnScale})`,
          background: C.primary,
          borderRadius: 24,
          padding: '40px 72px',
          display: 'flex', alignItems: 'center', gap: 20,
          boxShadow: `0 0 60px ${C.primary}50`,
        }}>
          <span style={{ fontFamily: F.brand, fontSize: 52, fontWeight: 700, color: C.bg }}>
            Prueba gratis hoy
          </span>
          <span style={{
            fontFamily: F.sans, fontSize: 52, color: C.bg, fontWeight: 700,
            transform: `translateX(${arrowX}px)`,
            display: 'inline-block',
          }}>
            →
          </span>
        </div>

        {/* Link in bio */}
        <div style={{
          opacity: linkOpacity,
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10,
        }}>
          <div style={{ fontFamily: F.mono, fontSize: 26, color: C.muted, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
            🔗 Link en bio
          </div>
          <div style={{ fontFamily: F.mono, fontSize: 24, color: C.primary }}>
            chandelierp-erp.vercel.app
          </div>
        </div>
      </div>
    </div>
  );
};
