from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..datos.db import get_db
from ..datos.esquemas import ConfiguracionContableUpdate
from ..datos.modelos import ConfiguracionContable, CuentasContables
from ..servicios.servicio_tenants import ServicioTenants
from ..utils.logger import setup_logger
from ..utils.seguridad import UserContext, require_tenant_roles

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/inicializar")
async def inicializar_configuracion(
    request: Request, db: Session = Depends(get_db), ctx: UserContext = Depends(require_tenant_roles("admin"))
):
    """
    Inicializa la configuración contable básica del tenant.
    Crea cuentas PUC, configuraciones contables, secuencias y medios de pago.
    Útil para tenants creados antes de implementar la inicialización automática.
    """
    tenant_id = getattr(request.state, "tenant_id", None) or ctx.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header requerido")

    servicio = ServicioTenants(db)
    servicio._inicializar_configuracion_tenant(tenant_id)
    db.commit()

    return {"message": "Configuración contable inicializada correctamente"}


@router.get("/")
async def listar_configuracion(
    db: Session = Depends(get_db), ctx: UserContext = Depends(require_tenant_roles("admin", "contador"))
):
    """Lista todas las configuraciones contables del tenant con datos de cuentas."""
    configs = (
        db.query(ConfiguracionContable)
        .filter(ConfiguracionContable.tenant_id == ctx.tenant_id)
        .order_by(ConfiguracionContable.concepto)
        .all()
    )

    result = []
    for cfg in configs:
        item = {
            "id": cfg.id,
            "concepto": cfg.concepto,
            "cuenta_debito_id": cfg.cuenta_debito_id,
            "cuenta_credito_id": cfg.cuenta_credito_id,
            "descripcion": cfg.descripcion,
            "cuenta_debito_codigo": cfg.cuenta_debito.codigo if cfg.cuenta_debito else None,
            "cuenta_debito_nombre": cfg.cuenta_debito.nombre if cfg.cuenta_debito else None,
            "cuenta_credito_codigo": cfg.cuenta_credito.codigo if cfg.cuenta_credito else None,
            "cuenta_credito_nombre": cfg.cuenta_credito.nombre if cfg.cuenta_credito else None,
            "created_at": cfg.created_at,
            "updated_at": cfg.updated_at,
        }
        result.append(item)

    return result


@router.put("/{concepto}")
async def actualizar_configuracion(
    concepto: str,
    data: ConfiguracionContableUpdate,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "contador")),
):
    """Actualiza la configuración contable de un concepto."""
    config = (
        db.query(ConfiguracionContable)
        .filter(ConfiguracionContable.tenant_id == ctx.tenant_id, ConfiguracionContable.concepto == concepto)
        .first()
    )

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Configuración '{concepto}' no encontrada")

    # Validate accounts exist if provided
    if data.cuenta_debito_id is not None:
        cuenta = (
            db.query(CuentasContables)
            .filter(CuentasContables.id == data.cuenta_debito_id, CuentasContables.tenant_id == ctx.tenant_id)
            .first()
        )
        if not cuenta:
            raise HTTPException(status_code=400, detail="Cuenta débito no encontrada")
        config.cuenta_debito_id = data.cuenta_debito_id

    if data.cuenta_credito_id is not None:
        cuenta = (
            db.query(CuentasContables)
            .filter(CuentasContables.id == data.cuenta_credito_id, CuentasContables.tenant_id == ctx.tenant_id)
            .first()
        )
        if not cuenta:
            raise HTTPException(status_code=400, detail="Cuenta crédito no encontrada")
        config.cuenta_credito_id = data.cuenta_credito_id

    if data.descripcion is not None:
        config.descripcion = data.descripcion

    db.commit()
    db.refresh(config)

    return {
        "id": config.id,
        "concepto": config.concepto,
        "cuenta_debito_id": config.cuenta_debito_id,
        "cuenta_credito_id": config.cuenta_credito_id,
        "descripcion": config.descripcion,
        "cuenta_debito_codigo": config.cuenta_debito.codigo if config.cuenta_debito else None,
        "cuenta_debito_nombre": config.cuenta_debito.nombre if config.cuenta_debito else None,
        "cuenta_credito_codigo": config.cuenta_credito.codigo if config.cuenta_credito else None,
        "cuenta_credito_nombre": config.cuenta_credito.nombre if config.cuenta_credito else None,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
    }
