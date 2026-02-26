"""
Rutas PQRS: Gestion de tickets de soporte (Peticiones, Quejas, Reclamos, Sugerencias).
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..datos.db import get_db
from ..datos.esquemas import (
    RespuestaTicket,
    TicketPQRSAdminResponse,
    TicketPQRSCreate,
    TicketPQRSResponse,
    TicketPQRSUpdate,
)
from ..datos.modelos import Usuarios
from ..servicios.servicio_pqrs import ServicioPQRS
from ..utils.logger import setup_logger
from ..utils.seguridad import get_current_user, get_tenant_id_from_token

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/", response_model=TicketPQRSResponse, status_code=status.HTTP_201_CREATED)
async def crear_ticket(
    datos: TicketPQRSCreate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Crear un nuevo ticket PQRS. Cualquier usuario autenticado puede crear."""
    servicio = ServicioPQRS(db)
    ticket = servicio.crear_ticket(
        datos=datos,
        usuario_id=current_user.id,
        tenant_id=tenant_id,
    )
    return ticket


@router.get("/", response_model=list[TicketPQRSResponse])
async def listar_tickets(
    tipo: Optional[str] = None,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Listar tickets. Admin ve todos, usuario normal ve solo los suyos."""
    servicio = ServicioPQRS(db)
    es_admin = current_user.rol == "admin" or current_user.es_superadmin
    tickets = servicio.listar_tickets(
        tenant_id=tenant_id,
        usuario_id=current_user.id,
        es_admin=es_admin,
        tipo=tipo,
        estado=estado,
        prioridad=prioridad,
    )
    return tickets


@router.get("/{ticket_id}", response_model=TicketPQRSResponse)
async def obtener_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Obtener detalle de un ticket."""
    servicio = ServicioPQRS(db)
    es_admin = current_user.rol == "admin" or current_user.es_superadmin
    ticket = servicio.obtener_ticket(
        ticket_id=ticket_id,
        tenant_id=tenant_id,
        usuario_id=current_user.id,
        es_admin=es_admin,
    )
    return ticket


@router.patch("/{ticket_id}", response_model=TicketPQRSResponse)
async def actualizar_ticket(
    ticket_id: UUID,
    datos: TicketPQRSUpdate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Actualizar estado/prioridad de un ticket. Solo admin."""
    if current_user.rol != "admin" and not current_user.es_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden actualizar tickets",
        )
    servicio = ServicioPQRS(db)
    ticket = servicio.actualizar_ticket(
        ticket_id=ticket_id,
        datos=datos,
        tenant_id=tenant_id,
    )
    return ticket


@router.get("/admin/todos", response_model=list[TicketPQRSAdminResponse])
async def listar_todos_tickets_admin(
    tenant_id: Optional[UUID] = Query(None, description="Filtrar por tenant"),
    tipo: Optional[str] = None,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
):
    """Solo superadmin. Devuelve tickets de TODOS los tenants."""
    if not current_user.es_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo superadmin")
    servicio = ServicioPQRS(db)
    return servicio.listar_todos_tickets(
        tenant_id_filtro=tenant_id,
        tipo=tipo,
        estado=estado,
        prioridad=prioridad,
    )


@router.post("/admin/{ticket_id}/responder", response_model=TicketPQRSAdminResponse)
async def responder_ticket_admin(
    ticket_id: UUID,
    datos: RespuestaTicket,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
):
    """Solo superadmin. Responde a cualquier ticket sin requerir tenant_id."""
    if not current_user.es_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo superadmin")

    from datetime import datetime, timezone

    from sqlalchemy.orm.attributes import flag_modified

    from ..datos.modelos_pqrs import TicketsPQRS

    ticket = db.query(TicketsPQRS).filter(TicketsPQRS.id == ticket_id, TicketsPQRS.deleted_at.is_(None)).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")

    nueva_respuesta = {
        "autor_id": str(current_user.id),
        "autor_nombre": f"{current_user.nombre} (Soporte)",
        "contenido": datos.contenido,
        "fecha": datetime.now(timezone.utc).isoformat(),
    }
    respuestas_actuales = list(ticket.respuestas or [])
    respuestas_actuales.append(nueva_respuesta)
    ticket.respuestas = respuestas_actuales
    flag_modified(ticket, "respuestas")
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/respuestas", response_model=TicketPQRSResponse)
async def agregar_respuesta(
    ticket_id: UUID,
    datos: RespuestaTicket,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Agregar una respuesta a un ticket."""
    servicio = ServicioPQRS(db)
    es_admin = current_user.rol == "admin" or current_user.es_superadmin
    ticket = servicio.agregar_respuesta(
        ticket_id=ticket_id,
        datos=datos,
        tenant_id=tenant_id,
        usuario_id=current_user.id,
        usuario_nombre=current_user.nombre,
        es_admin=es_admin,
    )
    return ticket
