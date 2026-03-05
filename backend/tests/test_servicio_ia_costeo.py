"""
Tests para ServicioIACosteo — asistente Socia.
Wave 0: stubs en RED state (servicio_ia_costeo.py no existe aún).
Wave 1: estos tests deben pasar (GREEN state).
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

# Este import falla en Wave 0 (archivo no existe) — RED state esperado
# En Wave 1 el archivo existirá y el import pasará
from app.servicios.servicio_ia_costeo import ServicioIACosteo

# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def receta_id():
    return uuid4()


@pytest.fixture
def servicio(mock_db, tenant_id):
    with patch("app.servicios.servicio_ia_costeo.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "sk-ant-test-key"
        svc = ServicioIACosteo(db=mock_db, tenant_id=tenant_id)
    return svc


# ── Tool use mock helper ─────────────────────────────────────────────────────


def _mock_anthropic_fase1_response():
    """Simula respuesta tool_use de Anthropic para Fase 1."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = {
        "precio_sugerido": 25000.0,
        "margen_esperado": 48.5,
        "escenario_recomendado": "Precio objetivo (60%)",
        "justificacion": "Bacano, con este precio cubres tus costos y te queda buen margen.",
        "alertas": ["Tu margen está al límite mínimo", "Los fines de semana en Palmira se vende más"],
        "mensaje_cierre": "Hagámosle, ese precio te va a funcionar chévere.",
    }
    mock_response = MagicMock()
    mock_response.content = [tool_block]
    return mock_response


def _mock_cvu_context():
    """Simula el contexto CVU que el servicio extrae de ServicioAnalisisCVU."""
    return {
        "receta_nombre": "VELA VASO TEST",
        "costo_variable_unitario": Decimal("13001.34"),
        "escenarios": [
            {"nombre": "Precio mínimo", "precio": Decimal("13001.34"), "viabilidad": "NO_VIABLE"},
            {"nombre": "Precio objetivo (60%)", "precio": Decimal("32503.35"), "viabilidad": "VIABLE"},
        ],
    }


# ── Tests ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analisis_inicial_returns_schema(servicio, receta_id):
    """R1.1: Fase 1 retorna los 6 campos del schema de Socia."""
    with (
        patch.object(servicio, "_build_context", return_value=_mock_cvu_context()),
        patch.object(servicio._client.messages, "create", return_value=_mock_anthropic_fase1_response()),
    ):
        result = await servicio.analisis_inicial(receta_id, precio_referencia=None)

    assert "precio_sugerido" in result
    assert "margen_esperado" in result
    assert "escenario_recomendado" in result
    assert "justificacion" in result
    assert "alertas" in result
    assert "mensaje_cierre" in result
    assert isinstance(result["alertas"], list)


@pytest.mark.asyncio
async def test_decimal_safety(servicio, receta_id):
    """R1.1 CRITICO: precio_sugerido y margen_esperado deben ser Decimal, nunca float."""
    with (
        patch.object(servicio, "_build_context", return_value=_mock_cvu_context()),
        patch.object(servicio._client.messages, "create", return_value=_mock_anthropic_fase1_response()),
    ):
        result = await servicio.analisis_inicial(receta_id, precio_referencia=None)

    assert isinstance(
        result["precio_sugerido"], Decimal
    ), f"precio_sugerido debe ser Decimal, got {type(result['precio_sugerido'])}"
    assert isinstance(
        result["margen_esperado"], Decimal
    ), f"margen_esperado debe ser Decimal, got {type(result['margen_esperado'])}"


@pytest.mark.asyncio
async def test_chat_fase2_returns_respuesta(servicio, receta_id):
    """R1.1: Fase 2 retorna dict con key 'respuesta' como string."""
    mock_chat_response = MagicMock()
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Claro que sí, hagámosle! En Palmira ese precio está muy bien."
    mock_chat_response.content = [text_block]

    messages = [
        {"role": "user", "content": "Hola Socia"},
        {"role": "assistant", "content": "Hola! Soy Socia."},
        {"role": "user", "content": "¿Qué precio me recomiendas?"},
    ]

    with (
        patch.object(servicio, "_build_context", return_value=_mock_cvu_context()),
        patch.object(servicio._client.messages, "create", return_value=mock_chat_response),
    ):
        result = await servicio.chat_libre(receta_id, messages)

    assert "respuesta" in result
    assert isinstance(result["respuesta"], str)
    assert len(result["respuesta"]) > 0


@pytest.mark.asyncio
async def test_tenant_isolation(receta_id, mock_db, tenant_id):
    """R1.1: Receta de otro tenant debe levantar error (no filtrar por tenant diferente)."""
    from fastapi import HTTPException

    # Simular que la receta no existe para este tenant (retorna None en DB query)
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None

    with patch("app.servicios.servicio_ia_costeo.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "sk-ant-test-key"
        svc = ServicioIACosteo(db=mock_db, tenant_id=tenant_id)

    with pytest.raises((HTTPException, ValueError)):
        await svc.analisis_inicial(receta_id, precio_referencia=None)
