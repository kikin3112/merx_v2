# Chandelier - Autenticación y Autorización

Sistema de autenticación JWT multi-tenant usado en el proyecto.

## Stack

- JWT: HS256 via `python-jose`
- Passwords: Argon2 via `passlib`
- Dependencies: `get_current_user`, `get_tenant_id_from_token`

## Dependencias de Auth

```python
# backend/app/rutas/auth.py (extracto de dependencies)
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from uuid import UUID

from ..config import settings
from ..datos.db import get_db
from ..datos.modelos import Usuarios

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuarios:
    """Decodifica JWT y retorna usuario autenticado."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(Usuarios).filter(Usuarios.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user

async def get_tenant_id_from_token(
    token: str = Depends(oauth2_scheme),
) -> UUID:
    """Extrae tenant_id del payload JWT."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant no seleccionado")
        return UUID(tenant_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
```

## Uso en Endpoints

```python
from ..rutas.auth import get_current_user, get_tenant_id_from_token
from ..datos.modelos import Usuarios

@router.get("/")
async def mi_endpoint(
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    # current_user tiene: id, email, rol, es_superadmin
    # tenant_id: UUID del tenant seleccionado
    ...
```

## Token Payload

```json
{
  "sub": "user-uuid",
  "email": "user@email.com",
  "rol": "admin",
  "tenant_id": "tenant-uuid",
  "rol_en_tenant": "admin",
  "exp": 1234567890
}
```

## Flujo de Login

1. `POST /api/v1/auth/login` (email + password) -> access_token + refresh_token + tenants[]
2. `POST /api/v1/auth/select-tenant` (tenant_id) -> new access_token con tenant_id embebido
3. Todos los requests posteriores llevan `Authorization: Bearer <token>` + `X-Tenant-ID: <uuid>`

## Credenciales Dev

- superadmin@chandelier.com / superadmin123
- admin@example.com / admin123
- operador@emprendedora.co / operador123
