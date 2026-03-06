# Chandelier - Generador de Endpoints API

Crea endpoints FastAPI siguiendo los patrones exactos del proyecto chandelierp.

## Convenciones del Proyecto

- Backend: `backend/app/rutas/` (archivos de rutas)
- Servicios: `backend/app/servicios/` (lógica de negocio)
- Modelos: `backend/app/datos/modelos_tenant.py` (modelos SQLAlchemy)
- Esquemas: dentro de cada archivo de ruta o en schemas separados
- DB: SQLAlchemy 2.0 **sync** (NO async)
- Multi-tenant: SIEMPRE filtrar por `tenant_id`

## Plantilla de Ruta

```python
# backend/app/rutas/{recurso}.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional

from ..datos.db import get_db
from ..datos.modelos_tenant import MiModelo
from ..rutas.auth import get_current_user, get_tenant_id_from_token
from ..datos.modelos import Usuarios
from ..utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


# ---- Schemas Pydantic ----

class RecursoCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    # campos...

    model_config = {"from_attributes": True}

class RecursoResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    nombre: str
    # campos...

    model_config = {"from_attributes": True}


# ---- Endpoints ----

@router.get("/", response_model=List[RecursoResponse])
async def listar_recursos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Lista recursos del tenant actual con paginación."""
    recursos = (
        db.query(MiModelo)
        .filter(MiModelo.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return recursos


@router.get("/{recurso_id}", response_model=RecursoResponse)
async def obtener_recurso(
    recurso_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Obtiene un recurso por ID."""
    recurso = (
        db.query(MiModelo)
        .filter(MiModelo.id == recurso_id, MiModelo.tenant_id == tenant_id)
        .first()
    )
    if not recurso:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")
    return recurso


@router.post("/", response_model=RecursoResponse, status_code=status.HTTP_201_CREATED)
async def crear_recurso(
    data: RecursoCreate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Crea un nuevo recurso."""
    nuevo = MiModelo(tenant_id=tenant_id, **data.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    logger.info(f"Recurso creado: {nuevo.id}", extra={"tenant_id": str(tenant_id)})
    return nuevo


@router.put("/{recurso_id}", response_model=RecursoResponse)
async def actualizar_recurso(
    recurso_id: UUID,
    data: RecursoCreate,
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token),
):
    """Actualiza un recurso existente."""
    recurso = (
        db.query(MiModelo)
        .filter(MiModelo.id == recurso_id, MiModelo.tenant_id == tenant_id)
        .first()
    )
    if not recurso:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")

    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(recurso, campo, valor)

    db.commit()
    db.refresh(recurso)
    return recurso
```

## Registro en main.py

```python
# En backend/app/main.py
from .rutas import mi_recurso
app.include_router(mi_recurso.router, prefix=f"{prefix}/mi-recurso", tags=["Mi Recurso"])
```

## Reglas Clave

- Trailing slash: Endpoints de colección DEBEN usar `"/"` (no `""`)
- Todas las queries filtran por `tenant_id`
- Servicios usan `db.flush()`, rutas hacen `db.commit()`
- Errores de negocio: `ValueError` en servicios, `HTTPException` en rutas
- Schemas plurales: `VentasCreate`, `CotizacionesCreate`
