"""
Tests for C3 audit fix: costo_unitario persisted on VentasDetalle at sale time.

Verifies that when a venta is created, each VentasDetalle row captures the
CPP (Costo Promedio Ponderado) from Inventarios at the moment of the sale.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from app.datos.modelos import (
    Inventarios,
    Productos,
    Secuencias,
    Terceros,
    VentasDetalle,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _headers(token_data: dict) -> dict:
    return {
        "Authorization": f"Bearer {token_data['token']}",
        "X-Tenant-ID": token_data["tenant_id"],
    }


def _seed_producto(db, tenant_id: UUID) -> Productos:
    producto = Productos(
        tenant_id=tenant_id,
        nombre="Producto CPP Test",
        codigo_interno="CPP-001",
        precio_venta=Decimal("20000"),
        porcentaje_iva=Decimal("0"),
        categoria="Producto_Propio",
        unidad_medida="UNIDAD",
        estado=True,
        maneja_inventario=True,
    )
    db.add(producto)
    db.flush()
    return producto


def _seed_inventario(db, tenant_id: UUID, producto_id: UUID, cpp: Decimal, cantidad: Decimal) -> Inventarios:
    inventario = Inventarios(
        tenant_id=tenant_id,
        producto_id=producto_id,
        cantidad_disponible=cantidad,
        costo_promedio_ponderado=cpp,
        valor_total=cpp * cantidad,
    )
    db.add(inventario)
    db.flush()
    return inventario


def _seed_cliente(db, tenant_id: UUID) -> Terceros:
    tercero = Terceros(
        tenant_id=tenant_id,
        nombre="Cliente CPP Test",
        tipo_documento="CC",
        numero_documento="123456789",
        tipo_tercero="CLIENTE",
    )
    db.add(tercero)
    db.flush()
    return tercero


def _seed_secuencia_facturas(db, tenant_id: UUID) -> None:
    secuencia = Secuencias(
        tenant_id=tenant_id,
        nombre="FACTURAS",
        prefijo="FAC-",
        siguiente_numero=1,
        longitud_numero=6,
    )
    db.add(secuencia)
    db.flush()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_crear_venta_persiste_costo_unitario(client, db_session, tenant_admin_token):
    """POST /api/v1/ventas/ — VentasDetalle.costo_unitario must equal CPP from Inventarios."""
    tenant_id = UUID(tenant_admin_token["tenant_id"])

    producto = _seed_producto(db_session, tenant_id)
    cpp_esperado = Decimal("7500")
    _seed_inventario(db_session, tenant_id, producto.id, cpp=cpp_esperado, cantidad=Decimal("100"))
    cliente = _seed_cliente(db_session, tenant_id)
    _seed_secuencia_facturas(db_session, tenant_id)
    db_session.commit()

    payload = {
        "tercero_id": str(cliente.id),
        "fecha_venta": str(date.today()),
        "detalles": [
            {
                "producto_id": str(producto.id),
                "cantidad": 2,
                "precio_unitario": 20000,
                "descuento": 0,
                "porcentaje_iva": 0,
            }
        ],
    }

    response = client.post(
        "/api/v1/ventas/",
        json=payload,
        headers=_headers(tenant_admin_token),
    )

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    body = response.json()
    venta_id = UUID(body["id"])

    # Fetch the VentasDetalle from DB
    detalle = (
        db_session.query(VentasDetalle)
        .filter(VentasDetalle.venta_id == venta_id, VentasDetalle.tenant_id == tenant_id)
        .first()
    )

    assert detalle is not None, "VentasDetalle should exist after venta creation"
    assert (
        detalle.costo_unitario == cpp_esperado
    ), f"Expected costo_unitario={cpp_esperado}, got {detalle.costo_unitario}"


def test_crear_venta_sin_inventario_costo_unitario_cero(client, db_session, tenant_admin_token):
    """POST /api/v1/ventas/ — costo_unitario is 0 when no Inventarios row exists."""
    tenant_id = UUID(tenant_admin_token["tenant_id"])

    producto = _seed_producto(db_session, tenant_id)
    # No Inventarios row seeded — CPP should default to 0
    cliente = _seed_cliente(db_session, tenant_id)
    _seed_secuencia_facturas(db_session, tenant_id)
    db_session.commit()

    payload = {
        "tercero_id": str(cliente.id),
        "fecha_venta": str(date.today()),
        "detalles": [
            {
                "producto_id": str(producto.id),
                "cantidad": 1,
                "precio_unitario": 20000,
                "descuento": 0,
                "porcentaje_iva": 0,
            }
        ],
    }

    response = client.post(
        "/api/v1/ventas/",
        json=payload,
        headers=_headers(tenant_admin_token),
    )

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    body = response.json()
    venta_id = UUID(body["id"])

    detalle = (
        db_session.query(VentasDetalle)
        .filter(VentasDetalle.venta_id == venta_id, VentasDetalle.tenant_id == tenant_id)
        .first()
    )

    assert detalle is not None, "VentasDetalle should exist"
    assert detalle.costo_unitario == Decimal(
        "0.00"
    ), f"Expected costo_unitario=0.00 when no inventory, got {detalle.costo_unitario}"
