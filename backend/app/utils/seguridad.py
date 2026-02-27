"""
Utilidades de seguridad: JWT, hashing de passwords, autenticación.
Usa Argon2 para hashing (más seguro que bcrypt).
Soporte multi-tenant con tenant_id en JWT payload.
"""

import base64 as _base64
import json as _json_mod
from datetime import datetime, timedelta, timezone
from typing import Callable, NamedTuple, Optional
from uuid import UUID

import jwt as pyjwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jwt import PyJWKClient
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..config import settings
from ..datos.db import get_db
from ..datos.modelos import Usuarios
from ..utils.logger import set_request_context, setup_logger

logger = setup_logger(__name__)


# ============================================================================
# TIPOS DE DATOS PARA CONTEXTO DE USUARIO
# ============================================================================


class UserContext(NamedTuple):
    """Contexto del usuario autenticado con información del tenant."""

    user: Usuarios
    tenant_id: Optional[UUID]
    rol_en_tenant: Optional[str]


# ============================================================================
# CONFIGURACIÓN DE HASHING
# ============================================================================

# Argon2 es más moderno y seguro que bcrypt
# Resistente a ataques GPU y ASIC
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,  # 3 iteraciones
    argon2__parallelism=4,  # 4 hilos paralelos
)

# ============================================================================
# ESQUEMA DE SEGURIDAD BEARER
# ============================================================================

security = HTTPBearer(
    scheme_name="JWT",
    description="Token JWT en header Authorization: Bearer {token}",
    auto_error=True,  # Lanza error automáticamente si falta el token
)


# ============================================================================
# FUNCIONES DE HASHING
# ============================================================================


def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando Argon2.

    Args:
        password: Contraseña en texto plano

    Returns:
        Hash de la contraseña

    Ejemplo:
        >>> hashed = hash_password("MiPassword123!")
        >>> print(hashed)
        $argon2id$v=19$m=65536,t=3,p=4$...
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña contra su hash.

    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash almacenado en DB

    Returns:
        True si coinciden, False en caso contrario
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error verificando password: {str(e)}")
        return False


# ============================================================================
# FUNCIONES JWT - ACCESS TOKEN
# ============================================================================


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    tenant_id: Optional[UUID] = None,
    rol_en_tenant: Optional[str] = None,
) -> str:
    """
    Crea un access token JWT con soporte multi-tenant.

    Args:
        data: Datos a incluir (típicamente {"sub": user_id, "email": ..., "rol": ...})
        expires_delta: Tiempo de expiración personalizado (default: 30 min)
        tenant_id: UUID del tenant seleccionado (opcional)
        rol_en_tenant: Rol del usuario en el tenant específico (opcional)

    Returns:
        Token JWT codificado

    Ejemplo:
        >>> token = create_access_token(
        ...     data={"sub": str(user.id), "email": user.email, "rol": user.rol},
        ...     tenant_id=selected_tenant_id,
        ...     rol_en_tenant="admin"
        ... )
    """
    to_encode = data.copy()

    # Usar timezone aware datetime (Python 3.12+)
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update(
        {
            "exp": expire,
            "iat": now,  # Issued at
            "type": "access",
        }
    )

    # Agregar tenant_id si está presente
    if tenant_id:
        to_encode["tenant_id"] = str(tenant_id)

    # Agregar rol en el tenant si está presente
    if rol_en_tenant:
        to_encode["rol_tenant"] = rol_en_tenant

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decodifica y valida un access token JWT.

    Args:
        token: Token JWT a decodificar

    Returns:
        Payload del token

    Raises:
        HTTPException 401: Si el token es inválido, expirado o no es access token
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Validar que sea access token
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: tipo incorrecto",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    except JWTError as e:
        logger.warning(f"Token JWT inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# FUNCIONES JWT - REFRESH TOKEN
# ============================================================================


def create_refresh_token(data: dict, expires_delta: timedelta) -> str:
    """
    Crea un refresh token JWT (TTL largo: 7 días default).

    Args:
        data: Datos a incluir (solo {"sub": user_id})
        expires_delta: Tiempo de expiración

    Returns:
        Refresh token JWT codificado

    Ejemplo:
        >>> refresh_token = create_refresh_token(
        ...     data={"sub": str(user.id)},
        ...     expires_delta=timedelta(days=7)
        ... )
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    to_encode.update({"exp": expire, "iat": now, "type": "refresh"})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def decode_refresh_token(token: str) -> dict:
    """
    Decodifica y valida un refresh token.

    Args:
        token: Refresh token JWT

    Returns:
        Payload del token

    Raises:
        HTTPException 401: Si el token es inválido o no es tipo refresh
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Validar que sea refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: no es un refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    except JWTError as e:
        logger.warning(f"Refresh token inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# DEPENDENCIAS DE AUTENTICACIÓN
# ============================================================================


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)
) -> Usuarios:
    """
    Dependencia de FastAPI para obtener el usuario autenticado.
    NO valida contexto de tenant (usar get_current_user_with_tenant para eso).

    Uso:
        @router.get("/protected")
        async def protected_route(
            current_user: Usuarios = Depends(get_current_user)
        ):
            return {"user": current_user.email}

    Args:
        credentials: Credenciales Bearer del header Authorization
        db: Sesión de base de datos

    Returns:
        Usuario autenticado

    Raises:
        HTTPException 401: Si el token es inválido
        HTTPException 403: Si el usuario está inactivo
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    # Extraer user_id del token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: falta subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validar formato UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: ID de usuario malformado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Buscar usuario en DB
    user = db.query(Usuarios).filter(Usuarios.id == user_uuid).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validar que esté activo
    if not user.estado:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    # Establecer contexto de usuario para logging
    set_request_context(user_id=str(user.id))

    return user


def get_current_user_with_tenant(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)
) -> UserContext:
    """
    Dependencia de FastAPI para obtener usuario con contexto de tenant.
    Valida que el tenant_id del header coincida con el del token.

    Uso:
        @router.get("/tenant-protected")
        async def tenant_route(
            ctx: UserContext = Depends(get_current_user_with_tenant)
        ):
            return {"user": ctx.user.email, "tenant": ctx.tenant_id}

    Returns:
        UserContext con usuario, tenant_id y rol en tenant

    Raises:
        HTTPException 401: Si el token es inválido
        HTTPException 403: Si el usuario no tiene acceso al tenant
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    # Extraer user_id del token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: falta subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validar formato UUID del usuario
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: ID de usuario malformado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Buscar usuario en DB
    user = db.query(Usuarios).filter(Usuarios.id == user_uuid).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validar que esté activo
    if not user.estado:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    # Extraer tenant_id del token
    token_tenant_id_str = payload.get("tenant_id")
    rol_en_tenant = payload.get("rol_tenant")

    # Obtener tenant_id del header (establecido por middleware)
    header_tenant_id = getattr(request.state, "tenant_id", None)

    tenant_id = None

    if token_tenant_id_str:
        try:
            tenant_id = UUID(token_tenant_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: tenant_id malformado",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Si hay tenant_id en header, validar que coincida con el del token
        if header_tenant_id and header_tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="El tenant_id del header no coincide con el del token"
            )

    # Establecer contexto de usuario para logging
    set_request_context(user_id=str(user.id))

    return UserContext(user=user, tenant_id=tenant_id, rol_en_tenant=rol_en_tenant)


def get_current_active_admin(current_user: Usuarios = Depends(get_current_user)) -> Usuarios:
    """
    Dependencia para rutas que requieren rol admin o superadmin.

    Uso:
        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: UUID,
            admin: Usuarios = Depends(get_current_active_admin)
        ):
            # Solo admins pueden ejecutar esto

    Raises:
        HTTPException 403: Si el usuario no es admin
    """
    if current_user.rol != "admin" and not current_user.es_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes. Se requiere rol admin"
        )
    return current_user


def require_roles(*allowed_roles: str) -> Callable:
    """
    Factory de dependencias para validación de múltiples roles.

    Uso:
        @router.post("/productos")
        async def crear_producto(
            producto: ProductoCreate,
            user: Usuarios = Depends(require_roles('admin', 'operador'))
        ):
            # Solo admin y operador pueden crear productos

    Args:
        *allowed_roles: Roles permitidos (ej: 'admin', 'operador', 'contador')

    Returns:
        Función de dependencia que valida el rol del usuario

    Raises:
        HTTPException 403: Si el usuario no tiene uno de los roles permitidos
    """

    def role_checker(current_user: Usuarios = Depends(get_current_user)) -> Usuarios:
        if current_user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes. Se requiere uno de los roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


def require_tenant_roles(*allowed_roles: str) -> Callable:
    """
    Factory de dependencias para validación de roles en contexto de tenant.

    Uso:
        @router.post("/productos")
        async def crear_producto(
            producto: ProductoCreate,
            ctx: UserContext = Depends(require_tenant_roles('admin', 'operador'))
        ):
            # Solo admin y operador del tenant pueden crear productos
            # ctx.tenant_id contiene el UUID del tenant

    Args:
        *allowed_roles: Roles permitidos en el tenant (ej: 'admin', 'operador', 'vendedor')

    Returns:
        Función de dependencia que valida el rol del usuario en el tenant

    Raises:
        HTTPException 403: Si el usuario no tiene uno de los roles permitidos en el tenant
    """

    def tenant_role_checker(
        request: Request, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)
    ) -> UserContext:
        ctx = get_current_user_with_tenant(request, credentials, db)

        # Superadmin global tiene acceso a todo
        if ctx.user.es_superadmin:
            return ctx

        # Validar rol en tenant
        if ctx.rol_en_tenant not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes en este tenant. Se requiere uno de los roles: {', '.join(allowed_roles)}",
            )

        return ctx

    return tenant_role_checker


def get_superadmin(
    credentials: HTTPAuthorizationCredentials = Depends(security), current_user: Usuarios = Depends(get_current_user)
) -> Usuarios:
    """
    Dependencia para rutas que requieren ser superadmin del sistema.
    Bloquea automáticamente tokens de impersonación.

    Uso:
        @router.get("/superadmin/tenants")
        async def list_all_tenants(
            superadmin: Usuarios = Depends(get_superadmin)
        ):
            # Solo superadmins pueden ver todos los tenants

    Raises:
        HTTPException 403: Si el usuario no es superadmin o está en modo impersonación
    """
    # Bloquear tokens de impersonación en rutas superadmin
    try:
        payload = jwt.decode(
            credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False}
        )
        if payload.get("impersonating"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso a rutas de superadmin no permitido en modo impersonación",
            )
    except JWTError:
        pass  # Si no se puede decodificar, get_current_user ya falló antes

    if not current_user.es_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere ser SuperAdmin del sistema")
    return current_user


def require_not_impersonating(credentials: HTTPAuthorizationCredentials = Depends(security)) -> None:
    """
    Dependencia que bloquea acciones sensibles durante impersonación.
    Usar en endpoints donde el usuario no debe poder actuar como otro (ej: change-password).

    Raises:
        HTTPException 403: Si el token es de impersonación
    """
    try:
        payload = jwt.decode(
            credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False}
        )
        if payload.get("impersonating"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Acción no permitida en modo impersonación"
            )
    except JWTError:
        pass  # Token inválido/expirado: get_current_user ya manejará el error


# ============================================================================
# FUNCIÓN DE AUTENTICACIÓN
# ============================================================================


def authenticate_user(email: str, password: str, db: Session) -> Optional[Usuarios]:
    """
    Autentica un usuario por email y contraseña.

    Args:
        email: Email del usuario
        password: Contraseña en texto plano
        db: Sesión de base de datos

    Returns:
        Usuario si las credenciales son válidas, None en caso contrario

    Ejemplo:
        >>> user = authenticate_user("admin@example.com", "password123", db)
        >>> if user:
        ...     print(f"Autenticado: {user.email}")
    """
    # Buscar usuario por email
    user = db.query(Usuarios).filter(Usuarios.email == email).first()

    if not user:
        # Ejecutar verify_password de todas formas para prevenir timing attacks
        verify_password(password, "$argon2id$v=19$m=65536,t=3,p=4$dummy")
        return None

    # Verificar contraseña
    if not verify_password(password, user.password_hash):
        return None

    # Verificar que esté activo
    if not user.estado:
        return None

    return user


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================


def get_token_expiration(token: str) -> Optional[datetime]:
    """
    Obtiene la fecha de expiración de un token sin validarlo completamente.

    Args:
        token: Token JWT

    Returns:
        Datetime de expiración o None si no se puede decodificar
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},  # No validar expiración
        )
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        return None
    except JWTError:
        return None


def is_token_expired(token: str) -> bool:
    """
    Verifica si un token está expirado.

    Args:
        token: Token JWT

    Returns:
        True si está expirado, False en caso contrario
    """
    expiration = get_token_expiration(token)
    if not expiration:
        return True
    return datetime.now(timezone.utc) > expiration


# Cache de clientes JWKS por URL
_clerk_jwks_clients: dict = {}


def _get_clerk_jwks_client(jwks_url: str) -> PyJWKClient:
    """Retorna un PyJWKClient cacheado para la URL dada."""
    if jwks_url not in _clerk_jwks_clients:
        _clerk_jwks_clients[jwks_url] = PyJWKClient(jwks_url, cache_keys=True, cache_jwk_set=True)
    return _clerk_jwks_clients[jwks_url]


def _decode_jwt_payload_raw(token: str) -> dict:
    """Decodifica el payload de un JWT con base64 puro, sin depender de pyjwt."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Token no tiene formato JWT válido")
    padding = "=" * (4 - len(parts[1]) % 4)
    payload_bytes = _base64.urlsafe_b64decode(parts[1] + padding)
    return _json_mod.loads(payload_bytes)


def verify_clerk_token(token: str) -> dict:
    """
    Verifica un JWT de Clerk usando el endpoint público JWKS.

    Usa CLERK_JWKS_URL si está configurado (recomendado).
    Fallback: deriva la URL del campo 'iss' del JWT via base64 raw decode.

    Raises:
        HTTPException 401: Si el token es inválido o expirado
    """
    try:
        # Preferir URL explícita en config (más confiable)
        jwks_url = settings.CLERK_JWKS_URL

        if not jwks_url:
            # Fallback: extraer iss con base64 puro (no depende de pyjwt behavior)
            payload_raw = _decode_jwt_payload_raw(token)
            iss = payload_raw.get("iss", "")
            if not iss:
                raise ValueError(
                    "CLERK_JWKS_URL no configurado y token sin campo 'iss'. "
                    "Configura CLERK_JWKS_URL=https://<tu-instancia>.clerk.accounts.dev/.well-known/jwks.json"
                )
            jwks_url = f"{iss}/.well-known/jwks.json"

        jwks_client = _get_clerk_jwks_client(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = pyjwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Token de Clerk inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de Clerk inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_tenant_id_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UUID:
    """
    Dependencia para extraer tenant_id directamente del token JWT.

    Útil cuando solo se necesita el tenant_id sin cargar el usuario completo.

    Uso:
        @router.get("/data")
        async def get_data(
            tenant_id: UUID = Depends(get_tenant_id_from_token)
        ):
            # tenant_id disponible directamente

    Returns:
        UUID del tenant

    Raises:
        HTTPException 401: Si el token es inválido o no tiene tenant_id
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    tenant_id_str = payload.get("tenant_id")
    if not tenant_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no contiene tenant_id. Seleccione un tenant primero.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return UUID(tenant_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: tenant_id malformado",
            headers={"WWW-Authenticate": "Bearer"},
        )
