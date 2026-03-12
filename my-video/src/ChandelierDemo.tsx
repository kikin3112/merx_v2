import React from 'react';
import { Series } from 'remotion';
import { SceneHook } from './scenes/SceneHook';
import { SceneDashboard } from './scenes/SceneDashboard';
import { SceneVenta } from './scenes/SceneVenta';
import { SceneProduccion } from './scenes/SceneProduccion';
import { SceneCTA } from './scenes/SceneCTA';
import { SceneDrawer } from './scenes/SceneDrawer';

// ── Frame budget (total = 975f = 32.5s @ 30fps) ──
// Hook(105) + Drawer(60) + Dashboard(155) +
// Drawer(60) + Venta(220) +
// Drawer(60) + Produccion(165) +
// CTA(150) = 975
//
// Timing rationale per scene:
// Hook:       105f — logo (0-40) + tagline (22-62) + 43f hold para leer
// Dashboard:  155f — animaciones completan en ~f127, 28f hold (-1s)
// Venta:      220f — success overlay termina en ~f178, 42f hold
// Produccion: 165f — badge aparece en f108, 57f hold visible
// CTA:        150f — todo visible en ~f85, 65f hold para leer precio y URL
// Drawer:      60f — abierto ~f15-38 = 23 frames (0.77s) para leer módulo

export const ChandelierDemo: React.FC = () => {
  return (
    <Series>
      {/* Scene 0 — Brand hook (3.5s) */}
      <Series.Sequence durationInFrames={105}>
        <SceneHook />
      </Series.Sequence>

      {/* Drawer → Dashboard (2s) */}
      <Series.Sequence durationInFrames={60}>
        <SceneDrawer activeModule="dashboard" />
      </Series.Sequence>

      {/* Scene 1 — Dashboard KPIs (5.17s) */}
      <Series.Sequence durationInFrames={155}>
        <SceneDashboard />
      </Series.Sequence>

      {/* Drawer → Ventas (2s) */}
      <Series.Sequence durationInFrames={60}>
        <SceneDrawer activeModule="ventas" />
      </Series.Sequence>

      {/* Scene 2 — Nueva Venta (7.33s) */}
      <Series.Sequence durationInFrames={220}>
        <SceneVenta />
      </Series.Sequence>

      {/* Drawer → Producción (2s) */}
      <Series.Sequence durationInFrames={60}>
        <SceneDrawer activeModule="produccion" />
      </Series.Sequence>

      {/* Scene 3 — Producción (5.5s) */}
      <Series.Sequence durationInFrames={165}>
        <SceneProduccion />
      </Series.Sequence>

      {/* Scene 4 — CTA (5s) */}
      <Series.Sequence durationInFrames={150}>
        <SceneCTA />
      </Series.Sequence>
    </Series>
  );
};
