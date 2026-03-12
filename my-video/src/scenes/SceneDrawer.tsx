import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, Img, staticFile } from 'remotion';
import { C } from '../tokens';
import { F } from '../fonts';

// ── Nav items (exact paths from dashboard-mobile.html mockup) ──
type NavId = 'dashboard' | 'ventas' | 'pos' | 'produccion' | 'inventario' | 'contabilidad' | 'reportes';

export type NavModule = 'dashboard' | 'ventas' | 'produccion' | null;

const NAV_SECTIONS: { items: { id: NavId; label: string; path: string }[] }[] = [
  {
    items: [
      {
        id: 'dashboard',
        label: 'Dashboard',
        path: 'M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z',
      },
      {
        id: 'ventas',
        label: 'Ventas',
        path: 'M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z',
      },
      {
        id: 'pos',
        label: 'POS',
        path: 'M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z',
      },
    ],
  },
  {
    items: [
      {
        id: 'produccion',
        label: 'Producción',
        path: 'M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1 1 .28 2.798-1.13 2.798H5.43c-1.41 0-2.13-1.798-1.13-2.798L5 14.5',
      },
      {
        id: 'inventario',
        label: 'Inventario',
        path: 'M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z',
      },
    ],
  },
  {
    items: [
      {
        id: 'contabilidad',
        label: 'Contabilidad',
        path: 'M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
      },
      {
        id: 'reportes',
        label: 'Reportes',
        path: 'M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z',
      },
    ],
  },
];

// Flat list for cascade animation indexing
const ALL_ITEMS = NAV_SECTIONS.flatMap((s) => s.items);

interface SceneDrawerProps {
  activeModule: NavModule;
}

// 45 frames (1.5s) — Mobile drawer navigation bridge
export const SceneDrawer: React.FC<SceneDrawerProps> = ({ activeModule }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Drawer in: 0→15 frames ──
  const inProgress = spring({
    frame,
    fps,
    config: { damping: 26, stiffness: 200 },
    durationInFrames: 16,
  });

  // ── Drawer out: starts at frame 38, finishes ~52 ──
  const outProgress = spring({
    frame: frame - 38,
    fps,
    config: { damping: 28, stiffness: 240 },
    durationInFrames: 14,
  });

  const drawerX = (1 - inProgress) * -860 - outProgress * 860;

  // Overlay dim — holds while drawer is open, fades as drawer closes
  const overlayOpacity = interpolate(
    frame,
    [0, 12, 44, 58],
    [0, 0.62, 0.62, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Active item highlight — appears on slide-in, holds during open, fades on slide-out
  const activeGlow = interpolate(
    frame,
    [13, 20, 38, 52],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Active item scale pulse — fires once drawer is fully open
  const activeScale = 1 + interpolate(
    frame,
    [22, 28, 36],
    [0, 0.028, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Cascade glow for null activeModule (all modules moment)
  const cascadeGlow = (i: number) =>
    interpolate(
      frame,
      [10 + i * 3, 14 + i * 3, 28 + i * 3],
      [0, 0.75, 0.5],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    );

  // Header badge pulse
  const ssePulse = interpolate(frame % 60, [0, 30, 59], [1, 0.35, 1]);

  const px = 46;

  return (
    <div style={{
      width: '100%', height: '100%',
      background: C.bg,
      display: 'flex', flexDirection: 'column',
      fontFamily: F.sans,
      position: 'relative', overflow: 'hidden',
    }}>

      {/* ── Header (same as Dashboard / Venta / Produccion) ── */}
      <div style={{
        height: 161, flexShrink: 0,
        background: C.surface,
        borderBottom: `1px solid ${C.border}`,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        paddingLeft: px, paddingRight: px,
        position: 'relative', zIndex: 3,
      }}>
        <Img
          src={staticFile('logo-grande-white.png')}
          style={{ height: 69, objectFit: 'contain' }}
        />
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 12,
          background: C.positiveDim, borderRadius: 9999, padding: '10px 24px',
        }}>
          <div style={{ width: 17, height: 17, borderRadius: '50%', background: C.positive, opacity: ssePulse }} />
          <span style={{ fontFamily: F.mono, fontSize: 28, fontWeight: 500, color: C.positive, letterSpacing: '0.04em' }}>
            En vivo
          </span>
        </div>
      </div>

      {/* ── Content area ── */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>

        {/* App content skeleton (implied content behind the drawer) */}
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column', gap: 28,
          padding: '40px 46px',
          opacity: 0.22,
        }}>
          {[160, 120, 104, 88, 80].map((h, i) => (
            <div key={i} style={{
              height: h, background: C.surface,
              borderRadius: 24, border: `1px solid ${C.border}`,
            }} />
          ))}
        </div>

        {/* Backdrop dim */}
        <div style={{
          position: 'absolute', inset: 0,
          background: `rgba(0,0,0,${overlayOpacity})`,
          zIndex: 1,
        }} />

        {/* ── Drawer panel ── */}
        <div style={{
          position: 'absolute', top: 0, left: 0, bottom: 0,
          width: 840,
          background: C.surface,
          borderRight: `1px solid ${C.borderMid}`,
          transform: `translateX(${drawerX}px)`,
          zIndex: 2,
          display: 'flex', flexDirection: 'column',
          boxShadow: '20px 0 72px rgba(0,0,0,0.55)',
        }}>

          {/* Drawer header — company info */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '40px 48px 36px',
            borderBottom: `1px solid ${C.border}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
              <div style={{
                width: 88, height: 88, borderRadius: 22,
                background: C.primaryDim,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
                <span style={{ fontFamily: F.brand, fontSize: 40, fontWeight: 700, color: C.primary }}>E</span>
              </div>
              <div>
                <div style={{ fontFamily: F.brand, fontSize: 38, fontWeight: 600, color: C.text, lineHeight: 1.2 }}>
                  Emprendedor(a)
                </div>
                <div style={{ fontFamily: F.mono, fontSize: 26, color: C.muted, marginTop: 4 }}>
                  Luz De Luna
                </div>
              </div>
            </div>
            {/* × close icon */}
            <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke={C.muted} strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>

          {/* Nav sections */}
          <div style={{
            flex: 1, overflowY: 'hidden',
            paddingTop: 20, paddingBottom: 20,
          }}>
            {NAV_SECTIONS.map((section, si) => (
              <React.Fragment key={si}>
                {si > 0 && (
                  <div style={{
                    height: 2, background: C.borderMid,
                    marginLeft: 48, marginRight: 48,
                    marginTop: 8, marginBottom: 8,
                  }} />
                )}
                {section.items.map((item, localIdx) => {
                  const flatIdx = ALL_ITEMS.findIndex((a) => a.id === item.id);
                  const isActive = item.id === activeModule;
                  const isCascade = activeModule === null;
                  const itemGlow = isActive
                    ? activeGlow
                    : isCascade
                    ? cascadeGlow(flatIdx)
                    : 0;
                  const hasGlow = itemGlow > 0.05;

                  return (
                    <div key={item.id} style={{ paddingLeft: 28, paddingRight: 28, paddingTop: 4, paddingBottom: 4 }}>
                      <div style={{
                        display: 'flex', alignItems: 'center', gap: 32,
                        padding: '24px 36px',
                        borderRadius: 18,
                        background: hasGlow
                          ? `rgba(255,155,101,${itemGlow * 0.16})`
                          : 'transparent',
                        border: `1px solid ${hasGlow
                          ? `rgba(255,155,101,${itemGlow * 0.42})`
                          : 'transparent'}`,
                        transform: isActive ? `scale(${activeScale})` : 'scale(1)',
                        transformOrigin: 'left center',
                      }}>
                        {/* Icon */}
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none"
                          stroke={hasGlow ? C.primary : C.muted}
                          strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
                          <path d={item.path} />
                        </svg>
                        {/* Label */}
                        <span style={{
                          fontFamily: F.sans,
                          fontSize: 42,
                          fontWeight: isActive ? 600 : 400,
                          color: hasGlow ? C.primary : C.muted,
                          letterSpacing: '-0.01em',
                          flex: 1,
                        }}>
                          {item.label}
                        </span>
                        {/* Active indicator */}
                        {isActive && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                            <div style={{
                              width: 14, height: 14, borderRadius: '50%',
                              background: C.primary,
                              opacity: activeGlow,
                              boxShadow: `0 0 10px ${C.primary}`,
                            }} />
                            <svg width="36" height="36" viewBox="0 0 24 24" fill="none"
                              stroke={C.primary} strokeWidth={2.5}
                              style={{ opacity: activeGlow }}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                            </svg>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </React.Fragment>
            ))}
          </div>

          {/* User footer */}
          <div style={{
            borderTop: `1px solid ${C.border}`,
            padding: '28px 48px',
            display: 'flex', alignItems: 'center', gap: 24,
          }}>
            <div style={{
              width: 80, height: 80, borderRadius: '50%',
              background: C.elevated,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, overflow: 'hidden',
            }}>
              <Img
                src={staticFile('isotipo.png')}
                style={{ width: 80, height: 80, objectFit: 'cover' }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 34, fontWeight: 500, color: C.text, fontFamily: F.sans }}>chandelierp</div>
              <div style={{ fontFamily: F.mono, fontSize: 26, color: C.muted }}>admin</div>
            </div>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke={C.muted} strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
            </svg>
          </div>

        </div>{/* /drawer panel */}
      </div>{/* /content area */}
    </div>
  );
};
