"""
Tests for GET /contabilidad/estado-resultados — P&L endpoint (E9).
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from app.datos.modelos import AsientosContables, CuentasContables, DetallesAsiento, PeriodosContables
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _seed_cuentas_y_asiento(db: Session, tenant_id: UUID) -> None:
    """
    Seeds 3 P&L accounts and one asiento with:
    - 4135 Ventas: credito=500000
    - 6135 Costo ventas: debito=200000
    - 5105 Gastos admin: debito=50000
    """
    cuenta_ventas = CuentasContables(
        tenant_id=tenant_id,
        codigo="4135",
        nombre="Ventas",
        tipo_cuenta="INGRESO",
        nivel=2,
        naturaleza="CREDITO",
        acepta_movimiento=True,
    )
    cuenta_cogs = CuentasContables(
        tenant_id=tenant_id,
        codigo="6135",
        nombre="Costo de mercancia vendida",
        tipo_cuenta="COSTOS",
        nivel=2,
        naturaleza="DEBITO",
        acepta_movimiento=True,
    )
    cuenta_gastos = CuentasContables(
        tenant_id=tenant_id,
        codigo="5105",
        nombre="Gastos de administracion",
        tipo_cuenta="EGRESO",
        nivel=2,
        naturaleza="DEBITO",
        acepta_movimiento=True,
    )
    db.add_all([cuenta_ventas, cuenta_cogs, cuenta_gastos])
    db.flush()

    periodo = PeriodosContables(tenant_id=tenant_id, anio=2026, mes=3, estado="ABIERTO")
    db.add(periodo)
    db.flush()

    asiento = AsientosContables(
        tenant_id=tenant_id,
        numero_asiento="A-001",
        fecha=date(2026, 3, 1),
        tipo_asiento="VENTAS",
        concepto="Test P&L seed",
        estado="ACTIVO",
        periodo_id=periodo.id,
    )
    db.add(asiento)
    db.flush()

    detalles = [
        DetallesAsiento(
            tenant_id=tenant_id,
            asiento_id=asiento.id,
            cuenta_id=cuenta_ventas.id,
            debito=Decimal("0"),
            credito=Decimal("500000"),
            descripcion="Venta test",
        ),
        DetallesAsiento(
            tenant_id=tenant_id,
            asiento_id=asiento.id,
            cuenta_id=cuenta_cogs.id,
            debito=Decimal("200000"),
            credito=Decimal("0"),
            descripcion="COGS test",
        ),
        DetallesAsiento(
            tenant_id=tenant_id,
            asiento_id=asiento.id,
            cuenta_id=cuenta_gastos.id,
            debito=Decimal("50000"),
            credito=Decimal("0"),
            descripcion="Gastos admin test",
        ),
    ]
    db.add_all(detalles)
    db.flush()


def test_estado_resultados_calcula_pnl(client: TestClient, db_session: Session, tenant_admin_token: dict):
    """Full P&L: ingresos 500k, COGS 200k, gastos 250k total — verify all aggregates."""
    tenant_id = UUID(tenant_admin_token["tenant_id"])
    _seed_cuentas_y_asiento(db_session, tenant_id)
    db_session.flush()

    headers = {
        "Authorization": f"Bearer {tenant_admin_token['token']}",
        "X-Tenant-ID": tenant_admin_token["tenant_id"],
    }

    response = client.get("/api/v1/contabilidad/estado-resultados", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert Decimal(data["ingresos"]["total"]) == Decimal("500000")
    assert Decimal(data["gastos"]["total"]) == Decimal("250000")  # 200000 + 50000
    assert Decimal(data["utilidad_bruta"]) == Decimal("300000")  # 500000 - 200000 cogs
    assert Decimal(data["utilidad_neta"]) == Decimal("250000")  # 500000 - 250000


def test_estado_resultados_filtra_por_fecha(client: TestClient, db_session: Session, tenant_admin_token: dict):
    """Date filter within range includes the entry."""
    tenant_id = UUID(tenant_admin_token["tenant_id"])
    _seed_cuentas_y_asiento(db_session, tenant_id)
    db_session.flush()

    headers = {
        "Authorization": f"Bearer {tenant_admin_token['token']}",
        "X-Tenant-ID": tenant_admin_token["tenant_id"],
    }

    response = client.get(
        "/api/v1/contabilidad/estado-resultados?fecha_inicio=2026-03-01&fecha_fin=2026-03-31",
        headers=headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert Decimal(data["ingresos"]["total"]) == Decimal("500000")


def test_estado_resultados_tenant_isolation(client: TestClient, db_session: Session, contador_token: dict):
    """Contador tenant has no data — all totals must be zero."""
    headers = {
        "Authorization": f"Bearer {contador_token['token']}",
        "X-Tenant-ID": contador_token["tenant_id"],
    }

    response = client.get("/api/v1/contabilidad/estado-resultados", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert Decimal(data["ingresos"]["total"]) == Decimal("0")
    assert Decimal(data["gastos"]["total"]) == Decimal("0")
    assert Decimal(data["utilidad_neta"]) == Decimal("0")
