"""
Módulo Comercial — Pipeline unificado de cotizaciones, ventas y facturas.
Endpoint: GET /api/v1/comercial/pipeline
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..datos.db import get_db
from ..datos.esquemas import CotizacionesResponse, VentasResponse
from ..servicios.servicio_comercial import ServicioComercial
from ..utils.seguridad import UserContext, require_tenant_roles

router = APIRouter()


@router.get("/pipeline")
async def obtener_pipeline(
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "vendedor", "contador")),
):
    """
    Retorna el estado completo del pipeline comercial:
    - cotizaciones VIGENTE/PENDIENTE
    - ventas_pendientes (PENDIENTE)
    - ventas_confirmadas (CONFIRMADA)
    - facturas_recientes (FACTURADA)
    - resumen: {total_cotizado, por_cobrar, facturado_mes}
    """
    servicio = ServicioComercial()
    pipeline = servicio.obtener_pipeline(db, ctx.tenant_id)

    return {
        "cotizaciones": [CotizacionesResponse.model_validate(c) for c in pipeline["cotizaciones"]],
        "ventas_pendientes": [VentasResponse.model_validate(v) for v in pipeline["ventas_pendientes"]],
        "ventas_confirmadas": [VentasResponse.model_validate(v) for v in pipeline["ventas_confirmadas"]],
        "facturas_recientes": [VentasResponse.model_validate(v) for v in pipeline["facturas_recientes"]],
        "resumen": pipeline["resumen"],
    }
