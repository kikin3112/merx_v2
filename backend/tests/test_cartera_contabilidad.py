"""
Tests for POST /cartera/{id}/pagos — COBRO_CARTERA accounting entry (E7 audit fix).

Verifies:
1. Payment creates COBRO_CARTERA AsientosContables with correct debit total.
2. Payment succeeds even when accounting config is absent (graceful degradation).
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from app.datos.modelos import (
    AsientosContables,
    Cartera,
    ConfiguracionContable,
    CuentasContables,
    DetallesAsiento,
    MediosPago,
    Secuencias,
    Terceros,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _headers(token_data: dict) -> dict:
    return {
        "Authorization": f"Bearer {token_data['token']}",
        "X-Tenant-ID": token_data["tenant_id"],
    }


def _seed_tercero(db, tenant_id: UUID) -> Terceros:
    tercero = Terceros(
        tenant_id=tenant_id,
        nombre="Cliente Test S.A.S.",
        tipo_documento="NIT",
        numero_documento="900888001-1",
        tipo_tercero="CLIENTE",
    )
    db.add(tercero)
    db.flush()
    return tercero


def _seed_medio_pago(db, tenant_id: UUID) -> MediosPago:
    medio = MediosPago(
        tenant_id=tenant_id,
        nombre="Efectivo Test",
        tipo="EFECTIVO",
        estado=True,
    )
    db.add(medio)
    db.flush()
    return medio


def _seed_config_contable(db, tenant_id: UUID):
    """Seeds CuentasContables (1105 Caja, 1305 CxC) + ConfiguracionContable
    (VENTA_CONTADO with caja as debito, VENTA_CREDITO with cxc as debito)
    + ASIENTOS sequence."""
    cuenta_caja = CuentasContables(
        tenant_id=tenant_id,
        codigo="1105",
        nombre="Caja general",
        tipo_cuenta="ACTIVO",
        nivel=4,
        naturaleza="DEBITO",
        acepta_movimiento=True,
        estado=True,
    )
    cuenta_cxc = CuentasContables(
        tenant_id=tenant_id,
        codigo="1305",
        nombre="Clientes nacionales (CxC)",
        tipo_cuenta="ACTIVO",
        nivel=4,
        naturaleza="DEBITO",
        acepta_movimiento=True,
        estado=True,
    )
    db.add(cuenta_caja)
    db.add(cuenta_cxc)
    db.flush()

    # VENTA_CONTADO: debito=Caja (used as destination of cash receipt)
    config_venta = ConfiguracionContable(
        tenant_id=tenant_id,
        concepto="VENTA_CONTADO",
        cuenta_debito_id=cuenta_caja.id,
        cuenta_credito_id=cuenta_caja.id,  # credito not used in cobro path
        descripcion="Venta de contado",
    )
    # VENTA_CREDITO: debito=CxC (used as source account being cancelled)
    config_credito = ConfiguracionContable(
        tenant_id=tenant_id,
        concepto="VENTA_CREDITO",
        cuenta_debito_id=cuenta_cxc.id,
        cuenta_credito_id=cuenta_cxc.id,  # credito not used in cobro path
        descripcion="Venta a crédito / CxC",
    )
    db.add(config_venta)
    db.add(config_credito)

    secuencia = Secuencias(
        tenant_id=tenant_id,
        nombre="ASIENTOS",
        prefijo="AS-",
        siguiente_numero=1,
        longitud_numero=6,
    )
    db.add(secuencia)
    db.flush()

    return cuenta_caja, cuenta_cxc


def _seed_cartera(db, tenant_id: UUID, tercero_id: UUID, valor: Decimal = Decimal("100000")) -> Cartera:
    cartera = Cartera(
        tenant_id=tenant_id,
        tipo_cartera="COBRAR",
        documento_referencia="FAC-TEST-001",
        tercero_id=tercero_id,
        fecha_emision=date(2026, 3, 1),
        fecha_vencimiento=date(2026, 4, 1),
        valor_total=valor,
        saldo_pendiente=valor,
        estado="PENDIENTE",
    )
    db.add(cartera)
    db.flush()
    return cartera


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pago_cartera_crea_asiento_contable(client, db_session, tenant_admin_token):
    """POST /cartera/{id}/pagos — happy path:
    - HTTP 201
    - AsientosContables with tipo_asiento=COBRO_CARTERA created
    - total debito == 100000
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])

    tercero = _seed_tercero(db_session, tenant_id)
    medio = _seed_medio_pago(db_session, tenant_id)
    _seed_config_contable(db_session, tenant_id)
    cartera = _seed_cartera(db_session, tenant_id, tercero.id)
    db_session.commit()

    response = client.post(
        f"/api/v1/cartera/{cartera.id}/pagos",
        json={
            "cartera_id": str(cartera.id),
            "valor_pago": "100000",
            "fecha_pago": "2026-03-06",
            "medio_pago_id": str(medio.id),
        },
        headers=_headers(tenant_admin_token),
    )

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    # AsientosContables COBRO_CARTERA created
    asiento = (
        db_session.query(AsientosContables)
        .filter(
            AsientosContables.tenant_id == tenant_id,
            AsientosContables.tipo_asiento == "COBRO_CARTERA",
        )
        .first()
    )
    assert asiento is not None, "AsientosContables COBRO_CARTERA should exist"

    # Verify total debito == 100000
    detalles = (
        db_session.query(DetallesAsiento)
        .filter(
            DetallesAsiento.asiento_id == asiento.id,
            DetallesAsiento.tenant_id == tenant_id,
        )
        .all()
    )
    total_debito = sum(d.debito for d in detalles)
    assert total_debito == Decimal("100000"), f"Expected total_debito=100000, got {total_debito}"


def test_pago_cartera_sin_config_contable_hace_rollback(client, db_session, tenant_admin_token):
    """POST /cartera/{id}/pagos without accounting config → 400, payment NOT persisted.
    Accounting is required for payment atomicity (C-04 audit fix).
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])

    tercero = _seed_tercero(db_session, tenant_id)
    medio = _seed_medio_pago(db_session, tenant_id)
    # Deliberately NO _seed_config_contable — accounting config absent
    cartera = _seed_cartera(db_session, tenant_id, tercero.id)
    db_session.commit()

    saldo_original = cartera.saldo_pendiente

    response = client.post(
        f"/api/v1/cartera/{cartera.id}/pagos",
        json={
            "cartera_id": str(cartera.id),
            "valor_pago": "100000",
            "fecha_pago": "2026-03-06",
            "medio_pago_id": str(medio.id),
        },
        headers=_headers(tenant_admin_token),
    )

    # Must fail — VENTA_CONTADO / VENTA_CREDITO config required (C-04)
    assert (
        response.status_code == 400
    ), f"Expected 400 when accounting config missing, got {response.status_code}: {response.text}"

    # Saldo should be unchanged (rollback)
    db_session.expire_all()
    cartera_db = db_session.query(Cartera).filter(Cartera.id == cartera.id).first()
    assert (
        cartera_db.saldo_pendiente == saldo_original
    ), f"Expected saldo_pendiente={saldo_original} after rollback, got {cartera_db.saldo_pendiente}"

    # No payment persisted
    from app.datos.modelos import PagosCartera

    count_pagos = (
        db_session.query(PagosCartera)
        .filter(PagosCartera.cartera_id == cartera.id, PagosCartera.tenant_id == tenant_id)
        .count()
    )
    assert count_pagos == 0, f"No PagosCartera should exist after rollback, got {count_pagos}"
