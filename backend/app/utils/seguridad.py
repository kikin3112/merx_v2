"""
Utilidades de seguridad: JWT, hashing de passwords, autenticación.
Usa Argon2 para hashing (más seguro que bcrypt).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Callable
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID

from ..config import settings
from ..datos.db import get_db
from ..datos.modelos import Usuarios
from ..utils.logger import setup_logger, set_request_context

logger = setup_logger(__name__)

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
    argon2__parallelism=4  # 4 hilos paralelos
)

# ============================================================================
# ESQUEMA DE SEGURIDAD BEARER
# ============================================================================

security = HTTPBearer(
    scheme_name="JWT",
    description="Token JWT en header Authorization: Bearer {token}",
    auto_error=True  # Lanza error automáticamente si falta el token
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

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un access token JWT.

    Args:
        data: Datos a incluir (típicamente {"sub": user_id, "email": ..., "rol": ...})
        expires_delta: Tiempo de expiración personalizado (default: 30 min)

    Returns:
        Token JWT codificado

    Ejemplo:
        >>> token = create_access_token(
        ...     data={"sub": str(user.id), "email": user.email, "rol": user.rol}
        ... )
    """
    to_encode = data.copy()

    # Usar timezone aware datetime (Python 3.12+)
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,  # Issued at
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

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
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Validar que sea access token
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: tipo incorrecto",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return payload

    except JWTError as e:
        logger.warning(f"Token JWT inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
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

    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

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
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Validar que sea refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: no es un refresh token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return payload

    except JWTError as e:
        logger.warning(f"Refresh token inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )


# ============================================================================
# DEPENDENCIAS DE AUTENTICACIÓN
# ============================================================================

def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> Usuarios:
    """
    Dependencia de FastAPI para obtener el usuario autenticado.

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
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Validar formato UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: ID de usuario malformado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Buscar usuario en DB
    user = db.query(Usuarios).filter(Usuarios.id == user_uuid).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Validar que esté activo
    if not user.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )

    # Establecer contexto de usuario para logging
    set_request_context(user_id=str(user.id))

    return user


def get_current_active_admin(
        current_user: Usuarios = Depends(get_current_user)
) -> Usuarios:
    """
    Dependencia para rutas que requieren rol admin.

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
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes. Se requiere rol admin"
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
                detail=f"Permisos insuficientes. Se requiere uno de los roles: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


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
            options={"verify_exp": False}  # No validar expiración
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