import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, Easing, Img, staticFile } from 'remotion';
import { C } from '../tokens';
import { F } from '../fonts';

// Typing animation helper
function typed(frame: number, from: number, to: number, text: string): string {
  const chars = Math.floor(
    interpolate(frame, [from, to], [0, text.length], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
      easing: Easing.linear,
    })
  );
  return text.slice(0, chars);
}

const CLIENTE = 'Pepita Pérez';
const PRODUCTO = 'Vela Lavanda';
const PRECIO_UNIT = 25000;
const CANTIDAD = 3;
const TOTAL = PRECIO_UNIT * CANTIDAD;

// 195 frames (6.5s) — Nueva Venta
export const SceneVenta: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: 'clamp' });
  const ssePulse = interpolate(frame % 60, [0, 30, 59], [1, 0.35, 1]);

  // Form fields appear in sequence
  const clienteLabelSpring = spring({ frame: frame - 10, fps, config: { damping: 200 }, durationInFrames: 22 });
  const clienteOpacity = interpolate(frame, [10, 24], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const clienteText = typed(frame, 20, 60, CLIENTE);

  const productoSpring = spring({ frame: frame - 65, fps, config: { damping: 200 }, durationInFrames: 22 });
  const productoOpacity = interpolate(frame, [65, 78], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const productoText = typed(frame, 72, 100, PRODUCTO);

  // Quantity row
  const cantidadSpring = spring({ frame: frame - 100, fps, config: { damping: 200 }, durationInFrames: 22 });
  const cantidadOpacity = interpolate(frame, [100, 114], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Animated total
  const totalVal = Math.round(
    interpolate(frame, [110, 140], [0, TOTAL], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
      easing: Easing.out(Easing.quad),
    })
  );
  const totalOpacity = interpolate(frame, [110, 128], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Guardar button pulse
  const btnScale = 1 + interpolate(frame, [138, 148, 158], [0, 0.05, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const btnOpacity = interpolate(frame, [130, 145], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Success overlay slides up
  const successY = interpolate(frame, [155, 178], [400, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const successOpacity = interpolate(frame, [155, 172], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Cursor blink
  const cursor = frame % 14 < 7 ? '|' : '';

  const px = 46;

  const inputStyle: React.CSSProperties = {
    background: C.elevated,
    border: `1px solid ${C.borderMid}`,
    borderRadius: 24,
    padding: '36px 40px',
    fontFamily: F.sans,
    fontSize: 40,
    color: C.text,
    width: '100%',
    boxSizing: 'border-box',
  };

  const labelStyle: React.CSSProperties = {
    fontFamily: F.mono,
    fontSize: 24,
    color: C.muted,
    letterSpacing: '0.06em',
    textTransform: 'uppercase',
    marginBottom: 12,
  };

  return (
    <div style={{
      width: '100%', height: '100%',
      background: C.bg,
      display: 'flex', flexDirection: 'column',
      fontFamily: F.sans,
      position: 'relative', overflow: 'hidden',
    }}>
      {/* Header — logo + En vivo (igual al Dashboard) */}
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

      {/* Form content */}
      <div style={{
        flex: 1,
        paddingLeft: px, paddingRight: px,
        paddingTop: 48,
        display: 'flex', flexDirection: 'column',
        gap: 36,
        overflow: 'hidden',
      }}>
        {/* Cliente field */}
        <div style={{
          opacity: clienteOpacity,
          transform: `translateY(${(1 - clienteLabelSpring) * 30}px)`,
        }}>
          <div style={labelStyle}>Cliente</div>
          <div style={inputStyle}>
            {clienteText}
            {frame >= 20 && frame <= 68 && <span style={{ color: C.primary }}>{cursor}</span>}
          </div>
        </div>

        {/* Producto field */}
        <div style={{
          opacity: productoOpacity,
          transform: `translateY(${(1 - productoSpring) * 30}px)`,
        }}>
          <div style={labelStyle}>Producto</div>
          <div style={inputStyle}>
            {productoText}
            {frame >= 72 && frame <= 108 && <span style={{ color: C.primary }}>{cursor}</span>}
          </div>
        </div>

        {/* Cantidad row */}
        <div style={{
          opacity: cantidadOpacity,
          transform: `translateY(${(1 - cantidadSpring) * 30}px)`,
          display: 'flex', gap: 20,
        }}>
          <div style={{ flex: 1 }}>
            <div style={labelStyle}>Cantidad</div>
            <div style={{ ...inputStyle, textAlign: 'center' }}>
              {frame >= 100 ? '3' : ''}
            </div>
          </div>
          <div style={{ flex: 2 }}>
            <div style={labelStyle}>Precio unitario</div>
            <div style={inputStyle}>$25.000</div>
          </div>
        </div>

        {/* Total */}
        <div style={{
          opacity: totalOpacity,
          background: C.surface,
          borderRadius: 32,
          padding: '36px 40px',
          border: `1px solid ${C.borderMid}`,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span style={{ fontFamily: F.mono, fontSize: 36, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Total
          </span>
          <span style={{ fontFamily: F.mono, fontSize: 72, fontWeight: 600, color: C.primary, letterSpacing: '-0.02em' }}>
            ${totalVal.toLocaleString('es-CO')}
          </span>
        </div>

        {/* Guardar button */}
        <div style={{
          opacity: btnOpacity,
          transform: `scale(${btnScale})`,
          background: C.primary,
          borderRadius: 24,
          padding: '36px',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          gap: 20,
          cursor: 'pointer',
        }}>
          <svg width="40" height="40" fill="none" viewBox="0 0 24 24" stroke={C.bg} strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span style={{ fontFamily: F.brand, fontSize: 48, fontWeight: 700, color: C.bg }}>
            Guardar Venta
          </span>
        </div>
      </div>

      {/* Success overlay */}
      <div style={{
        position: 'absolute',
        bottom: 0, left: 0, right: 0,
        height: 520,
        background: `linear-gradient(180deg, transparent 0%, ${C.surface} 15%, ${C.surface} 100%)`,
        borderRadius: '40px 40px 0 0',
        border: `1px solid ${C.positiveDim}`,
        borderBottom: 'none',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        gap: 28,
        opacity: successOpacity,
        transform: `translateY(${successY}px)`,
        boxShadow: `0 -24px 80px ${C.positive}18`,
      }}>
        {/* Check circle */}
        <div style={{
          width: 140, height: 140, borderRadius: '50%',
          background: C.positiveDim,
          border: `3px solid ${C.positive}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="70" height="70" fill="none" viewBox="0 0 24 24" stroke={C.positive} strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
        </div>
        <div style={{ fontFamily: F.brand, fontSize: 60, fontWeight: 700, color: C.text, letterSpacing: '-0.02em' }}>
          ¡Venta guardada!
        </div>
        <div style={{ fontFamily: F.mono, fontSize: 30, color: C.muted }}>
          Factura #FV-2024-0012 generada
        </div>
        <div style={{
          background: C.positiveDim,
          border: `1px solid ${C.positive}40`,
          borderRadius: 100,
          padding: '12px 32px',
          fontFamily: F.mono, fontSize: 26, color: C.positive, fontWeight: 600,
        }}>
          La contabilidad se actualizó sola ✓
        </div>
      </div>
    </div>
  );
};
