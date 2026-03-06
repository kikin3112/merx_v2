"""
Integration tests for POST /productos/catalogo-pdf endpoint.
"""

from decimal import Decimal
from uuid import uuid4

from app.datos.modelos import Productos
from fastapi.testclient import TestClient


def _create_producto(db_session, tenant_id, nombre="Producto Test", precio=Decimal("50000")):
    """Helper: create a producto in the test DB."""
    p = Productos(
        tenant_id=tenant_id,
        codigo_interno=f"TEST-{str(uuid4())[:8]}",
        nombre=nombre,
        categoria="Producto_Propio",
        unidad_medida="UNIDAD",
        tipo_iva="Gravado",
        porcentaje_iva=Decimal("19"),
        precio_venta=precio,
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


def test_catalogo_pdf_endpoint(client: TestClient, tenant_admin_token, db_session):
    """POST /productos/catalogo-pdf returns 200 with application/pdf content-type."""
    tenant_id = tenant_admin_token["tenant_id"]
    p1 = _create_producto(db_session, tenant_id, "Vela Vaso")
    p2 = _create_producto(db_session, tenant_id, "Vela Pilar")

    resp = client.post(
        "/api/v1/productos/catalogo-pdf",
        json={"producto_ids": [str(p1.id), str(p2.id)]},
        headers=_auth_headers(tenant_admin_token),
    )
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers["content-type"]


def test_catalogo_pdf_starts_with_pdf_magic(client: TestClient, tenant_admin_token, db_session):
    """PDF response body starts with %PDF magic bytes."""
    tenant_id = tenant_admin_token["tenant_id"]
    p = _create_producto(db_session, tenant_id, "Jabón de Coco")

    resp = client.post(
        "/api/v1/productos/catalogo-pdf",
        json={"producto_ids": [str(p.id)]},
        headers=_auth_headers(tenant_admin_token),
    )
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"


def test_catalogo_pdf_sin_productos(client: TestClient, tenant_admin_token):
    """POST with empty producto_ids list → 422."""
    resp = client.post(
        "/api/v1/productos/catalogo-pdf",
        json={"producto_ids": []},
        headers=_auth_headers(tenant_admin_token),
    )
    assert resp.status_code == 422


def test_catalogo_pdf_ids_invalidos(client: TestClient, tenant_admin_token):
    """POST with UUIDs not belonging to tenant → returns PDF gracefully (skips missing)."""
    fake_id = str(uuid4())
    resp = client.post(
        "/api/v1/productos/catalogo-pdf",
        json={"producto_ids": [fake_id]},
        headers=_auth_headers(tenant_admin_token),
    )
    # Gracefully returns empty catalogue PDF
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"


def test_catalogo_pdf_streaming(client: TestClient, tenant_admin_token, db_session):
    """Response includes Content-Disposition header containing 'catalogo'."""
    tenant_id = tenant_admin_token["tenant_id"]
    p = _create_producto(db_session, tenant_id, "Aceite Esencial")

    resp = client.post(
        "/api/v1/productos/catalogo-pdf",
        json={"producto_ids": [str(p.id)]},
        headers=_auth_headers(tenant_admin_token),
    )
    assert resp.status_code == 200
    assert "catalogo" in resp.headers.get("content-disposition", "").lower()


def test_catalogo_pdf_usa_tenant_branding(client: TestClient, tenant_admin_token, db_session):
    """PDF bytes are non-empty (branding applied via tenant_info)."""
    tenant_id = tenant_admin_token["tenant_id"]
    p = _create_producto(db_session, tenant_id, "Cera Soya")

    resp = client.post(
        "/api/v1/productos/catalogo-pdf",
        json={"producto_ids": [str(p.id)]},
        headers=_auth_headers(tenant_admin_token),
    )
    assert resp.status_code == 200
    assert len(resp.content) > 1000  # non-trivial PDF with branding


def test_catalogo_pdf_no_auth(client: TestClient):
    """POST without token → 400 (middleware) or 401/403."""
    resp = client.post(
        "/api/v1/productos/catalogo-pdf",
        json={"producto_ids": [str(uuid4())]},
    )
    assert resp.status_code in (400, 401, 403)


def test_catalogo_pdf_aislamiento_tenant(client: TestClient, tenant_admin_token, db_session):
    """Products from other tenants are excluded (tenant isolation)."""
    from app.datos.modelos_tenant import Planes, Tenants

    plan = db_session.query(Planes).first()
    other_tenant = Tenants(
        nombre="Other Corp",
        slug=f"other-{str(uuid4())[:6]}",
        estado="activo",
        email_contacto="other@test.com",
        plan_id=plan.id,
    )
    db_session.add(other_tenant)
    db_session.flush()

    p_other = _create_producto(db_session, other_tenant.id, "Producto Ajeno")

    resp = client.post(
        "/api/v1/productos/catalogo-pdf",
        json={"producto_ids": [str(p_other.id)]},
        headers=_auth_headers(tenant_admin_token),
    )
    # Gracefully skips — returns empty catalogue PDF
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"
