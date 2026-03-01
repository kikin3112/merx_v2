"""
Rutas de Análisis de Precios — módulo Socia.
Expone las herramientas de IO/AO: CVU, sensibilidad, escenarios, comparador, economía de escala.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..datos.db import get_db
from ..datos.esquemas import (
    CVURequest,
    CVUResponse,
    EconomiaEscalaRequest,
    EconomiaEscalaResponse,
    EscalaLote,
    EscenarioPrecioCompleto,
    EscenariosRequest,
    EscenariosResponse,
    RentabilidadItem,
    SensibilidadRequest,
    SensibilidadResponse,
    SensibilidadResultado,
)
from ..servicios.servicio_analisis_cvu import ServicioAnalisisCVU
from ..utils.logger import setup_logger
from ..utils.seguridad import UserContext, require_tenant_roles

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/cvu", response_model=CVUResponse)
async def analisis_cvu(
    data: CVURequest,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Análisis Costo-Volumen-Utilidad completo para una receta.

    Calcula:
    - Costo variable unitario (ingredientes + MO + indirectos)
    - Margen de contribución unitario y ratio
    - Punto de equilibrio en unidades e ingresos
    - Margen de seguridad
    - Utilidad esperada para el volumen dado
    """
    servicio = ServicioAnalisisCVU(db=db, tenant_id=ctx.tenant_id)
    try:
        result = servicio.calcular_cvu(
            receta_id=data.receta_id,
            precio_venta=data.precio_venta,
            costos_fijos_periodo=data.costos_fijos_periodo,
            volumen_esperado=data.volumen_esperado,
        )
        return CVUResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/sensibilidad", response_model=SensibilidadResponse)
async def analisis_sensibilidad(
    data: SensibilidadRequest,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Análisis de sensibilidad: ¿qué pasa si...?

    Para cada variación (precio_venta, mano_obra, costos_fijos, volumen),
    recalcula el punto de equilibrio y la utilidad esperada.
    Permite responder: "Si el costo sube 20%, ¿cuántas unidades más debo vender?"
    """
    servicio = ServicioAnalisisCVU(db=db, tenant_id=ctx.tenant_id)
    variaciones_raw = [v.model_dump() for v in data.variaciones]
    try:
        result = servicio.analisis_sensibilidad(
            receta_id=data.receta_id,
            precio_venta=data.precio_venta,
            costos_fijos=data.costos_fijos,
            volumen_base=data.volumen_base,
            variaciones=variaciones_raw,
        )
        resultados = [SensibilidadResultado(**r) for r in result["resultados"]]
        return SensibilidadResponse(
            receta_nombre=result["receta_nombre"],
            pe_base_unidades=result["pe_base_unidades"],
            pe_base_ingresos=result["pe_base_ingresos"],
            utilidad_base=result["utilidad_base"],
            resultados=resultados,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/escenarios", response_model=EscenariosResponse)
async def escenarios_precio(
    data: EscenariosRequest,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Genera 5 escenarios de precio:
    1. Precio mínimo (solo cubre costos variables)
    2. Precio de equilibrio (cubre CF con el volumen dado)
    3. Precio objetivo (logra el margen_objetivo de la receta)
    4. Precio de mercado (referencia externa opcional)
    5. Precio premium (mercado * 1.30)
    """
    servicio = ServicioAnalisisCVU(db=db, tenant_id=ctx.tenant_id)
    try:
        result = servicio.generar_escenarios_precio(
            receta_id=data.receta_id,
            costos_fijos=data.costos_fijos,
            volumen=data.volumen,
            precio_mercado_referencia=data.precio_mercado_referencia,
        )
        escenarios = [EscenarioPrecioCompleto(**e) for e in result["escenarios"]]
        return EscenariosResponse(
            receta_nombre=result["receta_nombre"],
            costo_variable_unitario=result["costo_variable_unitario"],
            escenarios=escenarios,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/comparador", response_model=List[RentabilidadItem])
async def comparador_rentabilidad(
    receta_ids: Optional[str] = None,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Comparador de rentabilidad multi-receta.
    Ordena por margen de contribución % descendente.

    Si se pasan receta_ids (CSV de UUIDs), filtra a esas recetas.
    Sin parámetros: compara todas las recetas activas del tenant.
    """
    servicio = ServicioAnalisisCVU(db=db, tenant_id=ctx.tenant_id)
    ids: Optional[List[UUID]] = None
    if receta_ids:
        try:
            ids = [UUID(rid.strip()) for rid in receta_ids.split(",") if rid.strip()]
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="receta_ids inválidos")

    resultado = servicio.comparar_rentabilidad(ids)
    return [RentabilidadItem(**r) for r in resultado]


@router.post("/economia-escala", response_model=EconomiaEscalaResponse)
async def economia_escala(
    data: EconomiaEscalaRequest,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_tenant_roles("admin", "operador")),
):
    """
    Curva de economía de escala.
    Para cada tamaño de lote, calcula el costo unitario promedio
    con el costo fijo de setup prorrateado.
    """
    servicio = ServicioAnalisisCVU(db=db, tenant_id=ctx.tenant_id)
    try:
        result = servicio.calcular_economia_escala(
            receta_id=data.receta_id,
            costos_fijos_setup=data.costos_fijos_setup,
            lotes=data.lotes,
        )
        escala = [EscalaLote(**e) for e in result["escala"]]
        return EconomiaEscalaResponse(
            receta_nombre=result["receta_nombre"],
            costo_variable_unitario=result["costo_variable_unitario"],
            escala=escala,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
