"""
Servicio de Audit Logging.
Registra acciones críticas del sistema de forma inmutable.
Usa su propia sesión para no fallar si la transacción principal falla.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import Request
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..datos.db import SessionLocal
from ..datos.modelos import Usuarios
from ..datos.modelos_tenant import AuditLog
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ServicioAuditLog:
    """Servicio para registrar y consultar audit logs."""

    def __init__(self, db: Session):
        self.db = db

    def registrar(
        self,
        actor_id: Optional[UUID],
        actor_email: str,
        action: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        changes: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Registra una acción en el audit log.
        Usa sesión independiente para garantizar persistencia
        incluso si la transacción principal falla.
        """
        audit_db = SessionLocal()
        try:
            log_entry = AuditLog(
                actor_id=actor_id,
                actor_email=actor_email,
                tenant_id=tenant_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                changes=changes,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            audit_db.add(log_entry)
            audit_db.commit()
            audit_db.refresh(log_entry)

            logger.info(
                f"Audit: {action} by {actor_email} on {resource_type}"
                + (f"/{resource_id}" if resource_id else ""),
                extra={
                    "audit_action": action,
                    "actor_email": actor_email,
                    "resource_type": resource_type,
                    "resource_id": str(resource_id) if resource_id else None,
                    "tenant_id": str(tenant_id) if tenant_id else None,
                }
            )
            return log_entry
        except Exception as e:
            audit_db.rollback()
            logger.error(f"Error registrando audit log: {e}", exc_info=True)
            # No re-lanzar: el audit log no debe bloquear la operación principal
        finally:
            audit_db.close()

    def registrar_desde_request(
        self,
        request: Request,
        user: Usuarios,
        action: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        changes: Optional[dict] = None,
    ) -> Optional[AuditLog]:
        """
        Helper que extrae ip y user_agent del Request automáticamente.
        """
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:500]

        return self.registrar(
            actor_id=user.id,
            actor_email=user.email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=tenant_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def registrar_login(
        self,
        request: Request,
        email: str,
        exitoso: bool,
        user_id: Optional[UUID] = None,
    ) -> Optional[AuditLog]:
        """Helper específico para eventos de login."""
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:500]

        return self.registrar(
            actor_id=user_id,
            actor_email=email,
            action="auth.login" if exitoso else "auth.login_failed",
            resource_type="auth",
            ip_address=ip_address,
            user_agent=user_agent,
            changes={"exitoso": exitoso},
        )

    def listar(
        self,
        tenant_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[List[AuditLog], int]:
        """
        Lista audit logs con filtros opcionales.
        Retorna (items, total_count).
        """
        query = self.db.query(AuditLog)

        if tenant_id is not None:
            query = query.filter(AuditLog.tenant_id == tenant_id)
        if actor_id is not None:
            query = query.filter(AuditLog.actor_id == actor_id)
        if action is not None:
            query = query.filter(AuditLog.action == action)
        if resource_type is not None:
            query = query.filter(AuditLog.resource_type == resource_type)
        if fecha_desde is not None:
            query = query.filter(AuditLog.created_at >= fecha_desde)
        if fecha_hasta is not None:
            query = query.filter(AuditLog.created_at <= fecha_hasta)

        total = query.count()

        items = (
            query
            .order_by(desc(AuditLog.created_at))
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        return items, total
