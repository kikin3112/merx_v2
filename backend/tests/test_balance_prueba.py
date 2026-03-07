"""
Tests for C-05 audit fix: balance de prueba excludes soft-deleted entries.

Verifies that AsientosContables with deleted_at set are excluded
from the balance de prueba report.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.datos.modelos import (
    AsientosContables,
    CuentasContables,
    DetallesAsiento,
    Secuencias,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _headers(token_data: dict) -> dict:
    return {
        "Authorization": f"Bearer {token_data['token']}",
        "X-Tenant-ID": token_data["tenant_id"],
    }


def _seed_cuenta_y_asiento(db, tenant_id: UUID, soft_delete: bool = False):
    """Creates a CuentasContables entry and an AsientosContables with one debit line."""
    cuenta = CuentasContables(
        tenant_id=tenant_id,
        codigo="1105",
        nombre="Caja general",
        tipo_cuenta="ACTIVO",
        nivel=4,
        naturaleza="DEBITO",
        acepta_movimiento=True,
        estado=True,
    )
    db.add(cuenta)
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

    asiento = AsientosContables(
        tenant_id=tenant_id,
        numero_asiento="AS-000001",
        fecha=date(2026, 3, 1),
        tipo_asiento="VENTAS",
        concepto="Test asiento",
        estado="ACTIVO",
    )
    if soft_delete:
        asiento.deleted_at = datetime(2026, 3, 2, 12, 0, 0)
    db.add(asiento)
    db.flush()

    detalle = DetallesAsiento(
        tenant_id=tenant_id,
        asiento_id=asiento.id,
        cuenta_id=cuenta.id,
        debito=Decimal("50000"),
        credito=Decimal("0"),
        descripcion="Test detalle",
    )
    db.add(detalle)
    db.flush()

    return cuenta, asiento


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_balance_prueba_excluye_asiento_soft_deleted(client, db_session, tenant_admin_token):
    """
    GET /contabilidad/balance-prueba — soft-deleted AsientosContables
    must NOT appear in the report.
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])
    headers = _headers(tenant_admin_token)

    _seed_cuenta_y_asiento(db_session, tenant_id, soft_delete=True)
    db_session.commit()

    resp = client.get("/api/v1/contabilidad/balance-prueba", headers=headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    data = resp.json()
    cuentas = data["cuentas"]
    # If soft-deleted entry is excluded, no rows should appear
    caja_entry = next((r for r in cuentas if r["codigo"] == "1105"), None)
    assert caja_entry is None, (
        f"Soft-deleted asiento should be excluded from balance de prueba. " f"Found: {caja_entry}"
    )


def test_balance_prueba_incluye_asiento_activo(client, db_session, tenant_admin_token):
    """
    GET /contabilidad/balance-prueba — active (non-deleted) entries
    MUST appear in the report.
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])
    headers = _headers(tenant_admin_token)

    _seed_cuenta_y_asiento(db_session, tenant_id, soft_delete=False)
    db_session.commit()

    resp = client.get("/api/v1/contabilidad/balance-prueba", headers=headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    data = resp.json()
    cuentas = data["cuentas"]
    caja_entry = next((r for r in cuentas if r["codigo"] == "1105"), None)
    assert caja_entry is not None, "Active asiento should appear in balance de prueba"
    assert Decimal(caja_entry["total_debito"]) == Decimal(
        "50000"
    ), f"Expected total_debito=50000, got {caja_entry['total_debito']}"
