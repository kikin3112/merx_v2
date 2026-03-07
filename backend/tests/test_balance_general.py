"""
Tests for C-21: Balance General endpoint.
Verifies activos = pasivos + patrimonio (accounting equation).
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from app.datos.modelos import (
    AsientosContables,
    CuentasContables,
    DetallesAsiento,
    Secuencias,
)


def _headers(token_data: dict) -> dict:
    return {
        "Authorization": f"Bearer {token_data['token']}",
        "X-Tenant-ID": token_data["tenant_id"],
    }


def _seed_cuenta(db, tenant_id: UUID, codigo: str, nombre: str, tipo: str, naturaleza: str):
    cuenta = CuentasContables(
        tenant_id=tenant_id,
        codigo=codigo,
        nombre=nombre,
        tipo_cuenta=tipo,
        nivel=4,
        naturaleza=naturaleza,
        acepta_movimiento=True,
        estado=True,
    )
    db.add(cuenta)
    db.flush()
    return cuenta


def _seed_seq(db, tenant_id: UUID):
    seq = Secuencias(
        tenant_id=tenant_id,
        nombre="ASIENTOS",
        prefijo="AS-",
        siguiente_numero=1,
        longitud_numero=6,
    )
    db.add(seq)
    db.flush()


def _seed_asiento_balanceado(db, tenant_id: UUID, cuenta_activo_id, cuenta_pasivo_id, monto: Decimal):
    """Creates a balanced entry: DEBE activo / HABER pasivo."""
    asiento = AsientosContables(
        tenant_id=tenant_id,
        numero_asiento="AS-000001",
        fecha=date(2026, 1, 1),
        tipo_asiento="AJUSTE",
        concepto="Asiento test",
        estado="ACTIVO",
    )
    db.add(asiento)
    db.flush()

    db.add(
        DetallesAsiento(
            tenant_id=tenant_id,
            asiento_id=asiento.id,
            cuenta_id=cuenta_activo_id,
            debito=monto,
            credito=Decimal("0"),
        )
    )
    db.add(
        DetallesAsiento(
            tenant_id=tenant_id,
            asiento_id=asiento.id,
            cuenta_id=cuenta_pasivo_id,
            debito=Decimal("0"),
            credito=monto,
        )
    )
    db.flush()


def test_balance_general_sin_movimientos(client, db_session, tenant_admin_token):
    """Balance general with no movements returns empty lists and balanceado=True."""
    headers = _headers(tenant_admin_token)
    resp = client.get("/api/v1/contabilidad/balance-general", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["balanceado"] is True
    assert data["activos"]["total"] == "0"
    assert data["pasivos"]["total"] == "0"
    assert data["patrimonio"]["total"] == "0"


def test_balance_general_ecuacion_contable(client, db_session, tenant_admin_token):
    """
    C-21: activos = pasivos + patrimonio.
    Seeds: 1105 Caja (Activo) DEBE $5M / 2105 CxP (Pasivo) HABER $5M.
    Expects: activos=5M, pasivos=5M, balanceado=True.
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])
    headers = _headers(tenant_admin_token)

    _seed_seq(db_session, tenant_id)
    cuenta_caja = _seed_cuenta(db_session, tenant_id, "1105", "Caja", "ACTIVO", "DEBITO")
    cuenta_cxp = _seed_cuenta(db_session, tenant_id, "2105", "CxP Proveedores", "PASIVO", "CREDITO")

    _seed_asiento_balanceado(db_session, tenant_id, cuenta_caja.id, cuenta_cxp.id, Decimal("5000000"))
    db_session.commit()

    resp = client.get("/api/v1/contabilidad/balance-general", headers=headers)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["balanceado"] is True
    assert Decimal(data["activos"]["total"]) == Decimal("5000000"), data
    assert Decimal(data["pasivos"]["total"]) == Decimal("5000000"), data
    assert abs(Decimal(data["diferencia"])) < Decimal("0.01"), data


def test_balance_general_fecha_corte_excluye_futuros(client, db_session, tenant_admin_token):
    """
    fecha_corte=2025-12-31 excludes entries from 2026-01-01.
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])
    headers = _headers(tenant_admin_token)

    _seed_seq(db_session, tenant_id)
    cuenta_caja = _seed_cuenta(db_session, tenant_id, "1105", "Caja", "ACTIVO", "DEBITO")
    cuenta_cxp = _seed_cuenta(db_session, tenant_id, "2105", "CxP", "PASIVO", "CREDITO")
    _seed_asiento_balanceado(db_session, tenant_id, cuenta_caja.id, cuenta_cxp.id, Decimal("5000000"))
    db_session.commit()

    # Query with corte BEFORE the seeded entry date (2026-01-01)
    resp = client.get("/api/v1/contabilidad/balance-general?fecha_corte=2025-12-31", headers=headers)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["activos"]["total"] == "0"
    assert data["balanceado"] is True
