"""
Test backend role-based access control (RBAC).
Verifies that role restrictions are enforced at the API level.
"""

from decimal import Decimal


def test_vendedor_cannot_delete_producto(client, vendedor_token, tenant_admin_token, db_session):
    """Vendedor role should not be able to delete products (403 Forbidden)."""
    from uuid import uuid4

    from app.datos.modelos import Productos

    tenant_id = uuid4(tenant_admin_token["tenant_id"])

    # Create a product as admin
    producto = Productos(
        tenant_id=tenant_id,
        nombre="Test Product",
        codigo_interno="PROD-001",
        precio_venta=Decimal("10000"),
        porcentaje_iva=Decimal("19"),
        categoria="Producto_Propio",
        estado=True,
    )
    db_session.add(producto)
    db_session.commit()

    # Try to delete as vendedor
    response = client.delete(
        f"/api/v1/productos/{producto.id}",
        headers={"Authorization": f"Bearer {vendedor_token['token']}", "X-Tenant-ID": vendedor_token["tenant_id"]},
    )

    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    assert "permisos" in response.json().get("detail", "").lower()


def test_contador_can_access_contabilidad(client, contador_token):
    """Contador can access accounting routes."""
    response = client.get(
        "/api/v1/contabilidad/asientos",
        headers={"Authorization": f"Bearer {contador_token['token']}", "X-Tenant-ID": contador_token["tenant_id"]},
    )

    assert response.status_code == 200, f"Contador should access accounting, got {response.status_code}"


def test_vendedor_cannot_access_contabilidad(client, vendedor_token):
    """Vendedor cannot access accounting routes (403 Forbidden)."""
    response = client.get(
        "/api/v1/contabilidad/asientos",
        headers={"Authorization": f"Bearer {vendedor_token['token']}", "X-Tenant-ID": vendedor_token["tenant_id"]},
    )

    assert response.status_code == 403, f"Expected 403, got {response.status_code}"


def test_admin_can_anular_factura(client, tenant_admin_token, db_session):
    """Only admin can annul invoices."""
    from uuid import uuid4

    from app.datos.modelos import Terceros, Ventas

    tenant_id = uuid4(tenant_admin_token["tenant_id"])

    # Create client
    tercero = Terceros(
        tenant_id=tenant_id,
        nombre="Test Cliente",
        tipo_documento="CC",
        numero_documento="123456",
        tipo_tercero="CLIENTE",
    )
    db_session.add(tercero)
    db_session.flush()

    # Create invoice
    factura = Ventas(
        tenant_id=tenant_id,
        numero_venta="FAC-001",
        tercero_id=tercero.id,
        estado="FACTURADA",
        subtotal=Decimal("10000"),
        total_impuestos=Decimal("1900"),
        total_venta=Decimal("11900"),
    )
    db_session.add(factura)
    db_session.commit()

    # Admin can annul
    response = client.post(
        f"/api/v1/facturas/{factura.id}/anular",
        headers={
            "Authorization": f"Bearer {tenant_admin_token['token']}",
            "X-Tenant-ID": tenant_admin_token["tenant_id"],
        },
    )

    assert response.status_code == 200, f"Admin should annul invoice, got {response.status_code}"


def test_vendedor_cannot_anular_factura(client, vendedor_token, tenant_admin_token, db_session):
    """Vendedor cannot annul invoices (403 Forbidden)."""
    from uuid import uuid4

    from app.datos.modelos import Terceros, Ventas

    tenant_id = uuid4(tenant_admin_token["tenant_id"])

    tercero = Terceros(
        tenant_id=tenant_id,
        nombre="Test Cliente",
        tipo_documento="CC",
        numero_documento="123456",
        tipo_tercero="CLIENTE",
    )
    db_session.add(tercero)
    db_session.flush()

    factura = Ventas(
        tenant_id=tenant_id,
        numero_venta="FAC-002",
        tercero_id=tercero.id,
        estado="FACTURADA",
        subtotal=Decimal("10000"),
        total_impuestos=Decimal("1900"),
        total_venta=Decimal("11900"),
    )
    db_session.add(factura)
    db_session.commit()

    response = client.post(
        f"/api/v1/facturas/{factura.id}/anular",
        headers={"Authorization": f"Bearer {vendedor_token['token']}", "X-Tenant-ID": vendedor_token["tenant_id"]},
    )

    assert response.status_code == 403, f"Expected 403, got {response.status_code}"


def test_superadmin_bypasses_tenant_role_checks(client, db_session):
    """Superadmin can access any tenant route regardless of tenant role."""
    from uuid import uuid4

    from app.datos.modelos import Usuarios
    from app.utils.seguridad import create_access_token, hash_password

    # Create superadmin user
    superadmin = Usuarios(
        email="superadmin@test.com",
        nombre="Super Admin",
        hash_password=hash_password("test123"),
        rol="admin",
        estado=True,
        es_superadmin=True,
    )
    db_session.add(superadmin)
    db_session.commit()

    # Create token with ANY tenant (superadmin bypasses role checks)
    token = create_access_token(
        data={"sub": str(superadmin.id), "email": superadmin.email, "rol": "admin"},
        tenant_id=uuid4(),
        rol_en_tenant="vendedor",  # Even with vendedor role, superadmin should access admin routes
    )

    # Superadmin should access contabilidad even with vendedor role
    response = client.get(
        "/api/v1/contabilidad/asientos", headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(uuid4())}
    )

    # Should succeed because es_superadmin bypasses role checks
    assert response.status_code in [200, 404], f"Superadmin should bypass role check, got {response.status_code}"
