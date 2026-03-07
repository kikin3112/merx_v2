"""
Database helper utilities for consistent, tenant-scoped record lookups.
"""

from typing import Type, TypeVar
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

T = TypeVar("T")


def safe_get_by_id(db: Session, model: Type[T], record_id: UUID, tenant_id: UUID) -> T:
    """
    Fetch a record by ID scoped to tenant_id.
    Excludes soft-deleted records (deleted_at IS NOT NULL) when the model has that column.
    Raises HTTP 404 if not found.

    Args:
        db: SQLAlchemy session
        model: SQLAlchemy model class
        record_id: UUID of the record to fetch
        tenant_id: UUID of the current tenant

    Returns:
        The model instance

    Raises:
        HTTPException(404): If record not found, wrong tenant, or soft-deleted
    """
    query = db.query(model).filter(
        model.id == record_id,
        model.tenant_id == tenant_id,
    )

    if hasattr(model, "deleted_at"):
        query = query.filter(model.deleted_at.is_(None))

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} no encontrado")
    return obj
