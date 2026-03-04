# Phase 2: IA Core — Asistente de Costeo y Pricing - Context

**Gathered:** 2026-03-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrar LLM (claude-haiku-4-5, decisión bloqueada Phase 1) en el módulo recetas para dar sugerencias
inteligentes de precio y análisis de márgenes. Sin cambios de schema DB, sin Alembic migrations.
El LLM actúa como "Socia" — asistente conversacional con personalidad definida.

</domain>

<decisions>
## Implementation Decisions

### Persona del asistente — "Socia"
- Nombre: **Socia**
- Género: femenino
- Tono: cálido, profesional, "chévere y buena vibra" — el mejor socio que el emprendedor ha tenido
- Jerga: Cali y el Valle del Cauca — apreciación genuina por la región
- Lenguaje: accesible para cualquier persona sin importar nivel educativo o procedencia
- No corporativo, no frío — habla como una amiga que sabe mucho de negocios

### UI Placement — Modal
- Botón explícito en RecetasPage: "Consultar a Socia" (o similar con ✨ o emoji regional)
- Abre modal — NO tab, NO panel lateral
- El usuario lo invoca cuando quiere; no auto-load al abrir la receta

### Flujo del modal (2 fases)
**Fase 1 — Análisis inicial:**
1. Usuario ingresa (opcional) precio de referencia del mercado/competencia
2. Socia muestra análisis completo estructurado:
   - Precio sugerido con justificación en lenguaje accesible
   - Cuál de los 5 escenarios existentes (mínimo/equilibrio/objetivo/mercado/premium) recomienda y por qué
   - Alertas mixtas: técnicas ("tu margen está al límite") + estratégicas ("en Palmira los fines de semana se vende más")
   - Frase motivacional / cierre cálido al estilo Socia
3. Al final del análisis: **"¿Tienes más preguntas para Socia?"**

**Fase 2 — Chat conversacional (condicional):**
- Solo si el usuario dice SÍ → se abre chat estilo burbujas
- Historial de conversación solo en sesión (React state) — NO persistido en DB
- Al cerrar el modal, el historial se borra
- Backend recibe `messages: list[dict]` para multi-turno (historia completa en cada request)

### Input del usuario al LLM
- Campo: precio de referencia de mercado/competencia (opcional, Decimal)
- Si no lo provee: Socia trabaja solo con el CVU calculado automáticamente del módulo recetas
- El backend extrae automáticamente: CVU, margen_objetivo, escenarios ya calculados, nombre receta, nombre tenant

### Relación con EscenariosPrecios existentes
- La IA NO reemplaza los 5 escenarios matemáticos (EscenariosPrecios.tsx sigue igual)
- Socia explica cuál de los 5 escenarios es el más adecuado y por qué, en lenguaje humano
- Los escenarios son el "mapa matemático" — Socia es la "consejera" que lo interpreta

### Output schema del LLM (Fase 1 — análisis inicial)
```
{
  precio_sugerido: Decimal,           # castear SIEMPRE via Decimal(str(raw))
  margen_esperado: Decimal,           # porcentaje, ej: 45.3
  escenario_recomendado: str,         # nombre del escenario: "Precio objetivo (60%)"
  justificacion: str,                 # en lenguaje accesible, tono Socia
  alertas: list[str],                 # mixtas: técnicas + estratégicas
  mensaje_cierre: str                 # frase cálida al estilo caleño
}
```

### Conversación multi-turno (Fase 2)
- Endpoint acepta `messages: list[{role: str, content: str}]` para historia de conversación
- Primer call: `messages=[]` → análisis estructurado (schema arriba)
- Calls subsiguientes: `messages=[{...history...}, {role: "user", content: pregunta}]` → respuesta libre de Socia
- La respuesta de Fase 2 es texto libre — no schema fijo, Socia responde como en conversación natural

### Decimal safety (crítico — de Phase 1)
- SIEMPRE castear outputs numéricos del LLM: `Decimal(str(raw_value))` en Pydantic
- Nunca almacenar floats del LLM directamente

</decisions>

<specifics>
## Specific Ideas

- "Socia" debe sentirse como el mejor socio que el emprendedor palmireño nunca ha tenido
- Jerga caleña genuina: "bacano", "qué chimba", "hagámosle", "eso es" — sin exagerar, natural
- Apreciación por la región: referencias a negocios locales (velas de Palmira, confites artesanales del Valle)
- Sistema prompt de Socia: incluir que ella conoce el mercado local del Valle del Cauca
- El lenguaje del análisis debe ser comprensible por alguien que nunca estudió contabilidad:
  "Para que no pierdas plata, cobra mínimo $X" en vez de "El precio de equilibrio es $X"

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `servicio_analisis_cvu.py` — `calcular_cvu()`, `generar_escenarios_precio()`: Socia lee estos outputs directamente como contexto
- `EscenariosPrecios.tsx` — ya lista los 5 escenarios; Socia los referencia por nombre en su recomendación
- `PuntoEquilibrioPanel.tsx` — datos CVU completos disponibles en el mismo contexto del modal
- `CalculadoraMargenes.calcular_costo_receta()` — fuente del costo primo que Socia usa como base
- `servicio_almacenamiento.py` — NO requerido para Phase 2 (sin PDFs ni S3)

### Established Patterns
- Arquitectura: `rutas/` solo HTTP, toda lógica LLM en `servicios/servicio_ia_costeo.py`
- React Query para server data — el chat state va en React local state (no React Query, no Zustand)
- Decimal para todo — nunca float en cálculos ni outputs del LLM
- Tenant isolation: `tenant_id` via dependency injection en el endpoint, igual que todos los servicios

### Integration Points
- Endpoint nuevo: `POST /recetas/{id}/asistente-ia` en `backend/app/rutas/recetas.py`
- Servicio nuevo: `backend/app/servicios/servicio_ia_costeo.py`
- Frontend nuevo: `frontend/src/components/recetas/AsistenteCosteoPanel.tsx` (modal + chat)
- Botón en `frontend/src/pages/RecetasPage.tsx` — junto al panel de la receta seleccionada
- Config: `ANTHROPIC_API_KEY` env var en Railway (acción owner previa, bloqueante)

</code_context>

<deferred>
## Deferred Ideas

- R1.2: Generación automática de descripciones de productos — la infraestructura LLM de Phase 2 lo habilita pero es su propia fase; agregar al backlog post-Phase 2
- Persistencia de historial de conversación con Socia en DB — requiere tabla nueva (Phase 4+)
- Número WABA propio por tenant para que Socia contacte directamente — Phase 5+
- Socia como chatbot WhatsApp para clientes finales del tenant — Phase 5+ backlog (R1.4)
- Analytics de uso de Socia (qué preguntas hace el emprendedor) — backlog

</deferred>

---

*Phase: 02-ia-core-asistente-de-costeo-y-pricing*
*Context gathered: 2026-03-04*
