"""
Servicio de IA para costeo — Socia, la asistente inteligente de Merx.
Usa OpenRouter (API compatible con OpenAI) para orquestar el modelo LLM.
"""

import hashlib
import json
import re
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session, joinedload

from ..config import settings
from ..datos.modelos import Recetas, RecetasIngredientes
from ..servicios.servicio_analisis_cvu import ServicioAnalisisCVU
from ..servicios.servicio_costos_indirectos import ServicioCostosIndirectos
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


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
    Fase 1: analisis_inicial() — structured JSON output via system prompt
    Fase 2: chat_libre() — free text conversation
    """

    def __init__(self, db: Session, tenant_id: UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._api_key = settings.OPENROUTER_API_KEY
        self._model = settings.OPENROUTER_MODEL

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_receta(self, receta_id: UUID) -> Recetas:
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
        receta = self._get_receta(receta_id)
        volumen = receta.produccion_mensual_esperada or 1

        fijo_total, _ = ServicioCostosIndirectos(self.db, self.tenant_id).calcular_fijo_y_porcentaje(Decimal("0"))
        costos_fijos = fijo_total

        return ServicioAnalisisCVU(self.db, self.tenant_id).generar_escenarios_precio(
            receta_id=receta_id,
            costos_fijos=costos_fijos,
            volumen=volumen,
            precio_mercado_referencia=precio_referencia,
        )

    def _build_system_prompt(self, context: dict, fase1: bool = True) -> str:
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

        base = f"""Eres Socia, la asistente de costeo y pricing de Merx. Eres femenina, cálida y caleña — la mejor socia que sabe mucho de negocios y conoce el mercado del Valle del Cauca (velas de Palmira, confites artesanales).

Tu tono es natural y accesible: usas palabras como "bacano", "chévere", "hagámosle", "eso es" — pero sin exagerar. Explicas los números en lenguaje simple: "Para no perder plata, cobra mínimo $X" en vez de "El precio de equilibrio es $X".

CONTEXTO DE LA RECETA:
Nombre: {receta_nombre}
Costo variable unitario (CVU): {cvu_fmt}

ESCENARIOS DE PRECIO DISPONIBLES:
{escenarios_text.rstrip()}"""

        if fase1:
            base += """

INSTRUCCIONES:
Analiza los escenarios y responde ÚNICAMENTE con un objeto JSON válido (sin markdown, sin texto antes ni después):
{
  "precio_sugerido": <número en COP>,
  "margen_esperado": <porcentaje 0-100>,
  "escenario_recomendado": "<nombre del escenario>",
  "justificacion": "<explicación cálida en 2-3 oraciones>",
  "alertas": ["<alerta1>", "<alerta2>"],
  "mensaje_cierre": "<frase motivadora caleña>"
}"""
        return base

    async def _call_openrouter(self, messages: list[dict], system: str) -> str:
        """Call OpenRouter API and return the text content of the first choice."""
        if not self._api_key:
            raise HTTPException(
                status_code=503,
                detail="Socia no pudo responder en este momento. Intenta de nuevo.",
            )

        payload = {
            "model": self._model,
            "messages": [{"role": "system", "content": system}] + messages,
            "max_tokens": 1024,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "HTTP-Referer": "https://merx.app",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(f"OpenRouter HTTP error: {exc.response.status_code} — {exc.response.text}")
            raise HTTPException(
                status_code=503,
                detail="Socia no pudo responder en este momento. Intenta de nuevo.",
            ) from exc
        except httpx.RequestError as exc:
            logger.error(f"OpenRouter request error: {exc}")
            raise HTTPException(
                status_code=503,
                detail="Socia no pudo responder en este momento. Intenta de nuevo.",
            ) from exc

        data = resp.json()
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract the first JSON object from model output (handles markdown fences)."""
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
        # Find first {...}
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON object found in model output: {text[:200]}")
        return json.loads(match.group())

    # ── Cache helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _compute_cache_key(context: dict, precio_referencia: Optional[Decimal]) -> str:
        """SHA-256 of CVU + escenarios + precio_referencia. Changes whenever costs change."""
        payload = json.dumps(
            {
                "cvu": str(context.get("costo_variable_unitario", "0")),
                "escenarios": str(context.get("escenarios", [])),
                "precio_ref": str(precio_referencia or ""),
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    # ── Public async API ──────────────────────────────────────────────────────

    async def analisis_inicial(
        self,
        receta_id: UUID,
        precio_referencia: Optional[Decimal] = None,
    ) -> dict:
        """
        Fase 1: Structured analysis via JSON-in-prompt.
        Returns dict with 6 keys: precio_sugerido, margen_esperado,
        escenario_recomendado, justificacion, alertas, mensaje_cierre.

        Result is cached in DB (socia_cache) and invalidated automatically when
        recipe costs change (CVU or escenarios differ from stored cache_key).
        """
        context = self._build_context(receta_id, precio_referencia)
        cache_key = self._compute_cache_key(context, precio_referencia)

        receta = self._get_receta(receta_id)
        if receta.socia_cache_key == cache_key and receta.socia_cache:
            logger.info(f"Socia cache HIT for receta {receta_id}")
            return receta.socia_cache

        logger.info(f"Socia cache MISS for receta {receta_id} — calling LLM")
        system_prompt = self._build_system_prompt(context, fase1=True)
        user_msg = f"Analiza el precio óptimo para la receta '{context.get('receta_nombre', 'esta receta')}'."

        try:
            raw_text = await self._call_openrouter(
                messages=[{"role": "user", "content": user_msg}],
                system=system_prompt,
            )
            raw = self._extract_json(raw_text)
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            logger.error(f"Error parsing OpenRouter response: {exc}")
            raise HTTPException(
                status_code=503,
                detail="Socia no pudo responder en este momento. Intenta de nuevo.",
            ) from exc

        validated = SociaAnalisisResponse(**raw)
        result = validated.model_dump(mode="json")  # Decimals → str for JSONB storage

        receta.socia_cache = result
        receta.socia_cache_key = cache_key
        self.db.flush()

        return result

    async def chat_libre(
        self,
        receta_id: UUID,
        messages: list[dict],
    ) -> dict:
        """
        Fase 2: Free-form conversation.
        messages: list of {"role": "user"|"assistant", "content": str}
        Returns {"respuesta": str}.
        """
        context = self._build_context(receta_id)
        system_prompt = self._build_system_prompt(context, fase1=False)

        raw_text = await self._call_openrouter(messages=messages, system=system_prompt)
        return {"respuesta": raw_text}
