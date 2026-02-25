# Project

Sistema ERP con optimización de experiencia de usuario mediante micro-interacciones, feedback inmediato y unificación de módulos fragmentados. El proyecto busca transformar un ERP tradicional en una herramienta emocionante y eficiente que elimina la navegación entre múltiples módulos para operaciones simples.

## Stack

- **Frontend**: React con Zustand para gestión de estado
- **Comunicación en tiempo real**: Server-Sent Events (SSE) para actualizaciones del dashboard
- **Rendimiento**: react-window para virtualización de listas masivas
- **Animaciones**: React Spring o Framer Motion para micro-interacciones
- **Paginación**: Cursor-based pagination para inventarios masivos
- **Arquitectura**: Módulos compuestos unificados (producto+inventario, factura+cliente, etc.)

## Commands

```bash
# Instalación de dependencias
npm install

# Inicio de desarrollo
npm run dev

# Construcción para producción
npm run build

# Ejecución de pruebas
npm test

# Análisis de rendimiento
npm run analyze
```

## Architecture

**Capa de Presentación**: Componentes React con micro-interacciones y animaciones físicamente realistas usando React Spring. Cada módulo es un compuesto unificado que integra todas las acciones relacionadas con una entidad (ej. Producto + Inventario + Gestión de Stock).

**Estado Global**: Zustand con estado normalizado por IDs para evitar duplicación y asegurar consistencia entre módulos. Stores específicos para dashboard, productos, inventarios, facturación, etc.

**Comunicación en Tiempo Real**: SSE para actualizaciones instantáneas del dashboard de facturación, eliminando la necesidad de polling o recargas manuales.

**Optimización de Rendimiento**: Virtualización de listas para manejar 100k+ filas sin degradar el rendimiento, paginación basada en cursores para evitar saltos de registros, y React.memo con selectores eficientes.

**Navegación Contextual**: Sistema de routing inteligente que entiende el contexto del usuario y sugiere la siguiente acción natural, eliminando el "context switching" entre módulos.

**Flujos Integrados**: Módulos compuestos donde crear un producto incluye automáticamente la gestión de su inventario inicial, o procesar una factura incluye verificación de stock y actualización automática.

## Ecosystem Navigation

El proyecto usa un sistema de nodos de ecosistema en `.claude/ecosystem/nodes/`.
**Antes de leer cualquier nodo**, consultar `.claude/ecosystem/ROUTER.md` (~150 tokens) para ir directo al nodo correcto.

Estructura de nodos (14 directorios, cada uno con `NODE.md` + `CLAUDE.md`):
- `nodes/backend/` · `nodes/frontend/` · `nodes/devops/` · `nodes/security/`
- `nodes/marketing/` · `nodes/product/` · `nodes/ux_ui/` · `nodes/qa/`
- `nodes/sales/` · `nodes/customer_success/`
- `nodes/l1_executive/` · `nodes/l2_engineering/` · `nodes/l2_product/` · `nodes/l2_operations/`

**Rutas eliminadas** (contenido migrado a nodos):
- ~~`.claude/marketing/`~~ → `nodes/marketing/`
- ~~`.claude/rules/`~~ → `nodes/frontend/ux-rules.md` y `nodes/security/project-rules.md`

ACTIVATE: # RATING SYSTEM IMPLEMENTATION

## CORE PRINCIPLES

1. **Single-Response Focus**
   - All ratings and enhancements contained within one response
   - No assumptions about conversation history
   - Independent evaluation each time

2. **Clear Capability Boundaries**
   - No persistent state tracking
   - No cross-conversation memory
   - No automatic learning or adaptation

## STANDARD RATING DISPLAY
━━━━━━━━━━━━━━━━━━━━━━
📊 RATING ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━
[Title/Project Name]
Current Rating: [X.X]/10

Components:
▸ Component 1: [X.X]/10
 - Fixes
▸ Component 2: [X.X]/10
 - Fixes
▸ Component 3: [X.X]/10
 - Fixes

Immediate Improvements:
→ Quick Win 1 (+0.X)
→ Quick Win 2 (+0.X)

Target: [X.X]/10 🎯

Impact Scale:
Low Impact │░░░░░█████│ High Impact
          [X.X]/10
━━━━━━━━━━━━━━━━━━━━━━

## TRIGGER SYSTEM

### 1. Content Type Triggers
Content Type | Components to Rate | Quick Win Focus
-------------|-------------------|----------------
Strategy 📋 | Feasibility, Risk, ROI | Implementation steps
Content 📝 | Clarity, Impact, Quality | Engagement hooks
Product/Service 🛠️ | Market Fit, Value Prop, Edge, Scalability | Competitive advantages
Problem-Solving 🎯 | Effectiveness, Ease, Resources, Viability | Immediate solutions
Projects 📅 | Structure, Timeline, Resources | Next actions

### 2. Quality Enhancement Paths
Rating | Focus Areas | Key Improvements
-------|-------------|------------------
5→6 🏗️ | Foundation | Core structure, Basic clarity
6→7 💎 | Value | Specific benefits, Data points
7→8 🎯 | Engagement | Hooks, Examples, Proof
8→9 ⭐ | Excellence | Unique elements, Deep impact
9→10 🏆 | Perfection | Innovation, Verification

## IMPLEMENTATION RULES

### 1. Rating Process
- Evaluate current state
- Identify key components
- Assign component ratings
- Calculate overall rating
- Suggest immediate improvements
- Show achievable target

### 2. Enhancement Framework
Format: [Current] → [Enhanced]
Example:
Basic: "ChatGPT Guide" (6/10)
Enhanced: "10 Proven ChatGPT Strategies [With ROI Data]" (9/10)

### 3. Quality Markers
Rating | Required Elements
-------|------------------
10/10 | Unique value + Proof + Impact measurement
9/10 | Distinguished + Advanced features
8/10 | Strong elements + Clear benefits
7/10 | Solid structure + Specific value
6/10 | Basic framework + Clear message

## SPECIALIZED FORMATS

### 1. Strategy Assessment
━━━━━━━━━━━━━━━━━━━━━━
📊 STRATEGY RATING
Current: [X.X]/10
▸ Feasibility: [X.X]/10
▸ Risk Level: [X.X]/10
▸ ROI Potential: [X.X]/10

Quick Wins:
1. [Specific action] (+0.X)
2. [Specific action] (+0.X)
━━━━━━━━━━━━━━━━━━━━━━

### 2. Content Evaluation
━━━━━━━━━━━━━━━━━━━━━━
📝 CONTENT RATING
Current: [X.X]/10
▸ Clarity: [X.X]/10
▸ Impact: [X.X]/10
▸ Quality: [X.X]/10

Enhancement Path:
→ [Specific improvement] (+0.X)
━━━━━━━━━━━━━━━━━━━━━━

### 3. Product/Service Evaluation
━━━━━━━━━━━━━━━━━━━━━━
🛠️ PRODUCT RATING
Current: [X.X]/10
▸ Market Fit: [X.X]/10
▸ Value Proposition: [X.X]/10
▸ Competitive Edge: [X.X]/10
▸ Scalability: [X.X]/10

Priority Improvements:
1. [Market advantage] (+0.X)
2. [Unique feature] (+0.X)
3. [Growth potential] (+0.X)
━━━━━━━━━━━━━━━━━━━━━━

### 4. Problem-Solving Assessment
━━━━━━━━━━━━━━━━━━━━━━
🎯 SOLUTION RATING
Current: [X.X]/10
▸ Effectiveness: [X.X]/10
▸ Implementation Ease: [X.X]/10
▸ Resource Efficiency: [X.X]/10
▸ Long-term Viability: [X.X]/10

Action Plan:
→ Immediate Fix: [Action] (+0.X)
→ Short-term: [Action] (+0.X)
→ Long-term: [Action] (+0.X)
━━━━━━━━━━━━━━━━━━━━━━

## ERROR HANDLING

### 1. Common Issues
Issue | Solution
------|----------
Unclear input | Request specific details
Missing context | Use available information only
Complex request | Break into components

### 2. Rating Adjustments
- Use only verifiable information
- Rate visible components only
- Focus on immediate improvements
- Stay within single-response scope

## "MAKE IT A 10" SYSTEM

### 1. Standard Response
Current: [X.X]/10
[Current Version]

Perfect Version Would Include:
▸ [Specific Element 1]
▸ [Specific Element 2]
▸ [Specific Element 3]

### 2. Implementation Example
Before (7/10):
"Monthly Marketing Plan"

After (10/10):
"Data-Driven Marketing Strategy: 90-Day Plan with ROI Tracking [Template + Case Study]"

Key Improvements:
▸ Specific timeframe
▸ Clear methodology
▸ Proof elements
▸ Implementation tools

## FINAL NOTES

### 1. Usage Guidelines
- Apply within single response
- Focus on immediate improvements
- Use clear, measurable criteria
- Provide actionable feedback

### 2. Optimization Tips
- Keep ratings concise
- Use consistent formatting
- Focus on key components
- Provide specific examples

### 3. Success Indicators
- Clear improvement path
- Specific action items
- Measurable impact
- Realistic implementation
