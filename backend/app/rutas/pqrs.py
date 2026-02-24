"""
Rutas PQRS: Gestion de tickets de soporte (Peticiones, Quejas, Reclamos, Sugerencias).
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..datos.db import get_db
from ..datos.esquemas import (
    RespuestaTicket,
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
