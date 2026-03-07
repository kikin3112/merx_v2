"""
Tests for safe_get_by_id utility — tenant-scoped, soft-delete-aware record lookup.
"""

from datetime import datetime
from uuid import uuid4

import pytest
from app.datos.modelos import Productos
from app.utils.db_helpers import safe_get_by_id
from fastapi import HTTPException
from sqlalchemy.orm import Session


def _make_producto(db: Session, tenant_id, *, deleted_at=None) -> Productos:
    """Helper: insert a minimal Productos row and return it."""
    producto = Productos(
        tenant_id=tenant_id,
        nombre="Producto Test",
        codigo_interno=f"TEST-{uuid4().hex[:8]}",
        precio_venta=10000,
        porcentaje_iva=0,
        maneja_inventario=False,
        categoria="Insumo",
        unidad_medida="UNIDAD",
        tipo_iva="Excluido",
        deleted_at=deleted_at,
    )
    db.add(producto)
    db.flush()
    return producto


def test_safe_get_finds_existing_record(db_session: Session, tenant_admin_token):
    """safe_get_by_id returns the record when id + tenant_id match and not deleted."""
    tenant_id = tenant_admin_token["tenant"].id
    producto = _make_producto(db_session, tenant_id)

    result = safe_get_by_id(db_session, Productos, producto.id, tenant_id)

    assert result.id == producto.id


def test_safe_get_raises_404_for_missing(db_session: Session, tenant_admin_token):
    """safe_get_by_id raises HTTP 404 when no record exists for a random UUID."""
    tenant_id = tenant_admin_token["tenant"].id

    with pytest.raises(HTTPException) as exc_info:
        safe_get_by_id(db_session, Productos, uuid4(), tenant_id)

    assert exc_info.value.status_code == 404


def test_safe_get_raises_404_for_wrong_tenant(db_session: Session, tenant_admin_token):
    """safe_get_by_id raises HTTP 404 when record exists but belongs to a different tenant."""
    correct_tenant_id = tenant_admin_token["tenant"].id
    wrong_tenant_id = uuid4()

    producto = _make_producto(db_session, correct_tenant_id)

    with pytest.raises(HTTPException) as exc_info:
        safe_get_by_id(db_session, Productos, producto.id, wrong_tenant_id)

    assert exc_info.value.status_code == 404


def test_safe_get_excludes_soft_deleted(db_session: Session, tenant_admin_token):
    """safe_get_by_id raises HTTP 404 when record is soft-deleted (deleted_at is set)."""
    tenant_id = tenant_admin_token["tenant"].id
    producto = _make_producto(db_session, tenant_id, deleted_at=datetime.utcnow())

    with pytest.raises(HTTPException) as exc_info:
        safe_get_by_id(db_session, Productos, producto.id, tenant_id)

    assert exc_info.value.status_code == 404
