"""
Tests for C-08: Prevent retroactive period hopping.
Creating an entry > 2 months in the past should raise ValueError.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest
from app.datos.modelos import CuentasContables, Secuencias
from app.servicios.servicio_contabilidad import ServicioContabilidad


def _seed_setup(db, tenant_id: UUID):
    """Seed two accounts and a sequence for the service tests."""
    caja = CuentasContables(
        tenant_id=tenant_id,
        codigo="1105",
        nombre="Caja",
        tipo_cuenta="ACTIVO",
        nivel=4,
        naturaleza="DEBITO",
        acepta_movimiento=True,
        estado=True,
    )
    ventas = CuentasContables(
        tenant_id=tenant_id,
        codigo="4135",
        nombre="Ventas",
        tipo_cuenta="INGRESO",
        nivel=4,
        naturaleza="CREDITO",
        acepta_movimiento=True,
        estado=True,
    )
    db.add(caja)
    db.add(ventas)
    db.flush()

    seq = Secuencias(
        tenant_id=tenant_id,
        nombre="ASIENTOS",
        prefijo="AS-",
        siguiente_numero=1,
        longitud_numero=6,
    )
    db.add(seq)
    db.flush()
    db.commit()

    return caja, ventas


def test_periodo_hopping_bloqueado_3_meses_atras(db_session, tenant_admin_token):
    """
    C-08: Creating a journal entry 3 months in the past raises ValueError.
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])
    caja, ventas = _seed_setup(db_session, tenant_id)

    from datetime import date as _date

    today = _date.today()
    # Date 3 months ago (always > 2 months in the past)
    if today.month > 3:
        fecha_antigua = _date(today.year, today.month - 3, 1)
    else:
        fecha_antigua = _date(today.year - 1, today.month + 9, 1)

    svc = ServicioContabilidad(db_session, tenant_id)

    with pytest.raises(ValueError, match="meses en el pasado"):
        svc.crear_asiento(
            fecha=fecha_antigua,
            tipo_asiento="AJUSTE",
            concepto="Test hopping bloqueado",
            detalles=[
                {"cuenta_id": caja.id, "debito": Decimal("100"), "credito": Decimal("0")},
                {"cuenta_id": ventas.id, "debito": Decimal("0"), "credito": Decimal("100")},
            ],
        )


def test_periodo_hopping_permitido_mes_actual(db_session, tenant_admin_token):
    """
    C-08: Creating entry in current month is always allowed.
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])
    caja, ventas = _seed_setup(db_session, tenant_id)

    svc = ServicioContabilidad(db_session, tenant_id)
    fecha_hoy = date.today()

    # Should NOT raise
    asiento = svc.crear_asiento(
        fecha=fecha_hoy,
        tipo_asiento="AJUSTE",
        concepto="Test mes actual",
        detalles=[
            {"cuenta_id": caja.id, "debito": Decimal("100"), "credito": Decimal("0")},
            {"cuenta_id": ventas.id, "debito": Decimal("0"), "credito": Decimal("100")},
        ],
    )
    assert asiento is not None


def test_apertura_bypass_hopping(client, db_session, tenant_admin_token):
    """
    C-07/C-08: asiento-apertura bypasses hopping check — historical dates allowed.
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])
    headers = {
        "Authorization": f"Bearer {tenant_admin_token['token']}",
        "X-Tenant-ID": tenant_admin_token["tenant_id"],
    }

    caja = CuentasContables(
        tenant_id=tenant_id,
        codigo="1105",
        nombre="Caja",
        tipo_cuenta="ACTIVO",
        nivel=4,
        naturaleza="DEBITO",
        acepta_movimiento=True,
        estado=True,
    )
    capital = CuentasContables(
        tenant_id=tenant_id,
        codigo="3115",
        nombre="Capital",
        tipo_cuenta="PATRIMONIO",
        nivel=4,
        naturaleza="CREDITO",
        acepta_movimiento=True,
        estado=True,
    )
    db_session.add(caja)
    db_session.add(capital)
    db_session.flush()

    seq = Secuencias(
        tenant_id=tenant_id,
        nombre="ASIENTOS",
        prefijo="AS-",
        siguiente_numero=1,
        longitud_numero=6,
    )
    db_session.add(seq)
    db_session.commit()

    # 2 years ago — would normally be blocked by hopping check
    payload = {
        "fecha": "2024-01-01",
        "concepto": "Apertura 2024",
        "saldos": [
            {"cuenta_id": str(caja.id), "debito": "10000000", "credito": "0"},
            {"cuenta_id": str(capital.id), "debito": "0", "credito": "10000000"},
        ],
    }

    resp = client.post("/api/v1/contabilidad/asiento-apertura", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["tipo_asiento"] == "APERTURA"
