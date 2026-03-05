"""
Servicio de IA para costeo — Socia, la asistente inteligente de Merx.
Orquesta llamadas a claude-haiku-4-5 via Anthropic SDK para sugerencias
de precio y análisis de márgenes dentro del módulo de recetas.
"""

from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

import anthropic
from fastapi import HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session, joinedload

from ..config import settings
from ..datos.modelos import Recetas, RecetasIngredientes
from ..servicios.servicio_analisis_cvu import ServicioAnalisisCVU
from ..servicios.servicio_costos_indirectos import ServicioCostosIndirectos
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


# ── Thin async wrapper for Anthropic messages ────────────────────────────────
# Required so unittest.mock.patch.object auto-detects create() as async
# (inspect.iscoroutinefunction returns False on the raw SDK method).


class _AnthropicMessages:
    """Async wrapper around anthropic.AsyncAnthropic.messages with a true async def create."""

    def __init__(self, raw_client: anthropic.AsyncAnthropic) -> None:
        self._raw = raw_client

    async def create(self, **kwargs: Any) -> Any:
        return await self._raw.messages.create(**kwargs)


class _AnthropicClientWrapper:
    """Wraps AsyncAnthropic so that _client.messages.create is a real async method."""

    def __init__(self, api_key: Optional[str]) -> None:
        self._raw = anthropic.AsyncAnthropic(api_key=api_key)
        self.messages = _AnthropicMessages(self._raw)


# ── Tool definition (Socia Fase 1 structured output) ─────────────────────────

SOCIA_TOOL = {
    "name": "analisis_costeo",
    "description": "Análisis estructurado de precio y margen para la receta artesanal",
    "input_schema": {
        "type": "object",
        "properties": {
            "precio_sugerido": {
                "type": "number",
                "description": "Precio sugerido en COP",
            },
            "margen_esperado": {
                "type": "number",
                "description": "Margen esperado en porcentaje (0-100)",
            },
            "escenario_recomendado": {
                "type": "string",
                "description": "Nombre del escenario recomendado de los 5 disponibles",
            },
            "justificacion": {
                "type": "string",
                "description": "Explicación en lenguaje accesible, tono de Socia",
            },
            "alertas": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Lista de alertas técnicas y estratégicas",
            },
            "mensaje_cierre": {
                "type": "string",
                "description": "Frase cálida de cierre al estilo caleño",
            },
        },
        "required": [
            "precio_sugerido",
            "margen_esperado",
            "escenario_recomendado",
            "justificacion",
            "alertas",
            "mensaje_cierre",
        ],
    },
}


# ── Pydantic model for Decimal safety ────────────────────────────────────────


class SociaAnalisisResponse(BaseModel):
    precio_sugerido: Decimal
    margen_esperado: Decimal
    escenario_recomendado: str
    justificacion: str
    alertas: list[str]
    mensaje_cierre: str

    @field_validator("precio_sugerido", "margen_esperado", mode="before")
    @classmethod
    def cast_decimal(cls, v: Any) -> Decimal:
        return Decimal(str(v))


# ── Main service ──────────────────────────────────────────────────────────────


class ServicioIACosteo:
    """
    Orquestador de IA para el módulo Socia.
    Fase 1: analisis_inicial() — structured output via tool_use (claude-haiku-4-5)
    Fase 2: chat_libre() — free text conversation
    """

    def __init__(self, db: Session, tenant_id: UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._client = _AnthropicClientWrapper(api_key=settings.ANTHROPIC_API_KEY)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_receta(self, receta_id: UUID) -> Recetas:
        """Fetch receta validating tenant isolation. Raises 404 if not found."""
        receta = (
            self.db.query(Recetas)
            .options(
                joinedload(Recetas.ingredientes).joinedload(RecetasIngredientes.producto),
                joinedload(Recetas.producto_resultado),
            )
            .filter(
                Recetas.id == receta_id,
                Recetas.tenant_id == self.tenant_id,
                Recetas.deleted_at.is_(None),
            )
            .first()
        )
        if not receta:
            raise HTTPException(status_code=404, detail="Receta no encontrada")
        return receta

    def _build_context(
        self,
        receta_id: UUID,
        precio_referencia: Optional[Decimal] = None,
    ) -> dict:
        """
        Reuse existing services to build CVU context.
        Does NOT duplicate any calculation logic.
        """
        receta = self._get_receta(receta_id)
        volumen = receta.produccion_mensual_esperada or 1

        costos_info = ServicioCostosIndirectos(self.db, self.tenant_id).calcular_total_para_costo_base(receta_id)
        costos_fijos = costos_info.get("total_cif", Decimal("0"))

        context = ServicioAnalisisCVU(self.db, self.tenant_id).generar_escenarios_precio(
            receta_id=receta_id,
            costos_fijos=costos_fijos,
            volumen=volumen,
            precio_mercado_referencia=precio_referencia,
        )
        return context

    def _build_system_prompt(self, context: dict) -> str:
        """
        Build Socia system prompt with caleña personality and embedded CVU context.
        Target ~500 tokens for prompt caching efficiency.
        All Decimal values converted to float/str before embedding in f-strings.
        """
        receta_nombre = context.get("receta_nombre", "tu receta")
        cvu = context.get("costo_variable_unitario", Decimal("0"))
        cvu_fmt = f"${float(cvu):,.0f} COP"

        escenarios = context.get("escenarios", [])
        escenarios_text = ""
        for e in escenarios:
            precio = float(e.get("precio", 0))
            viabilidad = e.get("viabilidad", "")
            nombre = e.get("nombre", "")
            escenarios_text += f"  • {nombre}: ${precio:,.0f} COP — {viabilidad}\n"

        return f"""Eres Socia, la asistente de costeo y pricing de Merx. Eres femenina, cálida y caleña — la mejor socia que sabe mucho de negocios y conoce el mercado del Valle del Cauca (velas de Palmira, confites artesanales).

Tu tono es natural y accesible: usas palabras como "bacano", "chévere", "hagámosle", "eso es" — pero sin exagerar. Explicas los números en lenguaje simple: "Para no perder plata, cobra mínimo $X" en vez de "El precio de equilibrio es $X".

CONTEXTO DE LA RECETA:
Nombre: {receta_nombre}
Costo variable unitario (CVU): {cvu_fmt}

ESCENARIOS DE PRECIO DISPONIBLES:
{escenarios_text.rstrip()}

INSTRUCCIONES:
- Analiza los 5 escenarios y recomienda el más adecuado para una PyME artesanal del Valle del Cauca
- Explica tu recomendación en términos que entienda cualquier emprendedora
- Identifica alertas técnicas (margen bajo, punto de equilibrio alto) y estratégicas (competencia, estacionalidad)
- Cierra siempre con una frase cálida y motivadora al estilo caleño
- Usa SIEMPRE la herramienta analisis_costeo para estructurar tu respuesta"""

    # ── Public async API ──────────────────────────────────────────────────────

    async def analisis_inicial(
        self,
        receta_id: UUID,
        precio_referencia: Optional[Decimal] = None,
    ) -> dict:
        """
        Fase 1: Structured analysis via tool_use.
        Returns dict with 6 keys: precio_sugerido, margen_esperado,
        escenario_recomendado, justificacion, alertas, mensaje_cierre.
        precio_sugerido and margen_esperado are always Decimal instances.
        """
        context = self._build_context(receta_id, precio_referencia)
        system_prompt = self._build_system_prompt(context)

        try:
            response = await self._client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1024,
                tools=[SOCIA_TOOL],
                tool_choice={"type": "tool", "name": "analisis_costeo"},
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": f"Analiza el precio óptimo para la receta '{context.get('receta_nombre', 'esta receta')}'.",
                    }
                ],
            )
        except anthropic.APIError as exc:
            logger.error(f"Anthropic API error en analisis_inicial: {exc}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail="Socia no pudo responder en este momento",
            ) from exc

        tool_block = next(b for b in response.content if b.type == "tool_use")
        raw = tool_block.input  # dict with raw values (floats from JSON)

        validated = SociaAnalisisResponse(**raw)
        return validated.model_dump()

    async def chat_libre(
        self,
        receta_id: UUID,
        messages: list[dict],
    ) -> dict:
        """
        Fase 2: Free-form conversation without tool_use.
        messages: conversation history in Anthropic format.
        Returns {"respuesta": str}.
        """
        context = self._build_context(receta_id)
        system_prompt = self._build_system_prompt(context)

        try:
            response = await self._client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1024,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=messages,
            )
        except anthropic.APIError as exc:
            logger.error(f"Anthropic API error en chat_libre: {exc}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail="Socia no pudo responder en este momento",
            ) from exc

        text_content = next(b for b in response.content if b.type == "text").text
        return {"respuesta": text_content}
