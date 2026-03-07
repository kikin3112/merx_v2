"""
Tests for PUT /compras/{id}/recibir endpoint (C2 audit fix).

Verifies:
1. PENDIENTE compra transitions to RECIBIDA, inventory ENTRADA created, accounting entry created.
2. Already RECIBIDA compra returns 400.
3. Non-existent compra returns 404.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from app.datos.modelos import (
    AsientosContables,
    Compras,
    ComprasDetalle,
    ConfiguracionContable,
    CuentasContables,
    EstadoCompra,
    Inventarios,
    MovimientosInventario,
    Productos,
    Secuencias,
    Terceros,
    TipoMovimiento,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _headers(token_data: dict) -> dict:
    return {
        "Authorization": f"Bearer {token_data['token']}",
        "X-Tenant-ID": token_data["tenant_id"],
    }


def _seed_tercero_proveedor(db, tenant_id: UUID) -> Terceros:
    tercero = Terceros(
        tenant_id=tenant_id,
        nombre="Proveedor Test S.A.S.",
        tipo_documento="NIT",
        numero_documento="900999001-1",
        tipo_tercero="PROVEEDOR",
    )
    db.add(tercero)
    db.flush()
    return tercero


def _seed_producto(db, tenant_id: UUID) -> Productos:
    producto = Productos(
        tenant_id=tenant_id,
        nombre="Insumo Test",
        codigo_interno="INS-001",
        precio_venta=Decimal("10000"),
        porcentaje_iva=Decimal("0"),
        categoria="Insumo",
        unidad_medida="UNIDAD",
        estado=True,
        maneja_inventario=True,
    )
    db.add(producto)
    db.flush()
    return producto


def _seed_config_contable(db, tenant_id: UUID):
    """Seeds 2 CuentasContables (1435, 1105) + ConfiguracionContable(COMPRA_CONTADO) + ASIENTOS sequence."""
    cuenta_inventario = CuentasContables(
        tenant_id=tenant_id,
        codigo="1435",
        nombre="Inventario de mercancías",
        tipo_cuenta="ACTIVO",
        nivel=4,
        naturaleza="DEBITO",
        acepta_movimiento=True,
        estado=True,
    )
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
    db.add(cuenta_inventario)
    db.add(cuenta_caja)
    db.flush()

    config = ConfiguracionContable(
        tenant_id=tenant_id,
        concepto="COMPRA_CONTADO",
        cuenta_debito_id=cuenta_inventario.id,
        cuenta_credito_id=cuenta_caja.id,
        descripcion="Compra de contado",
    )
    db.add(config)

    # ASIENTOS sequence required by generar_numero_secuencia inside ServicioContabilidad
    secuencia_asientos = Secuencias(
        tenant_id=tenant_id,
        nombre="ASIENTOS",
        prefijo="AS-",
        siguiente_numero=1,
        longitud_numero=6,
    )
    db.add(secuencia_asientos)
    db.flush()
    return cuenta_inventario, cuenta_caja, config


def _seed_compra(db, tenant_id: UUID, tercero_id, producto_id, estado=EstadoCompra.PENDIENTE) -> Compras:
    compra = Compras(
        tenant_id=tenant_id,
        numero_compra=f"COMP-TEST-{uuid4().hex[:6].upper()}",
        tercero_id=tercero_id,
        fecha_compra=date.today(),
        estado=estado,
    )
    db.add(compra)
    db.flush()

    detalle = ComprasDetalle(
        tenant_id=tenant_id,
        compra_id=compra.id,
        producto_id=producto_id,
        cantidad=Decimal("10"),
        precio_unitario=Decimal("5000"),
        descuento=Decimal("0"),
        porcentaje_iva=Decimal("0"),
    )
    db.add(detalle)
    db.flush()
    return compra


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_recibir_compra_actualiza_inventario_y_crea_asiento(client, db_session, tenant_admin_token):
    """PUT /compras/{id}/recibir — happy path:
    - estado → RECIBIDA
    - MovimientosInventario ENTRADA created
    - Inventarios cantidad=10, CPP=5000
    - AsientosContables tipo_asiento=COMPRAS created
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])

    tercero = _seed_tercero_proveedor(db_session, tenant_id)
    producto = _seed_producto(db_session, tenant_id)
    _seed_config_contable(db_session, tenant_id)
    compra = _seed_compra(db_session, tenant_id, tercero.id, producto.id)
    db_session.commit()

    response = client.put(
        f"/api/v1/compras/{compra.id}/recibir",
        headers=_headers(tenant_admin_token),
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["estado"] == "RECIBIDA"

    # Inventory updated
    inv = (
        db_session.query(Inventarios)
        .filter(
            Inventarios.tenant_id == tenant_id,
            Inventarios.producto_id == producto.id,
        )
        .first()
    )
    assert inv is not None, "Inventarios row should exist"
    assert inv.cantidad_disponible == Decimal("10"), f"Expected 10, got {inv.cantidad_disponible}"
    assert inv.costo_promedio_ponderado == Decimal("5000"), f"Expected CPP=5000, got {inv.costo_promedio_ponderado}"

    # MovimientosInventario ENTRADA created
    mov = (
        db_session.query(MovimientosInventario)
        .filter(
            MovimientosInventario.tenant_id == tenant_id,
            MovimientosInventario.producto_id == producto.id,
            MovimientosInventario.tipo_movimiento == TipoMovimiento.ENTRADA,
        )
        .first()
    )
    assert mov is not None, "MovimientosInventario ENTRADA should exist"

    # AsientosContables COMPRAS created
    asiento = (
        db_session.query(AsientosContables)
        .filter(
            AsientosContables.tenant_id == tenant_id,
            AsientosContables.tipo_asiento == "COMPRAS",
        )
        .first()
    )
    assert asiento is not None, "AsientosContables COMPRAS should exist"


def test_recibir_compra_ya_recibida_falla(client, db_session, tenant_admin_token):
    """PUT /compras/{id}/recibir on already RECIBIDA compra → 400."""
    tenant_id = UUID(tenant_admin_token["tenant_id"])

    tercero = _seed_tercero_proveedor(db_session, tenant_id)
    producto = _seed_producto(db_session, tenant_id)
    compra = _seed_compra(db_session, tenant_id, tercero.id, producto.id, estado=EstadoCompra.RECIBIDA)
    db_session.commit()

    response = client.put(
        f"/api/v1/compras/{compra.id}/recibir",
        headers=_headers(tenant_admin_token),
    )

    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"


def test_recibir_compra_no_encontrada(client, tenant_admin_token):
    """PUT /compras/{random_uuid}/recibir → 404."""
    random_id = uuid4()

    response = client.put(
        f"/api/v1/compras/{random_id}/recibir",
        headers=_headers(tenant_admin_token),
    )

    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
