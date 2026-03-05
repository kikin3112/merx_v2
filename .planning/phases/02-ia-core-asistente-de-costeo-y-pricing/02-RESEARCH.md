# Phase 2: IA Core — Asistente de Costeo y Pricing - Research

**Researched:** 2026-03-04
**Domain:** Anthropic claude-haiku-4-5 integration via Python SDK, FastAPI async service, React modal chat UI
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **LLM Provider:** claude-haiku-4-5 via Anthropic API — LOCKED from Phase 1 (vendor consolidation, $0.83/mes a 150K req)
- **Persona:** "Socia" — femenina, cálida, caleña, habla como amiga que sabe mucho de negocios, no corporativa
- **UI Placement:** Modal — botón explícito "Consultar a Socia" en RecetasPage. NO tab, NO panel lateral
- **DB persistence:** NINGUNA — historial de conversación solo en React local state; al cerrar modal se borra
- **Output schema Fase 1:**
  ```
  {
    precio_sugerido: Decimal,
    margen_esperado: Decimal,
    escenario_recomendado: str,
    justificacion: str,
    alertas: list[str],
    mensaje_cierre: str
  }
  ```
- **Decimal safety:** SIEMPRE castear outputs numéricos del LLM via `Decimal(str(raw_value))` en Pydantic
- **Multi-turno:** Endpoint acepta `messages: list[{role, content}]`. Fase 1 = `messages=[]`, Fase 2 = historial completo

### Claude's Discretion

- Diseño exacto del system prompt de Socia (tono, ejemplos de jerga caleña, estructura del prompt)
- Estrategia de prompt caching (cuáles tokens son cacheable)
- Gestión de errores LLM (timeouts, API failures, fallback UI)
- Test coverage para el servicio LLM (mocking de Anthropic SDK)
- Estructura interna de `servicio_ia_costeo.py`

### Deferred Ideas (OUT OF SCOPE)

- R1.2: Generación automática de descripciones de productos (backlog post-Phase 2)
- Persistencia de historial de conversación en DB (Phase 4+)
- Número WABA propio por tenant para que Socia contacte directamente (Phase 5+)
- Socia como chatbot WhatsApp para clientes finales del tenant (Phase 5+, R1.4)
- Analytics de uso de Socia (backlog)

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| R1.1 | Asistente de costeo IA: sugerencias de precio basadas en márgenes y mercado | anthropic SDK `tool_use` para structured output, `ServicioAnalisisCVU.generar_escenarios_precio()` como fuente de datos, modal React con 2 fases (análisis + chat) |

</phase_requirements>

---

## Summary

Phase 2 integra `claude-haiku-4-5` via Anthropic Python SDK dentro del módulo de recetas existente. El backend crea `servicio_ia_costeo.py` que orquesta el LLM leyendo los datos del CVU y escenarios de precio calculados por los servicios existentes, los serializa en el system prompt, y llama a la API de Anthropic con `tool_use` para garantizar structured output. No se requieren migraciones de DB, no se toca `modelos.py`.

El frontend añade un botón "Consultar a Socia" en la tab de análisis de `RecetasPage`, que abre un modal en dos fases: Fase 1 muestra el análisis estructurado con schema fijo (una sola llamada POST); Fase 2 condicional activa chat de burbujas con historial en React local state que se envía completo en cada request. El historial se destruye al cerrar el modal.

El riesgo técnico principal es la Decimal safety: el LLM devuelve números como strings o floats en JSON. El patrón Pydantic `Decimal(str(raw))` es el único mecanismo de defensa y debe aplicarse en TODOS los campos numéricos del response.

**Primary recommendation:** Implementar `servicio_ia_costeo.py` con Anthropic `tool_use` + prompt caching del system prompt. El modal React sigue el patrón de modales existentes en RecetasPage (misma estructura CSS con `fixed inset-0 z-50`).

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | >=0.40.0 | Anthropic Python SDK — llamadas LLM | Vendor bloqueado Phase 1; `tool_use` nativo para structured output |
| fastapi | >=0.128.0 | HTTP layer — endpoint nuevo | Ya en el stack; no hay alternativa |
| pydantic v2 | >=2.12.5 | Validacion output LLM + Decimal casting | Ya en el stack; unico mecanismo Decimal-safe confiable |
| ServicioAnalisisCVU | (interno) | Fuente de datos CVU, escenarios, cvu | Ya operacional en produccion — reutilizar directamente |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | >=0.27.0 | Client HTTP async (ya instalado) | Anthropic SDK lo usa internamente en async mode |
| React local state | (React 18) | Historial de conversacion Fase 2 | Decisión bloqueada: NO React Query, NO Zustand para chat state |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| anthropic tool_use | JSON mode via system prompt | tool_use garantiza schema; JSON mode puede fallar con modelos menores |
| React local state for chat | Zustand | Zustand sobra — el estado muere con el modal; local state es correcto |

### Installation

```bash
# Backend — agregar a pyproject.toml dependencies y correr:
uv add anthropic
# O editar pyproject.toml directamente y correr: uv sync
```

**CRITICO:** `anthropic` NO esta en `pyproject.toml` ni en `requirements.txt`. Es el primer paso obligatorio de Wave 0.

---

## Architecture Patterns

### Recommended Project Structure

```
backend/app/servicios/
├── servicio_ia_costeo.py        # NUEVO — orquestacion LLM Socia
├── servicio_analisis_cvu.py     # EXISTENTE — fuente de datos CVU/escenarios
└── [otros servicios existentes]

backend/app/rutas/
└── recetas.py                   # MODIFICAR — agregar endpoint POST /{id}/asistente-ia

frontend/src/components/recetas/
├── AsistenteCosteoPanel.tsx     # NUEVO — modal 2 fases + chat
└── [componentes existentes]

frontend/src/pages/
└── RecetasPage.tsx              # MODIFICAR — boton + state para modal
```

### Pattern 1: Anthropic tool_use para Structured Output (Fase 1)

**What:** Definir un "tool" en Anthropic API que actua como schema de respuesta obligatorio. El modelo DEBE invocar el tool para responder — garantiza JSON con los campos esperados.
**When to use:** Siempre en Fase 1 (analisis inicial). No usar en Fase 2 (respuesta libre de chat).

```python
# Source: Anthropic official docs — tool_use for structured output
import anthropic
from decimal import Decimal

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SOCIA_TOOL = {
    "name": "analisis_costeo",
    "description": "Analisis estructurado de precio y margen para la receta",
    "input_schema": {
        "type": "object",
        "properties": {
            "precio_sugerido": {"type": "number", "description": "Precio sugerido en COP"},
            "margen_esperado": {"type": "number", "description": "Margen esperado porcentaje"},
            "escenario_recomendado": {"type": "string"},
            "justificacion": {"type": "string"},
            "alertas": {"type": "array", "items": {"type": "string"}},
            "mensaje_cierre": {"type": "string"},
        },
        "required": ["precio_sugerido", "margen_esperado", "escenario_recomendado",
                     "justificacion", "alertas", "mensaje_cierre"],
    },
}

response = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=1024,
    tools=[SOCIA_TOOL],
    tool_choice={"type": "tool", "name": "analisis_costeo"},  # fuerza el tool
    system=[{
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},  # prompt caching
    }],
    messages=user_messages,
)

# Extraer tool_use block
tool_block = next(b for b in response.content if b.type == "tool_use")
raw = tool_block.input  # dict con los campos
```

### Pattern 2: Decimal Safety en Pydantic (CRITICO)

**What:** El LLM devuelve numeros como floats en JSON. Pydantic v2 con `Decimal` necesita coercion explicita.
**When to use:** En TODOS los campos numericos del response schema del LLM.

```python
# Source: Anthropic DECISIONS.md Phase 1 — Decimal corruption pitfall
from decimal import Decimal
from pydantic import BaseModel, field_validator

class SociaAnalisisResponse(BaseModel):
    precio_sugerido: Decimal
    margen_esperado: Decimal
    escenario_recomendado: str
    justificacion: str
    alertas: list[str]
    mensaje_cierre: str

    @field_validator("precio_sugerido", "margen_esperado", mode="before")
    @classmethod
    def cast_decimal(cls, v):
        return Decimal(str(v))  # str() primero para evitar float precision loss
```

### Pattern 3: Prompt Caching del System Prompt

**What:** El system prompt de Socia (~500 tokens) se cachea con `cache_control: {"type": "ephemeral"}`. Los tokens en cache cuestan 0.1x el precio base.
**When to use:** Siempre — el system prompt no cambia entre requests del mismo tenant.

```python
# Source: Anthropic prompt caching docs
system=[{
    "type": "text",
    "text": build_system_prompt(receta_context),
    "cache_control": {"type": "ephemeral"},
}]
# Minimo 1024 tokens para activar cache en Haiku
# El context de receta (nombre, CVU, escenarios) se embebe en el system prompt
```

### Pattern 4: Multi-turno Fase 2 (chat conversacional)

**What:** Fase 2 recibe el historial completo de mensajes en cada request. El backend lo pasa directamente a Anthropic sin modificar. Sin tool_use — respuesta libre de Socia.
**When to use:** Solo si el usuario hace clic en "Tengo mas preguntas para Socia".

```python
# Fase 2: messages llega con historial previo
async def consultar_socia(
    receta_id: UUID,
    request: AsistenteCosteoRequest,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    if not request.messages:  # Fase 1
        return await servicio.analisis_inicial(receta_id, request.precio_referencia)
    else:  # Fase 2
        return await servicio.chat_libre(receta_id, request.messages)
```

### Pattern 5: Modal React — estructura existente en RecetasPage

**What:** RecetasPage ya tiene 3 modales con el patron `fixed inset-0 z-50`. Seguir exactamente el mismo patron CSS.
**When to use:** Para AsistenteCosteoPanel — NO inventar nueva estructura de modal.

```tsx
// Patron existente en RecetasPage.tsx — replicar exactamente
{showSocia && selectedReceta && (
  <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/50">
    <div className="bg-white w-full h-full md:h-auto md:rounded-xl shadow-xl md:max-w-lg md:mx-4 flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <h2 className="text-lg font-semibold text-gray-900">✨ Socia</h2>
        <button onClick={() => { setShowSocia(false); setChatHistory([]); }}
          className="p-2 -mr-1 text-gray-400 hover:text-gray-600 text-xl">&times;</button>
      </div>
      <AsistenteCosteoPanel recetaId={selectedReceta.id} onClose={() => setShowSocia(false)} />
    </div>
  </div>
)}
```

### Pattern 6: Frontend API endpoint en endpoints.ts

**What:** El patron de los endpoints existentes usa `client.post()` con tipado. Agregar endpoint de Socia siguiendo exactamente el mismo patron.

```typescript
// Agregar en endpoints.ts junto a los otros de recetas
export const recetas = {
  // ... endpoints existentes ...
  consultarSocia: (id: string, data: { precio_referencia?: number; messages?: ChatMessage[] }) =>
    client.post<SociaAnalisisResponse | SociaChatResponse>(`/recetas/${id}/asistente-ia`, data),
};
```

### Anti-Patterns to Avoid

- **Float storage del LLM:** `precio = response["precio_sugerido"]` sin `Decimal(str(...))` — corrupcion de datos financieros
- **tool_choice ausente en Fase 1:** Sin `tool_choice: {"type": "tool", "name": "analisis_costeo"}` el modelo puede responder con texto libre en vez del tool
- **System prompt sin cache_control:** Cada request recarga el system prompt completo — costo 10x mayor
- **Chat history en Zustand:** El historial de chat muere con el modal — no necesita estado global
- **Llamada LLM en la ruta (rutas/):** Toda logica LLM va en `servicio_ia_costeo.py`, la ruta solo parsea HTTP
- **messages=None vs messages=[]:** Distinguir Fase 1 (`messages` ausente o vacio) de Fase 2 (`messages` con historia)

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Structured LLM output | JSON parsing con regex o split | `tool_use` de Anthropic con schema | tool_use garantiza tipos; regex falla con variaciones del modelo |
| Decimal casting | Conversion manual post-hoc | Pydantic `field_validator` con `Decimal(str(v))` | El validator corre automaticamente en cada instanciacion |
| Prompt template con datos financieros | f-string cruda | `build_system_prompt(context: dict)` function con Decimal-to-str serialization explicita | Evita que Decimal no-serializable rompa el string interpolation |
| Multiturn message history | DB table de mensajes | React local state + `messages: list[dict]` en request body | Decision bloqueada en CONTEXT.md; la infra DB es Phase 4+ |
| LLM retry logic | Bucle while custom | `anthropic` SDK maneja reintentos automaticos con backoff | El SDK tiene `max_retries=2` por defecto |

**Key insight:** Anthropic `tool_use` es el mecanismo de structured output mas robusto disponible para claude-haiku-4-5. No existe JSON mode equivalente en Anthropic; `tool_use` + `tool_choice: forced` es el patron oficial.

---

## Common Pitfalls

### Pitfall 1: Decimal Corruption desde LLM

**What goes wrong:** `response.content[0].input["precio_sugerido"]` es un float Python (ej: `13001.34000001`). Si se almacena directamente como `Decimal(13001.34)` se propaga el error de precision del float.
**Why it happens:** JSON deserializa numeros como float por defecto. `Decimal(float)` hereda el error de representacion binaria.
**How to avoid:** `Decimal(str(raw_value))` — el string representation del float es correcto para valores monetarios tipicos. En Pydantic: `field_validator(..., mode="before")` que hace `return Decimal(str(v))`.
**Warning signs:** `precio_sugerido` con mas de 2 decimales inesperados en la respuesta serializada.

### Pitfall 2: anthropic SDK no en pyproject.toml

**What goes wrong:** `import anthropic` falla en produccion con `ModuleNotFoundError`. El SDK NO esta instalado (verificado en `pyproject.toml` — no aparece en dependencies).
**Why it happens:** Phase 1 decidio el proveedor pero no instalo el SDK.
**How to avoid:** Wave 0 DEBE agregar `anthropic>=0.40.0` a `pyproject.toml` y correr `uv sync` antes de cualquier codigo LLM.
**Warning signs:** Railway deploy con `ImportError: No module named 'anthropic'`.

### Pitfall 3: ANTHROPIC_API_KEY ausente en Railway

**What goes wrong:** El servicio arranca localmente (con `.env`) pero falla en produccion con `anthropic.AuthenticationError`.
**Why it happens:** `config.py` no tiene `ANTHROPIC_API_KEY` como campo declarado — `extra="ignore"` lo ignora silenciosamente.
**How to avoid:** (1) Agregar `ANTHROPIC_API_KEY: Optional[str]` a `Settings` en `config.py`. (2) Agregar la key en Railway env vars ANTES de deploy. (3) El servicio debe verificar que la key exista al inicializarse.
**Warning signs:** HTTP 500 en produccion, logs con `AuthenticationError` o `None` value para la key.

### Pitfall 4: tool_use sin tool_choice forced

**What goes wrong:** claude-haiku-4-5 ocasionalmente responde con texto libre en vez de invocar el tool, rompiendo el parsing del response.
**Why it happens:** Sin `tool_choice={"type": "tool", "name": "analisis_costeo"}` el modelo tiene libertad de elegir si usa el tool.
**How to avoid:** Siempre incluir `tool_choice={"type": "tool", "name": "..."}` en llamadas de Fase 1. Solo omitirlo en Fase 2 (chat libre sin tool).
**Warning signs:** `response.content[0].type == "text"` cuando se espera `"tool_use"` — el parsing falla con AttributeError.

### Pitfall 5: System Prompt con datos financieros no serializables

**What goes wrong:** `f"El CVU es {cvu}"` falla si `cvu` es `Decimal` — `Decimal` no es JSON-serializable y puede incluir representaciones inesperadas en f-strings.
**Why it happens:** `str(Decimal("13001.34"))` funciona, pero accidentalmente pasando el objeto Decimal directamente puede causar comportamientos inesperados.
**How to avoid:** En `build_system_prompt()`, convertir todos los Decimal a `str()` o `float()` ANTES de construir el prompt. Usar formato legible: `f"${float(cvu):,.0f} COP"`.
**Warning signs:** Prompt con representaciones tipo `Decimal('13001.34')` en texto visible.

### Pitfall 6: Modal sin cleanup del chat state al cerrar

**What goes wrong:** El usuario cierra y reabre el modal — ve el historial de chat anterior. La decision bloqueada es que el historial se borra al cerrar.
**Why it happens:** Si `chatHistory` state esta en RecetasPage, el componente no se desmonta al cerrar el modal.
**How to avoid:** En el handler `onClose`, resetear explicitamente `setChatHistory([])` y `setFase1Response(null)`. Alternativamente, usar `key={selectedReceta.id}` en el componente del modal para forzar remount.
**Warning signs:** El usuario ve conversaciones previas al abrir el modal por segunda vez.

---

## Code Examples

### Backend: Estructura de servicio_ia_costeo.py

```python
# Source: Patron de servicios existente en backend/app/servicios/
from anthropic import Anthropic
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from ..config import settings
from ..servicios.servicio_analisis_cvu import ServicioAnalisisCVU
from ..servicios.servicio_costos_indirectos import ServicioCostosIndirectos

class ServicioIACosteo:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self._client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._cvu_svc = ServicioAnalisisCVU(db=db, tenant_id=tenant_id)
        self._indirectos_svc = ServicioCostosIndirectos(db=db, tenant_id=tenant_id)

    def _build_context(self, receta_id: UUID, precio_referencia=None) -> dict:
        """Recopila datos financieros de la receta para el system prompt."""
        # Usar servicios existentes — NO duplicar logica
        escenarios = self._cvu_svc.generar_escenarios_precio(
            receta_id=receta_id,
            costos_fijos=self._get_costos_fijos(receta_id),
            volumen=self._get_volumen(receta_id),
            precio_mercado_referencia=precio_referencia,
        )
        return escenarios  # dict con receta_nombre, costo_variable_unitario, escenarios[]

    async def analisis_inicial(self, receta_id: UUID, precio_referencia=None) -> dict:
        """Fase 1 — analisis estructurado con tool_use."""
        context = self._build_context(receta_id, precio_referencia)
        # ... llamada Anthropic con tool_use ...

    async def chat_libre(self, receta_id: UUID, messages: list[dict]) -> dict:
        """Fase 2 — respuesta conversacional libre."""
        context = self._build_context(receta_id)
        # ... llamada Anthropic sin tool_use, texto libre ...
```

### Backend: Endpoint en recetas.py

```python
# Source: Patron de rutas existente en backend/app/rutas/recetas.py
from ..servicios.servicio_ia_costeo import ServicioIACosteo

class AsistenteCosteoRequest(BaseModel):
    precio_referencia: Optional[Decimal] = None
    messages: list[dict] = []  # [] = Fase 1, con historia = Fase 2

@router.post("/{receta_id}/asistente-ia")
async def consultar_socia(
    receta_id: UUID,
    request: AsistenteCosteoRequest,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """Consulta a Socia — analisis inicial o chat conversacional."""
    servicio = ServicioIACosteo(db=db, tenant_id=ctx.tenant_id)
    try:
        if not request.messages:
            return await servicio.analisis_inicial(receta_id, request.precio_referencia)
        else:
            return await servicio.chat_libre(receta_id, request.messages)
    except Exception as e:
        logger.error("Error en asistente-ia", exc_info=e)
        raise HTTPException(status_code=500, detail="Socia no pudo responder en este momento")
```

### Frontend: AsistenteCosteoPanel — estructura de 2 fases

```tsx
// Source: patron modal existente en RecetasPage.tsx
interface Props { recetaId: string; onClose: () => void; }

export function AsistenteCosteoPanel({ recetaId, onClose }: Props) {
  const [fase, setFase] = useState<'inicial' | 'chat'>('inicial');
  const [analisis, setAnalisis] = useState<SociaAnalisisResponse | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [userInput, setUserInput] = useState('');

  const sociaMutation = useMutation({
    mutationFn: (data: { precio_referencia?: number; messages?: ChatMessage[] }) =>
      recetas.consultarSocia(recetaId, data),
    onSuccess: ({ data }) => {
      if (fase === 'inicial') setAnalisis(data as SociaAnalisisResponse);
      else {
        setChatHistory(prev => [...prev, { role: 'assistant', content: data.respuesta }]);
      }
    },
  });

  // Fase 1 se dispara automaticamente al montar el componente
  useEffect(() => {
    sociaMutation.mutate({});
  }, []);

  // Fase 2: enviar mensaje con historial completo
  function handleSendMessage() {
    const newMsg = { role: 'user' as const, content: userInput };
    const updatedHistory = [...chatHistory, newMsg];
    setChatHistory(updatedHistory);
    setUserInput('');
    sociaMutation.mutate({ messages: updatedHistory });
  }
  // ... render condicional Fase 1 / Fase 2
}
```

### Frontend: Agregar boton en RecetasPage

```tsx
// En el bloque donde se muestra selectedReceta en tab 'analisis'
// Junto a EscenariosPrecios — boton contextual cuando hay receta seleccionada
<button
  onClick={() => setShowSocia(true)}
  className="w-full py-3 px-4 bg-gradient-to-r from-amber-400 to-amber-500 text-white font-semibold rounded-xl hover:from-amber-500 hover:to-amber-600 transition-all shadow-sm flex items-center justify-center gap-2"
>
  ✨ Consultar a Socia
</button>
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| JSON mode via system prompt | `tool_use` + `tool_choice: forced` | claude-haiku-4-5 release | Garantiza schema, elimina parsing manual |
| Prompt caching inexistente | `cache_control: ephemeral` en messages array | Anthropic 2024 | Reduce costo hasta 90% en tokens de sistema |
| Streaming para UX | Respuesta completa (non-streaming) | N/A para este caso | El modal de Socia muestra analisis completo — streaming innecesario en Fase 1 |

**Deprecated/outdated:**
- `anthropic.Completion` API: reemplazada por `anthropic.messages.create` — usar solo la Messages API.
- `functions` parameter: solo existe en OpenAI; en Anthropic usar `tools` + `tool_choice`.

---

## Open Questions

1. **Async vs sync Anthropic client**
   - What we know: El SDK de Anthropic tiene `AsyncAnthropic` para llamadas async. FastAPI usa `async def` para endpoints.
   - What's unclear: Si `ServicioIACosteo` debe usar `AsyncAnthropic` o `Anthropic` sync (ambos funcionan en FastAPI, pero el async client evita bloquear el event loop).
   - Recommendation: Usar `AsyncAnthropic` y `await client.messages.create(...)`. Si el servicio es instanciado por request (patron del codebase), el client puede ser instanciado por request sin overhead significativo.

2. **Costos fijos y volumen para contexto del LLM**
   - What we know: `generar_escenarios_precio()` requiere `costos_fijos` y `volumen`. Estos vienen de los costos indirectos del tenant y de `produccion_mensual_esperada` de la receta.
   - What's unclear: Si el endpoint de Socia debe aceptar estos parametros del frontend o calcularlos autonomamente en el backend.
   - Recommendation: El backend los calcula autonomamente via `ServicioCostosIndirectos` y `receta.produccion_mensual_esperada` — el usuario no los ingresa manualmente. Socia trabaja con los datos ya calculados.

3. **config.py requiere ANTHROPIC_API_KEY field**
   - What we know: `config.py` usa `extra="ignore"` — variables no declaradas son ignoradas silenciosamente.
   - What's unclear: Si agregar `ANTHROPIC_API_KEY: Optional[str] = None` a `Settings` o leer la env var directamente con `os.environ.get`.
   - Recommendation: Agregar campo a `Settings` con validacion que falle en produccion si no esta set cuando el servicio LLM es invocado. Consistente con el patron de todas las otras credenciales del sistema.

---

## Validation Architecture

Config.json no existe — tratar nyquist_validation como habilitado.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.4+ (ya configurado en pyproject.toml) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest backend/tests/test_ia_costeo.py -x -v` |
| Full suite command | `uv run pytest backend/tests/ -v --tb=short` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| R1.1 | Endpoint POST /recetas/{id}/asistente-ia retorna schema correcto | unit (mock SDK) | `uv run pytest backend/tests/test_ia_costeo.py::test_analisis_inicial -x` | Wave 0 |
| R1.1 | Decimal casting del output LLM — sin floats | unit | `uv run pytest backend/tests/test_ia_costeo.py::test_decimal_safety -x` | Wave 0 |
| R1.1 | Fase 2 acepta messages y retorna respuesta libre | unit (mock SDK) | `uv run pytest backend/tests/test_ia_costeo.py::test_chat_fase2 -x` | Wave 0 |
| R1.1 | Tenant isolation — receta de otro tenant retorna 404 | unit | `uv run pytest backend/tests/test_ia_costeo.py::test_tenant_isolation -x` | Wave 0 |
| R1.1 | Frontend modal abre/cierra correctamente | manual | N/A | manual-only |
| R1.1 | Historial chat se destruye al cerrar modal | manual | N/A | manual-only |

### Sampling Rate

- **Per task commit:** `uv run pytest backend/tests/test_ia_costeo.py -x`
- **Per wave merge:** `uv run pytest backend/tests/ -v --tb=short`
- **Phase gate:** Full suite green antes de `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/tests/test_ia_costeo.py` — cubre R1.1 (mock Anthropic SDK con `unittest.mock.patch`)
- [ ] `backend/app/config.py` — agregar `ANTHROPIC_API_KEY: Optional[str] = None` al Settings model
- [ ] `pyproject.toml` — agregar `anthropic>=0.40.0` a `dependencies` y correr `uv sync`

---

## Sources

### Primary (HIGH confidence)

- Codebase leido directamente:
  - `backend/app/servicios/servicio_analisis_cvu.py` — API publica, metodos disponibles, firmas
  - `backend/app/rutas/recetas.py` — patron de rutas existente, dependencias, seguridad
  - `backend/app/config.py` — estructura Settings, patron de env vars
  - `frontend/src/pages/RecetasPage.tsx` — estructura de modales existentes, estado local, mutations
  - `backend/app/rutas/socia.py` — confirma que "socia" como nombre ya existe (gamificacion — diferente del asistente IA)
  - `pyproject.toml` — confirma ausencia de `anthropic` en dependencies (gap critico)
  - `.planning/phases/01-auditoria/DECISIONS.md` — decisiones bloqueadas, configuracion tecnica
  - `.planning/phases/02-ia-core-asistente-de-costeo-y-pricing/02-CONTEXT.md` — todas las decisiones de implementacion

### Secondary (MEDIUM confidence)

- Anthropic tool_use pattern: confirmado via conocimiento del SDK anthropic>=0.20 (stable API)
- Prompt caching pattern: `cache_control: ephemeral` es parte de la API publica de Anthropic desde 2024

### Tertiary (LOW confidence)

- Estimacion de latencia de Haiku 4.5 para este caso de uso: ~1-3 segundos para Fase 1 (~500 tokens input + sistema, ~300 tokens output) — no verificado via benchmark

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — SDK Anthropic identificado, ausencia en pyproject.toml confirmada, patron tool_use verificado en docs oficiales
- Architecture: HIGH — patronas de servicios y rutas verificados directamente en el codebase existente
- Pitfalls: HIGH — Decimal safety y ausencia de SDK confirmados en codebase; tool_choice pattern confirmado en docs Anthropic
- Test strategy: MEDIUM — pytest existente confirmado, archivos de test nuevos identificados correctamente

**Research date:** 2026-03-04
**Valid until:** 2026-04-04 (anthropic SDK API es estable; pyproject.toml gap es fact hasta que se resuelva en Wave 0)
