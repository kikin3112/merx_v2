from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc
from typing import Optional
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID
from collections import defaultdict

from ..datos.db import get_db
from ..datos.modelos import (
    Ventas, VentasDetalle, Productos, Inventarios, Terceros, Usuarios, Cotizaciones
)
from ..utils.seguridad import get_current_user, get_tenant_id_from_token
from ..utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/dashboard")
async def dashboard_kpis(
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """KPIs principales del dashboard. Accepts optional date range filters."""
    hoy = date.today()

    query = db.query(Ventas).filter(
        Ventas.tenant_id == tenant_id,
        Ventas.estado.in_(["CONFIRMADA", "FACTURADA"])
    )
    if fecha_inicio:
        query = query.filter(Ventas.fecha_venta >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Ventas.fecha_venta <= fecha_fin)

    ventas = query.all()

    total_ventas = sum(v.total_venta for v in ventas)
    cantidad_ventas = len(ventas)

    # Ventas de hoy (within filtered set)
    ventas_hoy = [v for v in ventas if v.fecha_venta == hoy]
    total_hoy = sum(v.total_venta for v in ventas_hoy)

    # Ventas últimos 30 días (within filtered set)
    hace_30 = hoy - timedelta(days=30)
    ventas_mes = [v for v in ventas if v.fecha_venta >= hace_30]
    total_mes = sum(v.total_venta for v in ventas_mes)

    # Stock bajo (always current)
    alertas_stock = db.query(Inventarios).join(
        Productos, Productos.id == Inventarios.producto_id
    ).filter(
        Inventarios.tenant_id == tenant_id,
        Productos.stock_minimo.isnot(None),
        Inventarios.cantidad_disponible <= Productos.stock_minimo
    ).count()

    # Facturas pendientes de cobro (always current)
    facturas_pendientes = db.query(Ventas).filter(
        Ventas.tenant_id == tenant_id,
        Ventas.estado == "FACTURADA"
    ).all()
    total_pendiente = sum(v.total_venta for v in facturas_pendientes)

    return {
        "total_ventas": float(total_ventas),
        "cantidad_ventas": cantidad_ventas,
        "promedio_venta": float(total_ventas / cantidad_ventas) if cantidad_ventas > 0 else 0,
        "alertas_stock_bajo": alertas_stock,
        "ventas_hoy": float(total_hoy),
        "cantidad_hoy": len(ventas_hoy),
        "ventas_mes": float(total_mes),
        "cantidad_mes": len(ventas_mes),
        "facturas_pendientes": float(total_pendiente),
        "cantidad_facturas_pendientes": len(facturas_pendientes),
    }


@router.get("/ventas")
async def reporte_ventas(
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Reporte de ventas por periodo."""
    query = db.query(Ventas).filter(
        Ventas.tenant_id == tenant_id,
        Ventas.estado != "ANULADA"
    )
    if fecha_inicio:
        query = query.filter(Ventas.fecha_venta >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Ventas.fecha_venta <= fecha_fin)

    ventas = query.order_by(Ventas.fecha_venta.desc()).all()

    total = sum(v.total_venta for v in ventas)
    return {
        "total_ventas": float(total),
        "cantidad": len(ventas),
        "promedio": float(total / len(ventas)) if ventas else 0
    }


@router.get("/ventas-diarias")
async def ventas_diarias(
    dias: int = Query(30, ge=7, le=365),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Ventas agrupadas por día para gráfico de línea.
    Retorna todos los días del período (incluyendo días sin ventas = 0).
    Accepts fecha_inicio/fecha_fin or dias param.
    """
    hoy = date.today()
    if fecha_inicio and fecha_fin:
        inicio = fecha_inicio
        fin = fecha_fin
    else:
        inicio = hoy - timedelta(days=dias - 1)
        fin = hoy

    num_dias = (fin - inicio).days + 1

    ventas = db.query(Ventas).filter(
        Ventas.tenant_id == tenant_id,
        Ventas.estado.in_(["CONFIRMADA", "FACTURADA"]),
        Ventas.fecha_venta >= inicio,
        Ventas.fecha_venta <= fin
    ).all()

    # Agrupar por fecha
    por_dia: dict[date, dict] = {}
    for v in ventas:
        dia = v.fecha_venta
        if dia not in por_dia:
            por_dia[dia] = {"total": Decimal("0"), "cantidad": 0}
        por_dia[dia]["total"] += v.total_venta
        por_dia[dia]["cantidad"] += 1

    # Rellenar días sin ventas
    resultado = []
    for i in range(num_dias):
        dia = inicio + timedelta(days=i)
        info = por_dia.get(dia, {"total": Decimal("0"), "cantidad": 0})
        resultado.append({
            "fecha": dia.isoformat(),
            "total": float(info["total"]),
            "cantidad": info["cantidad"]
        })

    return resultado


@router.get("/productos-top")
async def productos_top(
    limite: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Top productos por valor de inventario."""
    inventarios = db.query(
        Productos.nombre,
        Productos.codigo_interno,
        Inventarios.cantidad_disponible,
        Inventarios.valor_total
    ).join(
        Inventarios, Productos.id == Inventarios.producto_id
    ).filter(
        Productos.tenant_id == tenant_id,
        Productos.deleted_at.is_(None),
        Inventarios.cantidad_disponible > 0
    ).order_by(Inventarios.valor_total.desc()).limit(limite).all()

    return [
        {
            "nombre": row.nombre,
            "codigo": row.codigo_interno,
            "stock": float(row.cantidad_disponible),
            "valor_total": float(row.valor_total)
        }
        for row in inventarios
    ]


@router.get("/productos-mas-vendidos")
async def productos_mas_vendidos(
    limite: int = Query(10, ge=1, le=50),
    dias: int = Query(30, ge=1, le=365),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Top productos por cantidad vendida en un período."""
    if fecha_inicio and fecha_fin:
        inicio = fecha_inicio
        fin = fecha_fin
    else:
        inicio = date.today() - timedelta(days=dias)
        fin = date.today()

    ventas_activas = db.query(Ventas.id).filter(
        Ventas.tenant_id == tenant_id,
        Ventas.estado.in_(["CONFIRMADA", "FACTURADA"]),
        Ventas.fecha_venta >= inicio,
        Ventas.fecha_venta <= fin
    ).subquery()

    resultados = db.query(
        Productos.id,
        Productos.nombre,
        Productos.codigo_interno,
        Productos.precio_venta,
        func.sum(VentasDetalle.cantidad).label("total_cantidad"),
        func.sum(VentasDetalle.cantidad * VentasDetalle.precio_unitario).label("total_ingresos")
    ).join(
        VentasDetalle, Productos.id == VentasDetalle.producto_id
    ).filter(
        VentasDetalle.venta_id.in_(ventas_activas),
        Productos.tenant_id == tenant_id
    ).group_by(
        Productos.id, Productos.nombre, Productos.codigo_interno, Productos.precio_venta
    ).order_by(desc("total_ingresos")).limit(limite).all()

    return [
        {
            "producto_id": str(row.id),
            "nombre": row.nombre,
            "codigo": row.codigo_interno,
            "precio_venta": float(row.precio_venta),
            "total_cantidad": float(row.total_cantidad),
            "total_ingresos": float(row.total_ingresos)
        }
        for row in resultados
    ]


@router.get("/top-clientes")
async def top_clientes(
    limite: int = Query(10, ge=1, le=50),
    dias: int = Query(90, ge=1, le=365),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """Top clientes por monto total de ventas."""
    if fecha_inicio and fecha_fin:
        inicio = fecha_inicio
        fin = fecha_fin
    else:
        inicio = date.today() - timedelta(days=dias)
        fin = date.today()

    ventas = db.query(Ventas).filter(
        Ventas.tenant_id == tenant_id,
        Ventas.estado.in_(["CONFIRMADA", "FACTURADA"]),
        Ventas.fecha_venta >= inicio,
        Ventas.fecha_venta <= fin
    ).all()

    # Agrupar por tercero
    por_tercero: dict[str, dict] = {}
    for v in ventas:
        tid = str(v.tercero_id)
        if tid not in por_tercero:
            por_tercero[tid] = {"total": Decimal("0"), "cantidad": 0}
        por_tercero[tid]["total"] += v.total_venta
        por_tercero[tid]["cantidad"] += 1

    if not por_tercero:
        return []

    # Obtener nombres
    tercero_ids = [UUID(t) for t in por_tercero.keys()]
    terceros = db.query(Terceros).filter(Terceros.id.in_(tercero_ids)).all()
    nombres = {str(t.id): t.nombre for t in terceros}

    # Ordenar y limitar
    ranking = sorted(por_tercero.items(), key=lambda x: x[1]["total"], reverse=True)[:limite]

    return [
        {
            "tercero_id": tid,
            "nombre": nombres.get(tid, "Desconocido"),
            "total_ventas": float(info["total"]),
            "cantidad_ventas": info["cantidad"]
        }
        for tid, info in ranking
    ]


@router.get("/rentabilidad")
async def rentabilidad_productos(
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Rentabilidad por producto: precio_venta vs costo_promedio.
    Incluye margen bruto y % margen.
    """
    resultados = db.query(
        Productos.id,
        Productos.nombre,
        Productos.codigo_interno,
        Productos.categoria,
        Productos.precio_venta,
        Inventarios.costo_promedio_ponderado,
        Inventarios.cantidad_disponible,
        Inventarios.valor_total
    ).join(
        Inventarios, Productos.id == Inventarios.producto_id
    ).filter(
        Productos.tenant_id == tenant_id,
        Productos.deleted_at.is_(None),
        Productos.precio_venta > 0
    ).order_by(Productos.nombre).limit(limite).all()

    return [
        {
            "producto_id": str(row.id),
            "nombre": row.nombre,
            "codigo": row.codigo_interno,
            "categoria": row.categoria,
            "precio_venta": float(row.precio_venta),
            "costo_promedio": float(row.costo_promedio_ponderado),
            "margen_bruto": float(row.precio_venta - row.costo_promedio_ponderado),
            "margen_porcentaje": round(
                float((row.precio_venta - row.costo_promedio_ponderado) / row.precio_venta * 100), 1
            ) if row.precio_venta > 0 else 0,
            "stock": float(row.cantidad_disponible),
            "valor_inventario": float(row.valor_total)
        }
        for row in resultados
    ]


@router.get("/abc-inventario")
async def abc_inventario(
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Análisis ABC de inventario.
    Clasifica productos por contribución al valor total:
    A = 80% del valor (pocos productos de alto valor)
    B = 15% del valor (medio)
    C = 5% del valor (muchos productos de bajo valor)
    """
    items = db.query(
        Productos.id,
        Productos.nombre,
        Productos.codigo_interno,
        Inventarios.cantidad_disponible,
        Inventarios.valor_total
    ).join(
        Inventarios, Productos.id == Inventarios.producto_id
    ).filter(
        Productos.tenant_id == tenant_id,
        Productos.deleted_at.is_(None),
        Inventarios.cantidad_disponible > 0,
        Inventarios.valor_total > 0
    ).order_by(Inventarios.valor_total.desc()).all()

    if not items:
        return {"productos": [], "resumen": {"A": 0, "B": 0, "C": 0}}

    valor_total = sum(float(i.valor_total) for i in items)

    resultado = []
    acumulado = 0.0
    conteo = {"A": 0, "B": 0, "C": 0}

    for item in items:
        valor = float(item.valor_total)
        acumulado += valor
        porcentaje_acumulado = (acumulado / valor_total * 100) if valor_total > 0 else 0

        if porcentaje_acumulado <= 80:
            clasificacion = "A"
        elif porcentaje_acumulado <= 95:
            clasificacion = "B"
        else:
            clasificacion = "C"

        conteo[clasificacion] += 1
        resultado.append({
            "producto_id": str(item.id),
            "nombre": item.nombre,
            "codigo": item.codigo_interno,
            "stock": float(item.cantidad_disponible),
            "valor_total": valor,
            "porcentaje_valor": round(valor / valor_total * 100, 1) if valor_total > 0 else 0,
            "porcentaje_acumulado": round(porcentaje_acumulado, 1),
            "clasificacion": clasificacion
        })

    return {
        "productos": resultado,
        "resumen": conteo,
        "valor_total_inventario": valor_total
    }


@router.get("/rentabilidad-categoria")
async def rentabilidad_por_categoria(
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Rentabilidad agregada por categoría de producto.
    Calcula precio promedio, costo promedio, margen promedio y valor de inventario por categoría.
    """
    resultados = db.query(
        Productos.categoria,
        func.count(Productos.id).label("cantidad_productos"),
        func.avg(Productos.precio_venta).label("precio_promedio"),
        func.avg(Inventarios.costo_promedio_ponderado).label("costo_promedio"),
        func.sum(Inventarios.valor_total).label("valor_inventario"),
        func.sum(Inventarios.cantidad_disponible).label("stock_total"),
    ).join(
        Inventarios, Productos.id == Inventarios.producto_id
    ).filter(
        Productos.tenant_id == tenant_id,
        Productos.deleted_at.is_(None),
        Productos.precio_venta > 0
    ).group_by(Productos.categoria).all()

    return [
        {
            "categoria": row.categoria,
            "cantidad_productos": row.cantidad_productos,
            "precio_promedio": round(float(row.precio_promedio or 0), 2),
            "costo_promedio": round(float(row.costo_promedio or 0), 2),
            "margen_promedio": round(
                float((row.precio_promedio - row.costo_promedio) / row.precio_promedio * 100), 1
            ) if row.precio_promedio and row.precio_promedio > 0 else 0,
            "valor_inventario": round(float(row.valor_inventario or 0), 2),
            "stock_total": round(float(row.stock_total or 0), 2),
        }
        for row in resultados
    ]


@router.get("/comparativa-mensual")
async def comparativa_mensual(
    fecha_referencia: Optional[date] = Query(None, description="Any date in the month to compare. Defaults to today."),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Comparativa mes actual vs mes anterior.
    Retorna total ventas, cantidad, promedio con variación porcentual.
    Use fecha_referencia to compare any month vs its previous.
    """
    ref = fecha_referencia or date.today()
    inicio_mes_actual = ref.replace(day=1)

    # Mes anterior
    if ref.month == 1:
        inicio_mes_anterior = ref.replace(year=ref.year - 1, month=12, day=1)
    else:
        inicio_mes_anterior = ref.replace(month=ref.month - 1, day=1)
    fin_mes_anterior = inicio_mes_actual - timedelta(days=1)

    # Fin del reference month (last day or ref date if current month)
    hoy = date.today()
    if ref.year == hoy.year and ref.month == hoy.month:
        fin_mes_actual = hoy
    else:
        # Last day of the reference month
        if ref.month == 12:
            fin_mes_actual = ref.replace(year=ref.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            fin_mes_actual = ref.replace(month=ref.month + 1, day=1) - timedelta(days=1)

    # Ventas mes actual
    ventas_actual = db.query(Ventas).filter(
        Ventas.tenant_id == tenant_id,
        Ventas.estado.in_(["CONFIRMADA", "FACTURADA"]),
        Ventas.fecha_venta >= inicio_mes_actual,
        Ventas.fecha_venta <= fin_mes_actual
    ).all()

    # Ventas mes anterior
    ventas_anterior = db.query(Ventas).filter(
        Ventas.tenant_id == tenant_id,
        Ventas.estado.in_(["CONFIRMADA", "FACTURADA"]),
        Ventas.fecha_venta >= inicio_mes_anterior,
        Ventas.fecha_venta <= fin_mes_anterior
    ).all()

    total_actual = sum(v.total_venta for v in ventas_actual)
    cant_actual = len(ventas_actual)
    prom_actual = total_actual / cant_actual if cant_actual > 0 else Decimal("0")

    total_anterior = sum(v.total_venta for v in ventas_anterior)
    cant_anterior = len(ventas_anterior)
    prom_anterior = total_anterior / cant_anterior if cant_anterior > 0 else Decimal("0")

    def variacion(actual, anterior):
        if anterior == 0:
            return 100.0 if actual > 0 else 0.0
        return round(float((actual - anterior) / anterior * 100), 1)

    return {
        "mes_actual": {
            "total_ventas": float(total_actual),
            "cantidad_ventas": cant_actual,
            "promedio_venta": float(prom_actual),
            "periodo": f"{inicio_mes_actual.isoformat()} a {fin_mes_actual.isoformat()}"
        },
        "mes_anterior": {
            "total_ventas": float(total_anterior),
            "cantidad_ventas": cant_anterior,
            "promedio_venta": float(prom_anterior),
            "periodo": f"{inicio_mes_anterior.isoformat()} a {fin_mes_anterior.isoformat()}"
        },
        "variacion": {
            "total_ventas": variacion(total_actual, total_anterior),
            "cantidad_ventas": variacion(cant_actual, cant_anterior),
            "promedio_venta": variacion(prom_actual, prom_anterior),
        }
    }


@router.get("/proyeccion-flujo-caja")
async def proyeccion_flujo_caja(
    dias_proyeccion: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Proyección de flujo de caja basada en histórico de 90 días + facturas pendientes.
    """
    hoy = date.today()
    hace_90 = hoy - timedelta(days=90)

    # Ventas históricas (90 días)
    ventas = db.query(Ventas).filter(
        Ventas.tenant_id == tenant_id,
        Ventas.estado.in_(["CONFIRMADA", "FACTURADA"]),
        Ventas.fecha_venta >= hace_90,
        Ventas.fecha_venta <= hoy
    ).all()

    total_historico = sum((v.total_venta for v in ventas), Decimal("0"))
    dias_con_datos = (hoy - hace_90).days or 1
    promedio_diario = total_historico / dias_con_datos

    # Facturas pendientes (por cobrar)
    facturas_pendientes = db.query(Ventas).filter(
        Ventas.tenant_id == tenant_id,
        Ventas.estado == "FACTURADA"
    ).all()
    total_por_cobrar = sum((v.total_venta for v in facturas_pendientes), Decimal("0"))

    # Proyección diaria
    proyeccion = []
    acumulado = Decimal("0")
    for i in range(1, dias_proyeccion + 1):
        dia = hoy + timedelta(days=i)
        acumulado += promedio_diario
        proyeccion.append({
            "fecha": dia.isoformat(),
            "proyectado_dia": float(promedio_diario),
            "acumulado": float(acumulado),
        })

    return {
        "promedio_diario": float(promedio_diario),
        "total_por_cobrar": float(total_por_cobrar),
        "cantidad_facturas_pendientes": len(facturas_pendientes),
        "total_proyectado": float(promedio_diario * dias_proyeccion),
        "dias_proyeccion": dias_proyeccion,
        "proyeccion": proyeccion,
    }


@router.get("/margenes-categoria")
async def margenes_por_categoria(
    dias: int = Query(30, ge=7, le=365),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuarios = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id_from_token)
):
    """
    Márgenes basados en ventas reales por categoría.
    Calcula ingresos vs costo estimado por categoría en el período.
    """
    if fecha_inicio and fecha_fin:
        inicio = fecha_inicio
        fin = fecha_fin
    else:
        inicio = date.today() - timedelta(days=dias)
        fin = date.today()

    ventas_activas = db.query(Ventas.id).filter(
        Ventas.tenant_id == tenant_id,
        Ventas.estado.in_(["CONFIRMADA", "FACTURADA"]),
        Ventas.fecha_venta >= inicio,
        Ventas.fecha_venta <= fin
    ).subquery()

    # Detalles con info de producto e inventario
    detalles = db.query(
        Productos.categoria,
        VentasDetalle.cantidad,
        VentasDetalle.precio_unitario,
        VentasDetalle.descuento,
        Inventarios.costo_promedio_ponderado,
    ).join(
        Productos, VentasDetalle.producto_id == Productos.id
    ).outerjoin(
        Inventarios, Productos.id == Inventarios.producto_id
    ).filter(
        VentasDetalle.venta_id.in_(ventas_activas),
        Productos.tenant_id == tenant_id
    ).all()

    # Agrupar por categoría
    por_categoria: dict = {}
    for row in detalles:
        cat = row.categoria
        if cat not in por_categoria:
            por_categoria[cat] = {"ingresos": Decimal("0"), "costo": Decimal("0"), "cantidad_items": 0}

        ingreso_linea = row.cantidad * row.precio_unitario - row.descuento
        costo_linea = row.cantidad * (row.costo_promedio_ponderado or Decimal("0"))

        por_categoria[cat]["ingresos"] += ingreso_linea
        por_categoria[cat]["costo"] += costo_linea
        por_categoria[cat]["cantidad_items"] += 1

    resultado = []
    for cat, data in sorted(por_categoria.items()):
        ingresos = float(data["ingresos"])
        costo = float(data["costo"])
        margen = ingresos - costo
        margen_pct = (margen / ingresos * 100) if ingresos > 0 else 0

        resultado.append({
            "categoria": cat,
            "ingresos": round(ingresos, 2),
            "costo": round(costo, 2),
            "margen": round(margen, 2),
            "margen_porcentaje": round(margen_pct, 1),
            "cantidad_items": data["cantidad_items"],
        })

    return resultado
