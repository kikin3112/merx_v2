# Plan Maestro de Modernización Frontend: chandelierp V2 Full-Responsive

**Fecha:** 14 de Febrero de 2026
**Estado:** Borrador de Planificación
**Versión:** 1.1

## 1. Resumen Ejecutivo

El objetivo es transformar la interfaz de chandelierp V2 (actualmente optimizada para escritorio) en una experiencia **Full-Responsive** de clase mundial, priorizando la ergonomía móvil ("Thumb-Driven Design") sin sacrificar la densidad de información requerida en escritorio.

> [!IMPORTANT]
> **PRINCIPIO DE NO REGRESIÓN (ZERO-BREAK POLICY):**
> La implementación de este plan **NO DEBE ALTERAR NI ROMPER** ninguna funcionalidad existente del sistema. El comportamiento actual en escritorio debe preservarse intacto, y las nuevas funcionalidades responsivas deben ser aditivas o adaptativas sin efectos colaterales destructivos. Todo flujo de negocio (ventas, facturación, etc.) debe mantener su integridad lógica y operativa al 100%.

Se aprovechará el stack moderno ya existente (**React 19 + Tailwind CSS 4**) para implementar patrones de diseño de vanguardia (State of the Art 2025), asegurando que el sistema sea utilizable cómodamente en dispositivos desde 360px de ancho hasta pantallas 4K.

## 2. Diagnóstico del Estado Actual

| Componente | Estado Actual | Problema en Móvil |
| :--- | :--- | :--- |
| **Layout (AppShell)** | Flexbox fijo con Sidebar de 240px | La sidebar ocupa el 70-80% de una pantalla móvil. No colapsa. |
| **Navegación** | Lista vertical estática | Inaccesible con una sola mano. Oculta contenido principal. |
| **Tablas (DocumentDetail)** | `<table>` estándar HTML | Requiere scroll horizontal excesivo. Filas difíciles de leer/tocar. |
| **Modales** | Centrados, ancho fijo | Se salen de la pantalla, botones de cierre difíciles de alcanzar. |
| **Inputs** | Tamaño estándar (~38px) | Muy pequeños para dedos (touch target < 44px). |

## 3. Estándares de UX/UI Modernos (Q4 2025)

Basado en las mejores prácticas actuales:

1.  **Zona del Pulgar (Thumb Zone):** En móviles, la navegación y acciones principales deben estar en el tercio inferior de la pantalla.
2.  **Navegación Adaptativa:**
    *   **Escritorio:** Sidebar lateral expandida (comportamiento original preservado).
    *   **Tablet:** Sidebar colapsada (iconos).
    *   **Móvil:** Bottom Navigation Bar (Barra inferior) para vistas principales + Drawer para menú completo.
3.  **Tipografía Fluida:** Uso de `clamp()` para escalar textos suavemente entre dispositivos, asegurando legibilidad sin saltos bruscos.
4.  **Touch Targets:** Mínimo **44x44px** para cualquier elemento interactivo. Espaciado seguro de 8px entre elementos.
5.  **Data Densification:**
    *   **Escritorio:** Tablas densas ricas en datos.
    *   **Móvil:** Transformación a "Tarjetas de Datos" (Card View) o listas con disclosure progresivo.

## 4. Estrategia de Implementación

### Fase 1: Fundamentos y Layout (Core)
*Objetivo: Que la aplicación "quepa" en el móvil y sea navegable sin afectar escritorio.*

1.  **Refactor de `AppShell`:**
    *   Implementar un **Layout Context** para manejar el estado de la UI (mobile menu open, sidebar collapsed).
    *   Crear componente `ResponsiveNavigation`.
    *   **Móvil:** Renderizar `BottomTabBar` (fija abajo) con las 4-5 acciones más comunes (Dashboard, Ventas, POS, Menú).
    *   **Escritorio:** Mantener `Sidebar` pero hacerla "Collapsible" (plegable).

2.  **Configuración de Tailwind 4:**
    *   Definir breakpoints semánticos si los default no son suficientes (ej. `xs: 475px` para móviles grandes modernos).
    *   Configurar variables CSS para alturas de áreas seguras (notch de iPhone, barra de navegación Android).

### Fase 2: Componentes Críticos (Tablas y Formularios)
*Objetivo: Que los datos sean legibles y editables.*

1.  **Patrón `ResponsiveTable`:**
    *   Crear un componente HOC (Higher Order Component) o wrapper que:
        *   En `md` y superior: Renderiza la `<table>` normal (idéntica a la actual).
        *   En `sm` e inferior: Renderiza una lista de `<DataCard>` donde cada fila es una tarjeta.
    *   Implementar "Sticky Actions": Los botones de editar/borrar deben estar siempre visibles o accesibles via "Swipe" o menú de 3 puntos.

2.  **Formularios Ergonómicos:**
    *   **Input Mode:** Asegurar `inputmode="decimal"` en precios y cantidades para abrir el teclado numérico correcto.
    *   **Label Placement:** Mover labels encima de los inputs en móvil (block) vs al lado en escritorio (inline-grid).
    *   **Botones de Acción:** Mover botones de "Guardar/Cancelar" al final de la pantalla (sticky bottom) en móviles para fácil acceso.

### Fase 3: Detalle y Documentos (El componente `DocumentDetail`)
*Objetivo: Manejar la complejidad de Facturas/Ventas.*

1.  **Transformación del Modal:**
    *   En móvil, el modal debe convertirse en una **Full Screen Sheet** (Hoja de pantalla completa) que desliza desde abajo.
    *   Botón "Cerrar" grande y accesible.

2.  **Grid de Productos (Detalle de Venta):**
    *   No usar tabla para las líneas de productos en móvil.
    *   Usar lista de items con controles +/- grandes para cantidad.
    *   Mover el "Buscador de productos" a un overlay dedicado.

### Fase 4: Polish & Performance (PWA Lite)
*Objetivo: Sensación nativa.*

1.  **View Transitions:** Utilizar la API de View Transitions de React Router 7 para que los cambios de página se sientan como una app nativa (slide left/right).
2.  **Feedback Háptico/Visual:** Estados `active` claros en botones para confirmar el toque instantáneamente.
3.  **Scroll Snapping:** Para listas horizontales (si las hay).

## 5. Hoja de Ruta Técnica (Roadmap)

### Semana 1: Layout & Nav
- [ ] Crear `useIsMobile` hook (usando `window.matchMedia`).
- [ ] Refactorizar `AppShell.tsx` para soportar renderizado condicional de Nav.
- [ ] Crear componente `BottomNav` con iconos Heroicons.
- [ ] Ajustar padding del `main` content para no quedar oculto tras la BottomNav.
- [ ] **Validación:** Verificar que el layout de escritorio es pixel-perfect idéntico al original.

### Semana 2: Sistema de Tablas
- [ ] Crear componente `CardList` para móviles.
- [ ] Refactorizar `VentasPage`, `TercerosPage` para usar un patrón compuesto `ResponsiveList`.
    *   *Concepto:* `<ResponsiveList desktop={<Table ... />} mobile={<CardList ... />} />`

### Semana 3: Operaciones Complejas
- [ ] Refactorizar `DocumentDetail` para ser `Dialog` en Desktop y `Drawer/Sheet` en Móvil.
- [ ] Rediseñar la edición de líneas de venta para toque (botones grandes, menos inputs de texto libre).

### Semana 4: CRM & Dashboard
- [ ] Ajustar gráficas de Recharts para ser responsivas (width 100%).
- [ ] Pipeline de CRM: Cambiar de columnas horizontales a pestañas o acordeón vertical en móvil.

## 6. Recomendación de Arquitectura de CSS (Tailwind)

Se recomienda encarecidamente usar **Container Queries** (ya nativas en Tailwind 4) para componentes aislados.

```css
@container (min-width: 400px) {
  .product-card {
    display: grid;
    /* ... */
  }
}
```

Esto permite que una tarjeta de producto se vea bien tanto en el Dashboard (espacio pequeño) como en una lista de pantalla completa, sin depender del ancho total de la ventana.
