import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from svix.webhooks import Webhook, WebhookVerificationError

from ..config import settings
from ..datos.db import get_db
from ..datos.esquemas import (
    ChangePasswordRequest,
    LoginRequest,
    TenantBriefResponse,
    TenantSelectionRequest,
    Token,
    TokenWithTenant,
    TokenWithTenants,
    UsuarioResponse,
)
from ..datos.modelos import Usuarios
from ..servicios.servicio_audit import ServicioAuditLog
from ..servicios.servicio_tenants import ServicioTenants
from ..utils.logger import set_request_context, setup_logger
from ..utils.rate_limiter import limiter
from ..utils.seguridad import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
    hash_password,
    require_not_impersonating,
    verify_clerk_token,
    verify_password,
)

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/login", response_model=TokenWithTenants)
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica usuario y devuelve tokens JWT junto con los tenants disponibles.

    **Flujo Multi-Tenant:**
    1. Login con email/password -> Retorna token + lista de tenants
    2. Si solo tiene 1 tenant, puede usarlo directamente
    3. Si tiene múltiples, debe llamar a /select-tenant para obtener token con tenant

    **Seguridad:**
    - Rate limited: 5 intentos por minuto por IP
    - Logs sin exponer información sensible
    - Refresh token con rotación
    """
    audit = ServicioAuditLog(db)

    # Intentar autenticar
    user = authenticate_user(credentials.email, credentials.password, db)

    if not user:
        logger.warning(
            "Intento de login fallido",
            extra={
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )
        # Audit: login fallido
        audit.registrar_login(request, credentials.email, exitoso=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar que el usuario esté activo
    if not user.estado:
        logger.warning(f"Intento de login con usuario inactivo: {user.email}")
        audit.registrar_login(request, user.email, exitoso=False, user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo. Contacte al administrador."
        )

    # Actualizar ultimo_acceso
    user.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()

    # Obtener tenants del usuario
    servicio_tenants = ServicioTenants(db)
    usuarios_tenants = servicio_tenants.obtener_tenants_usuario(user.id)

    tenants_response: List[TenantBriefResponse] = []
    for ut in usuarios_tenants:
        tenant = servicio_tenants.obtener_tenant_por_id(ut.tenant_id)
        if tenant and tenant.esta_activo:
            tenants_response.append(TenantBriefResponse.model_validate(tenant))

    # Generar tokens (sin tenant_id aún)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "rol": user.rol}, expires_delta=access_token_expires
    )

    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}, expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    # Establecer contexto de usuario para logs subsecuentes
    set_request_context(user_id=str(user.id))

    logger.info(
        f"Login exitoso: {user.email}",
        extra={
            "user_id": str(user.id),
            "rol": user.rol,
            "tenants_count": len(tenants_response),
            "ip": request.client.host if request.client else "unknown",
        },
    )

    # Audit: login exitoso
    audit.registrar_login(request, user.email, exitoso=True, user_id=user.id)

    return TokenWithTenants(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",  # nosec B106
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UsuarioResponse.model_validate(user),
        tenants=tenants_response,
    )


@router.post("/select-tenant", response_model=TokenWithTenant)
async def select_tenant(
    request: Request,
    selection: TenantSelectionRequest,
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Selecciona un tenant y genera un nuevo token con contexto de tenant.

    **Requiere:** Token de acceso válido (del login inicial)
    """
    servicio = ServicioTenants(db)

    # Validar acceso al tenant
    usuario_tenant = servicio.validar_acceso_tenant(current_user.id, selection.tenant_id)
    if not usuario_tenant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este tenant")

    # Obtener información del tenant
    tenant = servicio.obtener_tenant_por_id(selection.tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    # Verificar que el tenant esté activo
    if not tenant.esta_activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El tenant está suspendido o inactivo")

    # Generar nuevos tokens CON tenant_id
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user.id), "email": current_user.email, "rol": current_user.rol},
        expires_delta=access_token_expires,
        tenant_id=selection.tenant_id,
        rol_en_tenant=usuario_tenant.rol,
    )

    refresh_token = create_refresh_token(
        data={"sub": str(current_user.id)}, expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    logger.info(
        f"Tenant seleccionado: {tenant.slug} por {current_user.email}",
        extra={
            "user_id": str(current_user.id),
            "tenant_id": str(tenant.id),
            "rol_en_tenant": usuario_tenant.rol,
            "ip": request.client.host if request.client else "unknown",
        },
    )

    return TokenWithTenant(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",  # nosec B106
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UsuarioResponse.model_validate(current_user),
        tenant=TenantBriefResponse.model_validate(tenant),
        rol_en_tenant=usuario_tenant.rol,
    )


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
async def refresh_access_token(
    request: Request,
    refresh_token: str = Body(..., embed=True),
    tenant_id: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
):
    """
    Renueva el access token usando un refresh token válido.
    Si se proporciona tenant_id, el nuevo token preserva el contexto de tenant.
    """
    try:
        # Decodificar y validar refresh token
        payload = decode_refresh_token(refresh_token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

        # Validar usuario en DB
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token malformado")

        user = db.query(Usuarios).filter(Usuarios.id == user_uuid).first()

        if not user:
            logger.warning(f"Refresh token para usuario inexistente: {user_id}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")

        if not user.estado:
            logger.warning(f"Refresh token para usuario inactivo: {user.email}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

        # Validar tenant_id si se proporcionó (preservar contexto de tenant)
        resolved_tenant_id = None
        resolved_rol_tenant = None
        if tenant_id:
            try:
                tenant_uuid = UUID(tenant_id)
            except ValueError:
                tenant_uuid = None

            if tenant_uuid:
                servicio = ServicioTenants(db)
                usuario_tenant = servicio.validar_acceso_tenant(user.id, tenant_uuid)
                if usuario_tenant:
                    resolved_tenant_id = tenant_uuid
                    resolved_rol_tenant = usuario_tenant.rol

        # Generar NUEVOS tokens (rotación) con tenant_id preservado
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "rol": user.rol},
            expires_delta=access_token_expires,
            tenant_id=resolved_tenant_id,
            rol_en_tenant=resolved_rol_tenant,
        )

        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id)}, expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        logger.info(f"Token renovado para: {user.email}" + (f" (tenant: {tenant_id})" if tenant_id else ""))

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",  # nosec B106
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UsuarioResponse.model_validate(user),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error renovando token", exc_info=e, extra={"ip": request.client.host if request.client else "unknown"}
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido o expirado")


@router.get("/me", response_model=UsuarioResponse)
async def get_me(current_user: Usuarios = Depends(get_current_user)):
    """
    Obtiene información del usuario autenticado.

    **Requiere:** Header `Authorization: Bearer {access_token}`
    """
    return UsuarioResponse.model_validate(current_user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("3/minute")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    _: None = Depends(require_not_impersonating),
    current_user: Usuarios = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cambia la contraseña del usuario autenticado.

    **Seguridad:**
    - Rate limited: 3 intentos por minuto por IP
    """
    audit = ServicioAuditLog(db)

    # Validar contraseña actual
    if not verify_password(password_data.current_password, current_user.password_hash):
        logger.warning(
            f"Intento fallido de cambio de contraseña: {current_user.email}", extra={"user_id": str(current_user.id)}
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña actual incorrecta")

    # Actualizar contraseña
    current_user.password_hash = hash_password(password_data.new_password)
    db.commit()

    logger.info(
        f"Contraseña cambiada: {current_user.email}",
        extra={"user_id": str(current_user.id), "ip": request.client.host if request.client else "unknown"},
    )

    # Audit: cambio de contraseña
    audit.registrar_desde_request(
        request=request,
        user=current_user,
        action="auth.password_change",
        resource_type="auth",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, current_user: Usuarios = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Cierra sesión del usuario.

    **Nota:** Con JWT stateless, el logout es del lado del cliente.
    El cliente debe eliminar los tokens de su almacenamiento.
    """
    logger.info(f"Logout: {current_user.email}", extra={"user_id": str(current_user.id)})

    # Audit: logout
    audit = ServicioAuditLog(db)
    audit.registrar_desde_request(
        request=request,
        user=current_user,
        action="auth.logout",
        resource_type="auth",
    )


@router.post("/clerk-exchange", response_model=TokenWithTenants)
@limiter.limit("10/minute")
async def clerk_exchange(request: Request, db: Session = Depends(get_db)):
    """
    Intercambia un JWT de Clerk por un JWT custom del sistema.

    El cliente envía el token de Clerk en el header Authorization: Bearer <clerk_token>.
    Si el usuario no existe en la DB, se crea automáticamente (lazy sync).

    Retorna TokenWithTenants idéntico al /auth/login para que el frontend lo use igual.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de Clerk requerido en Authorization header"
        )

    clerk_token = auth_header.split(" ", 1)[1]

    # Verificar JWT de Clerk (llama a JWKS público)
    clerk_payload = verify_clerk_token(clerk_token)

    # Los JWTs de sesión de Clerk no incluyen email en el payload.
    # Necesitamos obtenerlo desde el Backend API usando el sub (user_id).
    clerk_user_id = clerk_payload.get("sub")
    if not clerk_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token de Clerk no contiene user ID (sub)")

    # Obtener email via Clerk Backend API
    email = None
    try:
        resp = httpx.get(
            f"https://api.clerk.com/v1/users/{clerk_user_id}",
            headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"},
            timeout=10,
        )
        resp.raise_for_status()
        user_data = resp.json()
        email_addresses = user_data.get("email_addresses", [])
        primary_id = user_data.get("primary_email_address_id")
        for ea in email_addresses:
            if ea.get("id") == primary_id:
                email = ea.get("email_address")
                break
        if not email and email_addresses:
            email = email_addresses[0].get("email_address")
    except Exception as exc:
        logger.error(f"Error al consultar Clerk Backend API: {exc}")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo obtener el email del token de Clerk"
        )

    # Buscar o crear usuario
    es_superadmin_email = settings.SUPERADMIN_EMAIL and email.lower() == settings.SUPERADMIN_EMAIL.lower()
    user = db.query(Usuarios).filter(Usuarios.email == email).first()
    is_new_user = False
    if not user:
        # Lazy sync: crear usuario sin tenant, con password aleatorio
        nombre = clerk_payload.get("first_name", "") or ""
        apellido = clerk_payload.get("last_name", "") or ""
        nombre_completo = f"{nombre} {apellido}".strip() or email.split("@")[0]

        user = Usuarios(
            nombre=nombre_completo,
            email=email,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            rol="admin",
            estado=True,
            es_superadmin=bool(es_superadmin_email),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        is_new_user = True
        logger.info(f"Usuario creado via Clerk sync: {email}")
    elif es_superadmin_email and not user.es_superadmin:
        # El usuario ya existe pero no tiene es_superadmin — corregir
        user.es_superadmin = True
        db.commit()
        logger.info(f"es_superadmin=True asignado a {email} via SUPERADMIN_EMAIL")

    if not user.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo. Contacte al administrador."
        )

    user.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()

    servicio_tenants = ServicioTenants(db)
    usuarios_tenants = servicio_tenants.obtener_tenants_usuario(user.id)

    tenants_response: List[TenantBriefResponse] = []
    for ut in usuarios_tenants:
        tenant = servicio_tenants.obtener_tenant_por_id(ut.tenant_id)
        if tenant and tenant.esta_activo:
            tenants_response.append(TenantBriefResponse.model_validate(tenant))

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "rol": user.rol},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    set_request_context(user_id=str(user.id))
    logger.info(f"Clerk exchange exitoso: {email}")

    return TokenWithTenants(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",  # nosec B106
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UsuarioResponse.model_validate(user),
        tenants=tenants_response,
        is_new_user=is_new_user,
    )


@router.post("/clerk-webhook", status_code=status.HTTP_200_OK)
async def clerk_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Recibe eventos de Clerk para sincronización proactiva de usuarios.
    Verifica la firma usando svix y CLERK_WEBHOOK_SECRET.

    Eventos manejados: user.created, user.updated, user.deleted
    """
    webhook_secret = settings.CLERK_WEBHOOK_SECRET
    if not webhook_secret:
        logger.warning("CLERK_WEBHOOK_SECRET no configurado — webhook ignorado")
        return {"status": "skipped"}

    # Verificar firma svix
    headers = dict(request.headers)
    body = await request.body()

    try:
        wh = Webhook(webhook_secret)
        payload = wh.verify(body, headers)
    except WebhookVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Firma de webhook inválida")

    event_type = payload.get("type")
    data = payload.get("data", {})

    # Extraer email del payload de Clerk
    email_addresses = data.get("email_addresses", [])
    email = email_addresses[0].get("email_address") if email_addresses else None

    if not email:
        logger.warning(f"Webhook Clerk sin email — evento: {event_type}")
        return {"status": "ok"}

    es_superadmin_email = settings.SUPERADMIN_EMAIL and email.lower() == settings.SUPERADMIN_EMAIL.lower()

    if event_type == "user.created":
        existing = db.query(Usuarios).filter(Usuarios.email == email).first()
        if not existing:
            nombre = data.get("first_name", "") or ""
            apellido = data.get("last_name", "") or ""
            nombre_completo = f"{nombre} {apellido}".strip() or email.split("@")[0]
            user = Usuarios(
                nombre=nombre_completo,
                email=email,
                password_hash=hash_password(secrets.token_urlsafe(32)),
                rol="admin",
                estado=True,
                es_superadmin=bool(es_superadmin_email),
            )
            db.add(user)
            db.commit()
            logger.info(f"Usuario creado via webhook Clerk: {email}")
        elif es_superadmin_email and not existing.es_superadmin:
            existing.es_superadmin = True
            db.commit()
            logger.info(f"es_superadmin=True asignado a {email} via webhook Clerk")

    elif event_type == "user.updated":
        user = db.query(Usuarios).filter(Usuarios.email == email).first()
        if user:
            nombre = data.get("first_name", "") or ""
            apellido = data.get("last_name", "") or ""
            nombre_completo = f"{nombre} {apellido}".strip() or user.nombre
            user.nombre = nombre_completo
            db.commit()
            logger.info(f"Usuario actualizado via webhook Clerk: {email}")

    elif event_type == "user.deleted":
        user = db.query(Usuarios).filter(Usuarios.email == email).first()
        if user:
            user.estado = False
            db.commit()
            logger.info(f"Usuario desactivado via webhook Clerk: {email}")

    return {"status": "ok"}
