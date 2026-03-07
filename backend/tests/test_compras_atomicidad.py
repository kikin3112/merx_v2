"""
Tests for C-03 audit fix: purchase receiving is atomic with accounting entry.

Verifies that when ConfiguracionContable (COMPRA_CONTADO) is missing,
the PUT /compras/{id}/recibir endpoint must fail and roll back:
- estado stays PENDIENTE
- inventory stock does NOT increase
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from app.datos.modelos import (
    Compras,
    ComprasDetalle,
    EstadoCompra,
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


def _seed_proveedor(db, tenant_id: UUID) -> Terceros:
    prov = Terceros(
        tenant_id=tenant_id,
        nombre="Proveedor Atomicidad",
        tipo_documento="NIT",
        numero_documento="900777001-5",
        tipo_tercero="PROVEEDOR",
    )
    db.add(prov)
    db.flush()
    return prov


def _seed_producto(db, tenant_id: UUID) -> Productos:
    prod = Productos(
        tenant_id=tenant_id,
        nombre="Insumo Atomicidad",
        codigo_interno="ATOM-001",
        precio_venta=Decimal("5000"),
        porcentaje_iva=Decimal("0"),
        categoria="Insumo",
        unidad_medida="UNIDAD",
        estado=True,
        maneja_inventario=True,
    )
    db.add(prod)
    db.flush()

    inv = Inventarios(
        tenant_id=tenant_id,
        producto_id=prod.id,
        cantidad_disponible=Decimal("0"),
        costo_promedio_ponderado=Decimal("0"),
        valor_total=Decimal("0"),
    )
    db.add(inv)
    db.flush()
    return prod


def _seed_compra(db, tenant_id: UUID, proveedor_id: UUID, producto_id: UUID) -> Compras:
    seq = Secuencias(
        tenant_id=tenant_id,
        nombre="COMPRAS",
        prefijo="COM-",
        siguiente_numero=1,
        longitud_numero=6,
    )
    db.add(seq)
    db.flush()

    compra = Compras(
        tenant_id=tenant_id,
        numero_compra="COM-000001",
        tercero_id=proveedor_id,
        fecha_compra=date.today(),
        estado=EstadoCompra.PENDIENTE,
    )
    db.add(compra)
    db.flush()

    det = ComprasDetalle(
        tenant_id=tenant_id,
        compra_id=compra.id,
        producto_id=producto_id,
        cantidad=Decimal("10"),
        precio_unitario=Decimal("1000"),
        descuento=Decimal("0"),
        porcentaje_iva=Decimal("0"),
    )
    db.add(det)
    db.flush()
    return compra


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_recibir_compra_sin_config_contable_hace_rollback(client, db_session, tenant_admin_token):
    """
    PUT /compras/{id}/recibir without COMPRA_CONTADO config must fail.
    - HTTP 400 (not 200)
    - estado stays PENDIENTE (rollback)
    - inventory stays at 0 (rollback)
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])
    headers = _headers(tenant_admin_token)

    proveedor = _seed_proveedor(db_session, tenant_id)
    producto = _seed_producto(db_session, tenant_id)
    compra = _seed_compra(db_session, tenant_id, proveedor.id, producto.id)
    # Deliberately NO ConfiguracionContable for COMPRA_CONTADO
    db_session.commit()

    stock_antes = (
        db_session.query(Inventarios)
        .filter(Inventarios.producto_id == producto.id, Inventarios.tenant_id == tenant_id)
        .first()
    ).cantidad_disponible

    resp = client.put(
        f"/api/v1/compras/{compra.id}/recibir",
        headers=headers,
    )

    # Must fail — accounting config required
    assert resp.status_code in (
        400,
        500,
    ), f"Expected 400/500 when accounting config missing, got {resp.status_code}: {resp.text}"

    db_session.expire_all()

    # Estado should still be PENDIENTE (rollback)
    compra_db = db_session.query(Compras).filter(Compras.id == compra.id).first()
    assert (
        compra_db.estado == EstadoCompra.PENDIENTE
    ), f"Expected estado=PENDIENTE after rollback, got {compra_db.estado}"

    # Stock should not have increased (rollback)
    stock_despues = (
        db_session.query(Inventarios)
        .filter(Inventarios.producto_id == producto.id, Inventarios.tenant_id == tenant_id)
        .first()
    ).cantidad_disponible
    assert (
        stock_despues == stock_antes
    ), f"Expected stock unchanged after rollback, was {stock_antes}, now {stock_despues}"


def test_recibir_compra_con_config_contable_actualiza_inventario(client, db_session, tenant_admin_token):
    """
    PUT /compras/{id}/recibir with COMPRA_CONTADO config → HTTP 200,
    estado=RECIBIDA, inventory increases.
    """
    from app.datos.modelos import ConfiguracionContable, CuentasContables

    tenant_id = UUID(tenant_admin_token["tenant_id"])
    headers = _headers(tenant_admin_token)

    proveedor = _seed_proveedor(db_session, tenant_id)
    producto = _seed_producto(db_session, tenant_id)
    compra = _seed_compra(db_session, tenant_id, proveedor.id, producto.id)

    # Seed required accounts and config
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
    inventario_cuenta = CuentasContables(
        tenant_id=tenant_id,
        codigo="1435",
        nombre="Mercancías",
        tipo_cuenta="ACTIVO",
        nivel=4,
        naturaleza="DEBITO",
        acepta_movimiento=True,
        estado=True,
    )
    db_session.add_all([caja, inventario_cuenta])
    db_session.flush()

    config = ConfiguracionContable(
        tenant_id=tenant_id,
        concepto="COMPRA_CONTADO",
        cuenta_debito_id=inventario_cuenta.id,
        cuenta_credito_id=caja.id,
        descripcion="Compra de contado",
    )
    seq_asientos = Secuencias(
        tenant_id=tenant_id,
        nombre="ASIENTOS",
        prefijo="AS-",
        siguiente_numero=1,
        longitud_numero=6,
    )
    db_session.add_all([config, seq_asientos])
    db_session.commit()

    resp = client.put(f"/api/v1/compras/{compra.id}/recibir", headers=headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    db_session.expire_all()
    compra_db = db_session.query(Compras).filter(Compras.id == compra.id).first()
    assert compra_db.estado == EstadoCompra.RECIBIDA, f"Expected RECIBIDA, got {compra_db.estado}"

    stock = (db_session.query(Inventarios).filter(Inventarios.producto_id == producto.id).first()).cantidad_disponible
    assert stock == Decimal("10"), f"Expected stock=10 after receiving, got {stock}"
