"""
Tests for C-01 audit fix: COGS reversal on factura cancellation.

Verifies that when a FACTURADA invoice is cancelled:
- The accounting entry for COGS (account 6135) is reversed
- Net balance of 6135 (debito - credito) = $0 after cancellation
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from app.datos.modelos import (
    ConfiguracionContable,
    CuentasContables,
    DetallesAsiento,
    Inventarios,
    Productos,
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


def _seed_cuentas(db, tenant_id: UUID):
    """Seeds accounts 1105 (Caja), 4135 (Ventas), 6135 (CMV), 1435 (Inventario)."""
    caja = CuentasContables(
        tenant_id=tenant_id,
        codigo="1105",
        nombre="Caja general",
        tipo_cuenta="ACTIVO",
        nivel=4,
        naturaleza="DEBITO",
        acepta_movimiento=True,
        estado=True,
    )
    ventas = CuentasContables(
        tenant_id=tenant_id,
        codigo="4135",
        nombre="Comercio al por menor",
        tipo_cuenta="INGRESO",
        nivel=4,
        naturaleza="CREDITO",
        acepta_movimiento=True,
        estado=True,
    )
    cmv = CuentasContables(
        tenant_id=tenant_id,
        codigo="6135",
        nombre="CMV mercancías",
        tipo_cuenta="COSTOS",
        nivel=4,
        naturaleza="DEBITO",
        acepta_movimiento=True,
        estado=True,
    )
    inventario = CuentasContables(
        tenant_id=tenant_id,
        codigo="1435",
        nombre="Mercancías en almacén",
        tipo_cuenta="ACTIVO",
        nivel=4,
        naturaleza="DEBITO",
        acepta_movimiento=True,
        estado=True,
    )
    db.add_all([caja, ventas, cmv, inventario])
    db.flush()

    config_venta = ConfiguracionContable(
        tenant_id=tenant_id,
        concepto="VENTA_CONTADO",
        cuenta_debito_id=caja.id,
        cuenta_credito_id=ventas.id,
        descripcion="Venta de contado",
    )
    config_cogs = ConfiguracionContable(
        tenant_id=tenant_id,
        concepto="COSTO_VENTAS",
        cuenta_debito_id=cmv.id,
        cuenta_credito_id=inventario.id,
        descripcion="Costo de ventas",
    )
    db.add_all([config_venta, config_cogs])

    seq_facturas = Secuencias(
        tenant_id=tenant_id,
        nombre="FACTURAS",
        prefijo="FAC-",
        siguiente_numero=1,
        longitud_numero=6,
    )
    seq_asientos = Secuencias(
        tenant_id=tenant_id,
        nombre="ASIENTOS",
        prefijo="AS-",
        siguiente_numero=1,
        longitud_numero=6,
    )
    db.add_all([seq_facturas, seq_asientos])
    db.flush()

    return caja, ventas, cmv, inventario


def _seed_producto_con_inventario(db, tenant_id: UUID, cpp: Decimal, cantidad: Decimal) -> Productos:
    producto = Productos(
        tenant_id=tenant_id,
        nombre="Vela Test COGS",
        codigo_interno="COGS-001",
        precio_venta=Decimal("200"),
        porcentaje_iva=Decimal("0"),
        categoria="Producto_Propio",
        unidad_medida="UNIDAD",
        estado=True,
        maneja_inventario=True,
    )
    db.add(producto)
    db.flush()

    inv = Inventarios(
        tenant_id=tenant_id,
        producto_id=producto.id,
        cantidad_disponible=cantidad,
        costo_promedio_ponderado=cpp,
        valor_total=cpp * cantidad,
    )
    db.add(inv)
    db.flush()
    return producto


def _seed_cliente(db, tenant_id: UUID) -> Terceros:
    tercero = Terceros(
        tenant_id=tenant_id,
        nombre="Cliente COGS Test",
        tipo_documento="CC",
        numero_documento="987654321",
        tipo_tercero="CLIENTE",
    )
    db.add(tercero)
    db.flush()
    return tercero


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_anulacion_factura_revierte_cogs(client, db_session, tenant_admin_token):
    """
    End-to-end: emitir factura (5 units @ CPP=100) creates COGS debit $500 on 6135.
    Anular must reverse it → net 6135 = 0.
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])
    headers = _headers(tenant_admin_token)

    _, _, cmv, _ = _seed_cuentas(db_session, tenant_id)
    producto = _seed_producto_con_inventario(db_session, tenant_id, cpp=Decimal("100"), cantidad=Decimal("10"))
    cliente = _seed_cliente(db_session, tenant_id)
    db_session.commit()

    # 1. Create factura (PENDIENTE)
    resp = client.post(
        "/api/v1/facturas/",
        json={
            "tercero_id": str(cliente.id),
            "fecha_venta": str(date.today()),
            "detalles": [
                {
                    "producto_id": str(producto.id),
                    "cantidad": 5,
                    "precio_unitario": 200,
                    "descuento": 0,
                    "porcentaje_iva": 0,
                }
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    factura_id = resp.json()["id"]

    # 2. Emit factura → FACTURADA + COGS entry
    resp = client.post(f"/api/v1/facturas/{factura_id}/emitir", headers=headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    # Verify COGS debit created: 6135.debito = 500
    db_session.expire_all()
    detalles_post_emit = (
        db_session.query(DetallesAsiento)
        .filter(DetallesAsiento.cuenta_id == cmv.id, DetallesAsiento.tenant_id == tenant_id)
        .all()
    )
    total_debito_before = sum(d.debito for d in detalles_post_emit)
    assert total_debito_before == Decimal("500"), f"Expected COGS debit=500 after emission, got {total_debito_before}"

    # 3. Anular factura → ANULADA + COGS reversal
    resp = client.post(f"/api/v1/facturas/{factura_id}/anular", headers=headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    # 4. Verify net COGS (debito - credito) = 0
    db_session.expire_all()
    detalles_post_anul = (
        db_session.query(DetallesAsiento)
        .filter(DetallesAsiento.cuenta_id == cmv.id, DetallesAsiento.tenant_id == tenant_id)
        .all()
    )
    total_debito = sum(d.debito for d in detalles_post_anul)
    total_credito = sum(d.credito for d in detalles_post_anul)
    net_cogs = total_debito - total_credito

    assert net_cogs == Decimal("0"), (
        f"Net COGS on 6135 should be 0 after cancellation. "
        f"debito={total_debito}, credito={total_credito}, net={net_cogs}"
    )
