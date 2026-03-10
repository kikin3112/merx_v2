import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, Easing, Img, staticFile } from 'remotion';
import { C } from '../tokens';
import { F } from '../fonts';

// Scale: 1080/375 = 2.88 — all sizes are mockup-px × 2.88
// Canvas: 1080 × 1920. Header: 161px. Content overflow-hidden. Nav absolute bottom.


// Bento cell wrapper
const BentoCell: React.FC<{
  label: string;
  value: string | number;
  delta: string;
  valueColor?: string;
  opacity: number;
  translateY: number;
}> = ({ label, value, delta, valueColor = C.text, opacity, translateY }) => (
  <div style={{
    opacity,
    transform: `translateY(${translateY}px)`,
    background: C.surface,
    border: `1px solid ${C.border}`,
    borderRadius: 32,
    padding: '40px 46px',
    display: 'flex', flexDirection: 'column',
  }}>
    {/* bento-kpi-label */}
    <div style={{
      fontFamily: F.mono, fontSize: 29, color: C.muted,
      textTransform: 'uppercase', letterSpacing: '0.08em',
      marginBottom: 14,
    }}>
      {label}
    </div>
    {/* bento-kpi-val */}
    <div style={{
      fontFamily: F.mono, fontSize: 58, fontWeight: 600,
      letterSpacing: '-0.03em', lineHeight: 1.1,
      color: valueColor,
    }}>
      {value}
    </div>
    {/* bento-kpi-delta */}
    <div style={{
      fontSize: 32, color: C.muted, marginTop: 10, fontFamily: F.sans,
    }}>
      {delta}
    </div>
  </div>
);

// ── Top clientes data ──
const CLIENTES = [
  { rank: 1, name: 'M. Fernanda López', sub: '12 compras', amount: '$3.840.000' },
  { rank: 2, name: 'Artesanías El Dorado', sub: '8 compras', amount: '$2.950.000' },
  { rank: 3, name: 'Tienda Aromatic SAS', sub: '7 compras', amount: '$2.180.000' },
];

// Chart points (from mockup SVG)
const CHART_POINTS = '10,60 40,48 70,55 100,40 130,50 160,30 190,45 220,35 250,28 280,40 310,25 330,30';
const CHART_FILL_POINTS = '10,60 40,48 70,55 100,40 130,50 160,30 190,45 220,35 250,28 280,40 310,25 330,30 330,85 10,85';

// 165 frames (5.5s) — Dashboard fiel al mockup
export const SceneDashboard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Animations ──

  // Header
  const headerOpacity = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: 'clamp' });

  // SSE dot pulse (simulated with frame modulo)
  const ssePulse = interpolate(frame % 60, [0, 30, 59], [1, 0.35, 1]);

  // Action card
  const actionSpring = spring({ frame: frame - 8, fps, config: { damping: 200 }, durationInFrames: 25 });
  const actionOpacity = interpolate(frame, [8, 22], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Bento cells stagger
  const b1Spring = spring({ frame: frame - 22, fps, config: { damping: 200 }, durationInFrames: 28 });
  const b1Opacity = interpolate(frame, [22, 36], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  const b2Spring = spring({ frame: frame - 32, fps, config: { damping: 200 }, durationInFrames: 28 });
  const b2Opacity = interpolate(frame, [32, 46], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  const b3Spring = spring({ frame: frame - 42, fps, config: { damping: 200 }, durationInFrames: 28 });
  const b3Opacity = interpolate(frame, [42, 56], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  const b4Spring = spring({ frame: frame - 52, fps, config: { damping: 200 }, durationInFrames: 28 });
  const b4Opacity = interpolate(frame, [52, 66], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Animated ventas periodo number
  const ventasNum = Math.round(
    interpolate(frame, [22, 75], [0, 18450000], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
      easing: Easing.out(Easing.cubic),
    })
  );
  const ventasStr = ventasNum >= 1000000
    ? `$${(ventasNum / 1000000).toFixed(2)}M`
    : `$${ventasNum.toLocaleString('es-CO')}`;

  // Chart
  const chartOpacity = interpolate(frame, [65, 80], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const chartProgress = interpolate(frame, [72, 130], [0, 340], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.out(Easing.quad),
  });

  // Top clientes
  const clienteOpacity = (start: number) =>
    interpolate(frame, [start, start + 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const clienteX = (start: number) =>
    (1 - spring({ frame: frame - start, fps, config: { damping: 200 }, durationInFrames: 20 })) * -40;

  const px = 46; // horizontal padding (16 × 2.88)

  return (
    <div style={{
      width: '100%', height: '100%',
      background: C.bg,
      display: 'flex', flexDirection: 'column',
      fontFamily: F.sans,
      position: 'relative',
      overflow: 'hidden',
    }}>

      {/* ── Header bar (cv-surface, border-bottom) ── */}
      <div style={{
        height: 161,
        flexShrink: 0,
        background: C.surface,
        borderBottom: `1px solid ${C.border}`,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        paddingLeft: px, paddingRight: px,
        opacity: headerOpacity,
      }}>
        {/* Logo */}
        <Img
          src={staticFile('logo-grande-white.png')}
          style={{ height: 69, objectFit: 'contain' }}
        />

        {/* "En vivo" badge */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 12,
          background: C.positiveDim,
          borderRadius: 9999,
          padding: '10px 24px',
        }}>
          {/* SSE dot */}
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

      {/* ── Scrollable content ── */}
      <div style={{
        flex: 1,
        paddingLeft: px, paddingRight: px,
        paddingTop: 40,
        paddingBottom: 60,
        display: 'flex', flexDirection: 'column',
        gap: 40,
        overflow: 'hidden',
      }}>

        {/* Section label */}
        <div style={{
          fontFamily: F.mono, fontSize: 30, fontWeight: 500,
          color: C.primary,
          textTransform: 'uppercase', letterSpacing: '0.18em',
          opacity: actionOpacity,
        }}>
          Próximas acciones
        </div>

        {/* Action card — border-left negative */}
        <div style={{
          opacity: actionOpacity,
          transform: `translateY(${(1 - actionSpring) * 30}px)`,
          background: C.surface,
          border: `1px solid ${C.border}`,
          borderLeft: `12px solid ${C.negative}`,
          borderRadius: 32,
          padding: '30px 42px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 24,
        }}>
          <span style={{ fontSize: 36, color: C.text, fontFamily: F.sans }}>
            3 ventas por facturar ($4.250.000)
          </span>
          <div style={{
            background: C.negativeDim, color: C.negative,
            borderRadius: 9999, padding: '8px 24px',
            fontFamily: F.mono, fontSize: 28, fontWeight: 500,
            flexShrink: 0,
          }}>
            Facturar
          </div>
        </div>

        {/* KPI Grid 2×2 */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 28,
        }}>
          <BentoCell
            label="Ventas periodo"
            value={ventasStr}
            delta="47 ventas"
            valueColor={C.primary}
            opacity={b1Opacity}
            translateY={(1 - b1Spring) * 36}
          />
          <BentoCell
            label="Ventas hoy"
            value="$1.23M"
            delta="6 ventas"
            valueColor={C.positive}
            opacity={b2Opacity}
            translateY={(1 - b2Spring) * 36}
          />
          <BentoCell
            label="Promedio"
            value="$392k"
            delta="47 ventas"
            valueColor={C.accent}
            opacity={b3Opacity}
            translateY={(1 - b3Spring) * 36}
          />
          <BentoCell
            label="Alertas stock"
            value="4"
            delta="bajo mínimo"
            valueColor={C.negative}
            opacity={b4Opacity}
            translateY={(1 - b4Spring) * 36}
          />
        </div>

        {/* Ventas diarias chart */}
        <div style={{
          opacity: chartOpacity,
          background: C.surface,
          border: `1px solid ${C.border}`,
          borderRadius: 32,
          padding: '40px 46px 32px',
        }}>
          <div style={{ fontSize: 36, fontWeight: 600, color: C.text, marginBottom: 32, fontFamily: F.sans }}>
            Ventas diarias
          </div>
          <svg viewBox="0 0 340 100" width="100%" style={{ display: 'block', height: 248 }}>
            <defs>
              <clipPath id="chartClip">
                <rect x="0" y="0" width={chartProgress} height="100" />
              </clipPath>
              <linearGradient id="mlg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={C.primary} stopOpacity="0.22" />
                <stop offset="100%" stopColor={C.primary} stopOpacity="0.01" />
              </linearGradient>
            </defs>
            {/* Grid lines */}
            <line x1="0" y1="85" x2="340" y2="85" stroke={C.borderMid} strokeDasharray="3 3" />
            <line x1="0" y1="55" x2="340" y2="55" stroke={C.borderMid} strokeDasharray="3 3" />
            <line x1="0" y1="25" x2="340" y2="25" stroke={C.borderMid} strokeDasharray="3 3" />
            {/* X-axis labels */}
            <text x="0"   y="99" fill={C.muted} fontFamily={F.sans} fontSize="8">04 feb</text>
            <text x="105" y="99" fill={C.muted} fontFamily={F.sans} fontSize="8">14 feb</text>
            <text x="213" y="99" fill={C.muted} fontFamily={F.sans} fontSize="8">24 feb</text>
            <text x="294" y="99" fill={C.muted} fontFamily={F.sans} fontSize="8">06 mar</text>
            {/* Animated chart (draws left to right) */}
            <g clipPath="url(#chartClip)">
              <polygon fill="url(#mlg)" points={CHART_FILL_POINTS} />
              <polyline
                fill="none"
                stroke={C.primary}
                strokeWidth="2"
                strokeLinejoin="round"
                strokeLinecap="round"
                points={CHART_POINTS}
              />
            </g>
          </svg>
        </div>

        {/* Top clientes */}
        <div style={{
          background: C.surface,
          border: `1px solid ${C.border}`,
          borderRadius: 32,
          padding: '40px 46px',
        }}>
          <div style={{ fontSize: 36, fontWeight: 600, color: C.text, marginBottom: 32, fontFamily: F.sans }}>
            Top clientes
          </div>
          {CLIENTES.map((c, i) => (
            <div key={c.rank} style={{
              opacity: clienteOpacity(88 + i * 12),
              transform: `translateX(${clienteX(88 + i * 12)}px)`,
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              paddingTop: 20, paddingBottom: 20,
              borderBottom: i < CLIENTES.length - 1 ? `1px solid ${C.border}` : 'none',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
                {/* Rank circle */}
                <div style={{
                  width: 80, height: 80, borderRadius: '50%',
                  background: C.elevated,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                }}>
                  <span style={{ fontFamily: F.mono, fontSize: 30, fontWeight: 600, color: C.primary }}>
                    {c.rank}
                  </span>
                </div>
                <div>
                  <div style={{ fontSize: 34, fontWeight: 500, color: C.text, marginBottom: 4 }}>{c.name}</div>
                  <div style={{ fontFamily: F.mono, fontSize: 28, color: C.muted }}>{c.sub}</div>
                </div>
              </div>
              <div style={{ fontSize: 34, fontWeight: 600, color: C.text }}>{c.amount}</div>
            </div>
          ))}
        </div>

      </div>

    </div>
  );
};
