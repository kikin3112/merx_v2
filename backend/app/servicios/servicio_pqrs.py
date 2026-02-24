from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..datos.esquemas import RespuestaTicket, TicketPQRSCreate, TicketPQRSUpdate
from ..datos.modelos_pqrs import EstadoTicket, PrioridadTicket, TicketsPQRS, TipoPQRS
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ServicioPQRS:
    def __init__(self, db: Session):
        self.db = db

    def crear_ticket(self, datos: TicketPQRSCreate, usuario_id: UUID, tenant_id: UUID) -> TicketsPQRS:
        """Crea un nuevo ticket PQRS."""
        ticket = TicketsPQRS(
            tipo=TipoPQRS(datos.tipo),
            asunto=datos.asunto,
            descripcion=datos.descripcion,
            estado=EstadoTicket.ABIERTO,
            prioridad=PrioridadTicket(datos.prioridad),
            usuario_id=usuario_id,
            tenant_id=tenant_id,
            respuestas=[],
        )
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        logger.info(f"Ticket PQRS creado: {ticket.id} por usuario {usuario_id}")
        return ticket

    def listar_tickets(
        self,
        tenant_id: UUID,
        usuario_id: Optional[UUID] = None,
        es_admin: bool = False,
        tipo: Optional[str] = None,
        estado: Optional[str] = None,
        prioridad: Optional[str] = None,
    ) -> list[TicketsPQRS]:
        """Lista tickets. Admin ve todos del tenant, usuario normal solo los suyos."""
        query = self.db.query(TicketsPQRS).filter(
            TicketsPQRS.tenant_id == tenant_id,
            TicketsPQRS.deleted_at.is_(None),
        )

        if not es_admin and usuario_id:
            query = query.filter(TicketsPQRS.usuario_id == usuario_id)

        if tipo:
            query = query.filter(TicketsPQRS.tipo == TipoPQRS(tipo))
        if estado:
            query = query.filter(TicketsPQRS.estado == EstadoTicket(estado))
        if prioridad:
            query = query.filter(TicketsPQRS.prioridad == PrioridadTicket(prioridad))

        return query.order_by(TicketsPQRS.created_at.desc()).all()

    def obtener_ticket(
        self,
        ticket_id: UUID,
        tenant_id: UUID,
        usuario_id: Optional[UUID] = None,
        es_admin: bool = False,
    ) -> TicketsPQRS:
        """Obtiene un ticket por ID. Valida acceso."""
        ticket = (
            self.db.query(TicketsPQRS)
            .filter(
                TicketsPQRS.id == ticket_id,
                TicketsPQRS.tenant_id == tenant_id,
                TicketsPQRS.deleted_at.is_(None),
            )
            .first()
        )

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket no encontrado",
            )

        if not es_admin and usuario_id and ticket.usuario_id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene acceso a este ticket",
            )

        return ticket

    def actualizar_ticket(self, ticket_id: UUID, datos: TicketPQRSUpdate, tenant_id: UUID) -> TicketsPQRS:
        """Actualiza estado/prioridad de un ticket (admin only)."""
        ticket = self.obtener_ticket(ticket_id, tenant_id, es_admin=True)

        if datos.estado:
            ticket.estado = EstadoTicket(datos.estado)
        if datos.prioridad:
            ticket.prioridad = PrioridadTicket(datos.prioridad)

        self.db.commit()
        self.db.refresh(ticket)
        logger.info(f"Ticket {ticket_id} actualizado: estado={ticket.estado}, prioridad={ticket.prioridad}")
        return ticket

    def agregar_respuesta(
        self,
        ticket_id: UUID,
        datos: RespuestaTicket,
        tenant_id: UUID,
        usuario_id: UUID,
        usuario_nombre: str,
        es_admin: bool = False,
    ) -> TicketsPQRS:
        """Agrega una respuesta al ticket."""
        ticket = self.obtener_ticket(ticket_id, tenant_id, usuario_id=usuario_id, es_admin=es_admin)

        from datetime import datetime, timezone

        nueva_respuesta = {
            "autor_id": str(usuario_id),
            "autor_nombre": usuario_nombre,
            "contenido": datos.contenido,
            "fecha": datetime.now(timezone.utc).isoformat(),
        }

        respuestas_actuales = list(ticket.respuestas or [])
        respuestas_actuales.append(nueva_respuesta)
        ticket.respuestas = respuestas_actuales

        # Force SQLAlchemy to detect the JSONB change
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(ticket, "respuestas")

        self.db.commit()
        self.db.refresh(ticket)
        logger.info(f"Respuesta agregada al ticket {ticket_id} por {usuario_nombre}")
        return ticket
