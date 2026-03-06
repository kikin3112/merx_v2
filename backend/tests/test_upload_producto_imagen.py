"""
Integration tests for product image upload/delete endpoints.

Endpoints:
  POST /api/v1/productos/{id}/imagen
  DELETE /api/v1/productos/{id}/imagen
"""

from decimal import Decimal
from io import BytesIO
from unittest.mock import patch
from uuid import uuid4

from app.datos.modelos import Productos
from fastapi.testclient import TestClient


def _create_producto(db_session, tenant_id, nombre="Producto Imagen Test"):
    """Helper: create a producto in the test DB."""
    p = Productos(
        tenant_id=tenant_id,
        codigo_interno=f"IMG-{str(uuid4())[:8]}",
        nombre=nombre,
        categoria="Producto_Propio",
        unidad_medida="UNIDAD",
        tipo_iva="Gravado",
        porcentaje_iva=Decimal("19"),
        precio_venta=Decimal("30000"),
        estado=True,
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


def _auth_headers(token_data: dict) -> dict:
    return {
        "Authorization": f"Bearer {token_data['token']}",
        "X-Tenant-ID": token_data["tenant_id"],
    }


def _png_bytes() -> bytes:
    """Minimal valid 1x1 PNG."""
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
        b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_upload_imagen_producto(client: TestClient, tenant_admin_token, db_session):
    """POST /productos/{id}/imagen with PNG → 200, imagen_s3_key returned."""
    tenant_id = tenant_admin_token["tenant_id"]
    p = _create_producto(db_session, tenant_id)

    fake_key = f"tenants/{tenant_id}/products/{p.id}.png"

    with (
        patch(
            "app.servicios.servicio_almacenamiento.ServicioAlmacenamiento.subir_imagen",
            return_value=fake_key,
        ),
        patch(
            "app.servicios.servicio_almacenamiento.ServicioAlmacenamiento.is_enabled",
            new_callable=lambda: property(lambda self: True),
        ),
    ):
        resp = client.post(
            f"/api/v1/productos/{p.id}/imagen",
            files={"file": ("foto.png", BytesIO(_png_bytes()), "image/png")},
            headers=_auth_headers(tenant_admin_token),
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "imagen_s3_key" in data


def test_upload_imagen_formato_invalido(client: TestClient, tenant_admin_token, db_session):
    """POST with .gif content-type → 422."""
    tenant_id = tenant_admin_token["tenant_id"]
    p = _create_producto(db_session, tenant_id)

    resp = client.post(
        f"/api/v1/productos/{p.id}/imagen",
        files={"file": ("animated.gif", BytesIO(b"GIF89a"), "image/gif")},
        headers=_auth_headers(tenant_admin_token),
    )
    assert resp.status_code == 422


def test_upload_imagen_producto_no_encontrado(client: TestClient, tenant_admin_token):
    """POST to non-existent product → 404."""
    fake_id = str(uuid4())
    resp = client.post(
        f"/api/v1/productos/{fake_id}/imagen",
        files={"file": ("foto.png", BytesIO(_png_bytes()), "image/png")},
        headers=_auth_headers(tenant_admin_token),
    )
    assert resp.status_code == 404


def test_delete_imagen_producto(client: TestClient, tenant_admin_token, db_session):
    """DELETE /productos/{id}/imagen → 204, imagen_s3_key set to None."""
    tenant_id = tenant_admin_token["tenant_id"]
    p = _create_producto(db_session, tenant_id)
    p.imagen_s3_key = "tenants/test/products/test.png"
    db_session.commit()

    with (
        patch(
            "app.servicios.servicio_almacenamiento.ServicioAlmacenamiento.eliminar_archivo",
            return_value=True,
        ),
        patch(
            "app.servicios.servicio_almacenamiento.ServicioAlmacenamiento.is_enabled",
            new_callable=lambda: property(lambda self: True),
        ),
    ):
        resp = client.delete(
            f"/api/v1/productos/{p.id}/imagen",
            headers=_auth_headers(tenant_admin_token),
        )

    assert resp.status_code == 204

    db_session.refresh(p)
    assert p.imagen_s3_key is None


def test_delete_imagen_producto_sin_imagen(client: TestClient, tenant_admin_token, db_session):
    """DELETE on product without image → 204 (idempotent)."""
    tenant_id = tenant_admin_token["tenant_id"]
    p = _create_producto(db_session, tenant_id)

    resp = client.delete(
        f"/api/v1/productos/{p.id}/imagen",
        headers=_auth_headers(tenant_admin_token),
    )
    assert resp.status_code == 204
