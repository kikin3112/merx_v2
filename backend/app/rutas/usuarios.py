from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..datos.db import get_db
from ..datos.esquemas import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from ..datos.modelos import Usuarios
from ..utils.logger import setup_logger
from ..utils.seguridad import get_current_user, hash_password

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    usuario_data: UsuarioCreate, db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)
):
    """
    Crea un nuevo usuario del sistema.

    **Validaciones:**
    - Email único
    - Contraseña cumple requisitos (validado en schema)
    - Rol válido: admin, operador, contador

    **Permisos:** Solo admin puede crear usuarios
    """
    # Solo admin puede crear usuarios
    if current_user.rol != "admin" and not current_user.es_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores pueden crear usuarios")

    # El rol superadmin NO se puede asignar via API
    if usuario_data.rol == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El rol superadmin es exclusivo del sistema y no puede asignarse via API",
        )

    # Validar email único
    existing = db.query(Usuarios).filter(Usuarios.email == usuario_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ya existe un usuario con el email '{usuario_data.email}'"
        )

    try:
        # Hashear contraseña
        password_hash = hash_password(usuario_data.password)

        # Crear usuario (sin incluir password en model_dump)
        user_dict = usuario_data.model_dump(exclude={"password"})
        nuevo_usuario = Usuarios(**user_dict, password_hash=password_hash)

        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)

        logger.info(
            f"Usuario creado: {nuevo_usuario.email}",
            extra={"usuario_id": str(nuevo_usuario.id), "rol": nuevo_usuario.rol, "created_by": str(current_user.id)},
        )

        return UsuarioResponse.model_validate(nuevo_usuario)

    except Exception as e:
        db.rollback()
        logger.error("Error creando usuario", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al crear el usuario"
        )


@router.get("/", response_model=List[UsuarioResponse])
async def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    rol: Optional[str] = Query(None, description="admin, operador, contador"),
    estado: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
):
    """
    Lista usuarios del sistema.

    **Filtros:**
    - `rol`: Filtrar por rol
    - `estado`: true (activos) / false (inactivos)

    **Permisos:** Solo admin puede ver lista completa
    """
    # Solo admin puede ver todos los usuarios
    if current_user.rol != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores pueden listar usuarios")

    query = db.query(Usuarios)

    # Aplicar filtros
    if rol:
        query = query.filter(Usuarios.rol == rol)

    if estado is not None:
        query = query.filter(Usuarios.estado == estado)

    # Ordenar y paginar
    usuarios = query.order_by(Usuarios.nombre).offset(skip).limit(limit).all()

    return [UsuarioResponse.model_validate(u) for u in usuarios]


@router.get("/me", response_model=UsuarioResponse)
async def obtener_perfil(current_user: Usuarios = Depends(get_current_user)):
    """
    Obtiene el perfil del usuario autenticado.

    **Nota:** Diferente de `/auth/me`, este está en el contexto de usuarios.
    """
    return UsuarioResponse.model_validate(current_user)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obtener_usuario(
    usuario_id: UUID, db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)
):
    """
    Obtiene un usuario por ID.

    **Permisos:**
    - Admin: puede ver cualquier usuario
    - Otros: solo pueden ver su propio perfil
    """
    # Validar permisos
    if current_user.rol != "admin" and current_user.id != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para ver este usuario")

    usuario = db.query(Usuarios).filter(Usuarios.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Usuario con ID {usuario_id} no encontrado")

    return UsuarioResponse.model_validate(usuario)


@router.patch("/{usuario_id}", response_model=UsuarioResponse)
async def actualizar_usuario(
    usuario_id: UUID,
    usuario_data: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
):
    """
    Actualiza un usuario existente.

    **Permisos:**
    - Admin: puede actualizar cualquier usuario (incluyendo rol)
    - Usuario: solo puede actualizar su propio nombre y email (no rol)
    """
    # Buscar usuario
    usuario = db.query(Usuarios).filter(Usuarios.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Usuario con ID {usuario_id} no encontrado")

    # Validar permisos
    is_self_update = current_user.id == usuario_id
    is_admin = current_user.rol == "admin"

    if not is_admin and not is_self_update:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para actualizar este usuario"
        )

    try:
        update_data = usuario_data.model_dump(exclude_unset=True)

        # Si no es admin, no puede cambiar rol ni estado
        if not is_admin and not current_user.es_superadmin:
            if "rol" in update_data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores pueden cambiar roles"
                )
            if "estado" in update_data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo administradores pueden activar/desactivar usuarios",
                )

        # No permitir asignar rol superadmin via API
        if "rol" in update_data and update_data["rol"] == "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El rol superadmin es exclusivo del sistema y no puede asignarse via API",
            )

        # No permitir modificar un superadmin (a menos que sea otro superadmin)
        if usuario.es_superadmin and not current_user.es_superadmin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para modificar un superadmin del sistema",
            )

        # Validar email único (si se está cambiando)
        if "email" in update_data:
            existing = (
                db.query(Usuarios).filter(Usuarios.email == update_data["email"], Usuarios.id != usuario_id).first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=f"Email '{update_data['email']}' ya está en uso"
                )

        # Si se está actualizando la contraseña, hashearla
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data["password"])
            del update_data["password"]

        # Aplicar cambios
        for field, value in update_data.items():
            setattr(usuario, field, value)

        db.commit()
        db.refresh(usuario)

        logger.info(
            f"Usuario actualizado: {usuario.email}",
            extra={"usuario_id": str(usuario.id), "updated_by": str(current_user.id)},
        )

        return UsuarioResponse.model_validate(usuario)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error actualizando usuario", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al actualizar el usuario"
        )


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(
    usuario_id: UUID, db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)
):
    """
    Desactiva un usuario (soft delete).

    **Nota:** No se elimina físicamente, solo se marca como inactivo.

    **Restricciones:**
    - No se puede auto-eliminar
    - Solo admin puede eliminar usuarios
    """
    # Solo admin o superadmin puede eliminar
    if current_user.rol != "admin" and not current_user.es_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores pueden eliminar usuarios"
        )

    # No permitir auto-eliminación
    if current_user.id == usuario_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puede desactivar su propia cuenta")

    usuario = db.query(Usuarios).filter(Usuarios.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Usuario con ID {usuario_id} no encontrado")

    # No permitir desactivar superadmins del sistema
    if usuario.es_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No se puede desactivar un superadmin del sistema"
        )

    try:
        # Soft delete
        usuario.estado = False
        db.commit()

        logger.warning(
            f"Usuario desactivado: {usuario.email}",
            extra={"usuario_id": str(usuario.id), "deleted_by": str(current_user.id)},
        )

    except Exception as e:
        db.rollback()
        logger.error("Error eliminando usuario", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al eliminar el usuario"
        )


@router.post("/{usuario_id}/reactivar", response_model=UsuarioResponse)
async def reactivar_usuario(
    usuario_id: UUID, db: Session = Depends(get_db), current_user: Usuarios = Depends(get_current_user)
):
    """
    Reactiva un usuario desactivado.

    **Permisos:** Solo admin
    """
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores pueden reactivar usuarios"
        )

    usuario = db.query(Usuarios).filter(Usuarios.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Usuario con ID {usuario_id} no encontrado")

    if usuario.estado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario ya está activo")

    try:
        usuario.estado = True
        db.commit()
        db.refresh(usuario)

        logger.info(
            f"Usuario reactivado: {usuario.email}",
            extra={"usuario_id": str(usuario.id), "reactivated_by": str(current_user.id)},
        )

        return UsuarioResponse.model_validate(usuario)

    except Exception as e:
        db.rollback()
        logger.error("Error reactivando usuario", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al reactivar el usuario"
        )
