"""
Servicio de Calificaciones: rating 1-5 estrellas por tenant.
"""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..datos.esquemas import CalificacionCreate
from ..datos.modelos_calificaciones import Calificaciones
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ServicioCalificaciones:
    def __init__(self, db: Session):
        self.db = db

    def crear_o_actualizar(
        self,
        tenant_id: UUID,
        usuario_id: Optional[UUID],
        datos: CalificacionCreate,
        nombre_empresa: Optional[str] = None,
    ) -> Calificaciones:
        """
        Crea la calificación del tenant o la actualiza si ya existe.
        Solo una calificación activa por tenant.
        Al actualizar, resetea el estado a 'pendiente'.
        """
        existente = (
            self.db.query(Calificaciones)
            .filter(
                Calificaciones.tenant_id == tenant_id,
                Calificaciones.deleted_at.is_(None),
            )
            .first()
        )

        if existente:
            existente.estrellas = datos.estrellas
            existente.titulo = datos.titulo
            existente.comentario = datos.comentario
            existente.estado = "pendiente"  # re-moderación al editar
            if nombre_empresa:
                existente.nombre_empresa = nombre_empresa
            self.db.commit()
            self.db.refresh(existente)
            logger.info(f"Calificación actualizada para tenant {tenant_id}")
            return existente

        nueva = Calificaciones(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            estrellas=datos.estrellas,
            titulo=datos.titulo,
            comentario=datos.comentario,
            nombre_empresa=nombre_empresa,
            estado="pendiente",
        )
        self.db.add(nueva)
        self.db.commit()
        self.db.refresh(nueva)
        logger.info(f"Calificación creada para tenant {tenant_id}: {nueva.id}")
        return nueva

    def obtener_calificacion_tenant(self, tenant_id: UUID) -> Optional[Calificaciones]:
        """Retorna la calificación activa del tenant o None."""
        return (
            self.db.query(Calificaciones)
            .filter(
                Calificaciones.tenant_id == tenant_id,
                Calificaciones.deleted_at.is_(None),
            )
            .first()
        )

    def listar_publicas(self, limit: int = 20) -> list[Calificaciones]:
        """Retorna calificaciones aprobadas ordenadas por estrellas DESC."""
        return (
            self.db.query(Calificaciones)
            .filter(
                Calificaciones.estado == "aprobada",
                Calificaciones.deleted_at.is_(None),
            )
            .order_by(Calificaciones.estrellas.desc(), Calificaciones.created_at.desc())
            .limit(limit)
            .all()
        )

    def listar_admin(self, estado: Optional[str] = None) -> list[Calificaciones]:
        """Superadmin: lista todas las calificaciones."""
        query = self.db.query(Calificaciones).filter(Calificaciones.deleted_at.is_(None))
        if estado:
            query = query.filter(Calificaciones.estado == estado)
        return query.order_by(Calificaciones.created_at.desc()).all()

    def moderar(self, calificacion_id: UUID, nuevo_estado: str) -> Calificaciones:
        """Superadmin: aprueba o rechaza una calificación."""
        cal = (
            self.db.query(Calificaciones)
            .filter(
                Calificaciones.id == calificacion_id,
                Calificaciones.deleted_at.is_(None),
            )
            .first()
        )
        if not cal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Calificación no encontrada",
            )
        cal.estado = nuevo_estado
        self.db.commit()
        self.db.refresh(cal)
        logger.info(f"Calificación {calificacion_id} moderada: {nuevo_estado}")
        return cal
