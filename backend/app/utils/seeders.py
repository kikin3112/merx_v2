"""
Seeders: Datos iniciales para desarrollo y testing.
Ejecutar con: POST /api/v1/admin/seed
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict
from uuid import UUID

from sqlalchemy.orm import Session

from ..datos.db import SessionLocal
from ..datos.modelos import (
    ConfiguracionContable,
    CuentasContables,
    Inventarios,
    MediosPago,
    Productos,
    Secuencias,
    Terceros,
    Usuarios,
)
from ..datos.modelos_tenant import Planes, Suscripciones, Tenants, UsuariosTenants
from ..utils.logger import setup_logger
from ..utils.seguridad import hash_password

logger = setup_logger(__name__)


# ============================================================================
# SEED: PLANES
# ============================================================================


def seed_planes(db: Session) -> UUID:
    """Crea planes de suscripción. Retorna el ID del plan default."""
    logger.info("Creando planes...")

    planes = [
        {
            "nombre": "Free Trial",
            "descripcion": "Plan gratuito de prueba por 14 días",
            "precio_mensual": Decimal("0.00"),
            "max_usuarios": 2,
            "max_productos": 500,
            "max_facturas_mes": 30,
            "max_storage_mb": 100,
            "esta_activo": True,
            "es_default": True,
            "caracteristicas": {"trial_days": 14},
        },
        {
            "nombre": "Pro",
            "descripcion": "Plan profesional para microempresas",
            "precio_mensual": Decimal("49900.00"),
            "precio_anual": Decimal("499000.00"),
            "max_usuarios": 5,
            "max_productos": 500,
            "max_facturas_mes": 500,
            "max_storage_mb": 2048,
            "esta_activo": True,
            "es_default": False,
            "caracteristicas": {"reportes_avanzados": True, "soporte_prioritario": True},
        },
    ]

    plan_default_id = None
    for plan_data in planes:
        existing = db.query(Planes).filter(Planes.nombre == plan_data["nombre"]).first()
        if not existing:
            plan = Planes(**plan_data)
            db.add(plan)
            db.flush()
            if plan_data["es_default"]:
                plan_default_id = plan.id
            logger.info(f"  Plan creado: {plan_data['nombre']}")
        else:
            # Actualizar límites del plan existente para reflejar cambios de configuración
            for field in ("max_usuarios", "max_productos", "max_facturas_mes", "max_storage_mb"):
                if field in plan_data:
                    setattr(existing, field, plan_data[field])
            db.flush()
            if plan_data["es_default"]:
                plan_default_id = existing.id
            logger.info(f"  Plan actualizado: {plan_data['nombre']}")

    db.commit()
    return plan_default_id


# ============================================================================
# SEED: SUPERADMIN + TENANT DEMO
# ============================================================================


def seed_superadmin_and_tenant(db: Session, plan_id: UUID) -> tuple[UUID, UUID]:
    """
    Crea superadmin y un tenant demo.
    Retorna (tenant_id, admin_user_id).
    """
    logger.info("Creando superadmin y tenant demo...")

    # Superadmin
    superadmin = db.query(Usuarios).filter(Usuarios.email == "superadmin@chandelier.com").first()
    if not superadmin:
        superadmin = Usuarios(
            nombre="Super Administrador",
            email="superadmin@chandelier.com",
            password_hash=hash_password("superadmin123"),
            rol="superadmin",
            estado=True,
            es_superadmin=True,
        )
        db.add(superadmin)
        db.flush()
        logger.info("  Superadmin creado: superadmin@chandelier.com / superadmin123")

    # Tenant demo
    tenant = db.query(Tenants).filter(Tenants.slug == "demo").first()
    if not tenant:
        tenant = Tenants(
            nombre="Emprendedora Demo",
            slug="demo",
            nit="900999999",
            email_contacto="demo@emprendedora.co",
            telefono="3001234567",
            direccion="Calle 100 #20-30",
            ciudad="Bogotá",
            departamento="Cundinamarca",
            plan_id=plan_id,
            estado="activo",
            fecha_inicio_suscripcion=datetime.now(timezone.utc),
            fecha_fin_suscripcion=datetime.now(timezone.utc) + timedelta(days=365),
        )
        db.add(tenant)
        db.flush()
        logger.info(f"  Tenant demo creado: {tenant.nombre} (ID: {tenant.id})")

    # Admin del tenant
    admin = db.query(Usuarios).filter(Usuarios.email == "admin@example.com").first()
    if not admin:
        admin = Usuarios(
            nombre="Admin Demo",
            email="admin@example.com",
            password_hash=hash_password("admin123"),
            rol="admin",
            estado=True,
            es_superadmin=False,
        )
        db.add(admin)
        db.flush()
        logger.info("  Admin tenant: admin@example.com / admin123")

    # Relación admin-tenant
    rel = (
        db.query(UsuariosTenants)
        .filter(UsuariosTenants.usuario_id == admin.id, UsuariosTenants.tenant_id == tenant.id)
        .first()
    )
    if not rel:
        rel = UsuariosTenants(usuario_id=admin.id, tenant_id=tenant.id, rol="admin", esta_activo=True, es_default=True)
        db.add(rel)

    # NOTA: El superadmin NO se asigna a ningún tenant.
    # El rol superadmin es exclusivo del sistema (es_superadmin=True en Usuarios).
    # El superadmin gestiona tenants sin pertenecer a ellos.

    # Operador de prueba
    operador = db.query(Usuarios).filter(Usuarios.email == "operador@emprendedora.co").first()
    if not operador:
        operador = Usuarios(
            nombre="Operador Ventas",
            email="operador@emprendedora.co",
            password_hash=hash_password("operador123"),
            rol="operador",
            estado=True,
            es_superadmin=False,
        )
        db.add(operador)
        db.flush()

        rel_op = UsuariosTenants(
            usuario_id=operador.id, tenant_id=tenant.id, rol="vendedor", esta_activo=True, es_default=True
        )
        db.add(rel_op)
        logger.info("  Operador: operador@emprendedora.co / operador123")

    # Suscripción
    sub = db.query(Suscripciones).filter(Suscripciones.tenant_id == tenant.id).first()
    if not sub:
        sub = Suscripciones(
            tenant_id=tenant.id,
            plan_id=plan_id,
            periodo_inicio=datetime.now(timezone.utc),
            periodo_fin=datetime.now(timezone.utc) + timedelta(days=365),
            estado="activo",
        )
        db.add(sub)

    db.commit()
    return tenant.id, admin.id


# ============================================================================
# SEED: SECUENCIAS (tenant-scoped)
# ============================================================================


def seed_secuencias(db: Session, tenant_id: UUID):
    """Crea secuencias para numeración automática."""
    logger.info("Creando secuencias...")

    secuencias = [
        {"nombre": "COMPRAS", "prefijo": "CMP-", "siguiente_numero": 1, "longitud_numero": 6},
        {"nombre": "COTIZACIONES", "prefijo": "COT-", "siguiente_numero": 1, "longitud_numero": 6},
        {"nombre": "ORDENES_PRODUCCION", "prefijo": "OP-", "siguiente_numero": 1, "longitud_numero": 6},
        {"nombre": "ASIENTOS", "prefijo": "ASI-", "siguiente_numero": 1, "longitud_numero": 6},
        {"nombre": "FACTURAS", "prefijo": "FAC-", "siguiente_numero": 1, "longitud_numero": 6},
    ]

    for seq_data in secuencias:
        existing = (
            db.query(Secuencias)
            .filter(Secuencias.nombre == seq_data["nombre"], Secuencias.tenant_id == tenant_id)
            .first()
        )

        if not existing:
            secuencia = Secuencias(tenant_id=tenant_id, **seq_data)
            db.add(secuencia)
            logger.info(f"  Secuencia: {seq_data['nombre']}")

    db.commit()


# ============================================================================
# SEED: CUENTAS CONTABLES (tenant-scoped)
# ============================================================================


def seed_cuentas_contables(db: Session, tenant_id: UUID) -> Dict[str, UUID]:
    """Crea plan de cuentas PUC básico."""
    logger.info("Creando plan de cuentas PUC...")

    cuentas = [
        # ACTIVOS
        {
            "codigo": "1",
            "nombre": "ACTIVO",
            "nivel": 1,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "ACTIVO",
            "acepta_movimiento": False,
        },
        {
            "codigo": "11",
            "nombre": "DISPONIBLE",
            "nivel": 2,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "ACTIVO",
            "acepta_movimiento": False,
            "padre": "1",
        },
        {
            "codigo": "1105",
            "nombre": "CAJA",
            "nivel": 3,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "ACTIVO",
            "acepta_movimiento": True,
            "padre": "11",
        },
        {
            "codigo": "1110",
            "nombre": "BANCOS",
            "nivel": 3,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "ACTIVO",
            "acepta_movimiento": True,
            "padre": "11",
        },
        # DEUDORES
        {
            "codigo": "13",
            "nombre": "DEUDORES",
            "nivel": 2,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "ACTIVO",
            "acepta_movimiento": False,
            "padre": "1",
        },
        {
            "codigo": "1305",
            "nombre": "CLIENTES",
            "nivel": 3,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "ACTIVO",
            "acepta_movimiento": True,
            "padre": "13",
        },
        # INVENTARIOS
        {
            "codigo": "14",
            "nombre": "INVENTARIOS",
            "nivel": 2,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "ACTIVO",
            "acepta_movimiento": False,
            "padre": "1",
        },
        {
            "codigo": "1430",
            "nombre": "PRODUCTOS EN PROCESO",
            "nivel": 3,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "ACTIVO",
            "acepta_movimiento": True,
            "padre": "14",
        },
        {
            "codigo": "1435",
            "nombre": "MERCANCÍAS",
            "nivel": 3,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "ACTIVO",
            "acepta_movimiento": True,
            "padre": "14",
        },
        # PASIVOS
        {
            "codigo": "2",
            "nombre": "PASIVO",
            "nivel": 1,
            "naturaleza": "CREDITO",
            "tipo_cuenta": "PASIVO",
            "acepta_movimiento": False,
        },
        {
            "codigo": "22",
            "nombre": "PROVEEDORES",
            "nivel": 2,
            "naturaleza": "CREDITO",
            "tipo_cuenta": "PASIVO",
            "acepta_movimiento": False,
            "padre": "2",
        },
        {
            "codigo": "2205",
            "nombre": "PROVEEDORES NACIONALES",
            "nivel": 3,
            "naturaleza": "CREDITO",
            "tipo_cuenta": "PASIVO",
            "acepta_movimiento": True,
            "padre": "22",
        },
        {
            "codigo": "24",
            "nombre": "IMPUESTOS",
            "nivel": 2,
            "naturaleza": "CREDITO",
            "tipo_cuenta": "PASIVO",
            "acepta_movimiento": False,
            "padre": "2",
        },
        {
            "codigo": "2408",
            "nombre": "IVA POR PAGAR",
            "nivel": 3,
            "naturaleza": "CREDITO",
            "tipo_cuenta": "PASIVO",
            "acepta_movimiento": True,
            "padre": "24",
        },
        # PATRIMONIO
        {
            "codigo": "3",
            "nombre": "PATRIMONIO",
            "nivel": 1,
            "naturaleza": "CREDITO",
            "tipo_cuenta": "PATRIMONIO",
            "acepta_movimiento": False,
        },
        {
            "codigo": "31",
            "nombre": "CAPITAL SOCIAL",
            "nivel": 2,
            "naturaleza": "CREDITO",
            "tipo_cuenta": "PATRIMONIO",
            "acepta_movimiento": False,
            "padre": "3",
        },
        {
            "codigo": "3105",
            "nombre": "CAPITAL SUSCRITO Y PAGADO",
            "nivel": 3,
            "naturaleza": "CREDITO",
            "tipo_cuenta": "PATRIMONIO",
            "acepta_movimiento": True,
            "padre": "31",
        },
        {
            "codigo": "36",
            "nombre": "RESULTADOS DEL EJERCICIO",
            "nivel": 2,
            "naturaleza": "CREDITO",
            "tipo_cuenta": "PATRIMONIO",
            "acepta_movimiento": False,
            "padre": "3",
        },
        {
            "codigo": "3605",
            "nombre": "UTILIDAD DEL EJERCICIO",
            "nivel": 3,
            "naturaleza": "CREDITO",
            "tipo_cuenta": "PATRIMONIO",
            "acepta_movimiento": True,
            "padre": "36",
        },
        # INGRESOS
        {
            "codigo": "4",
            "nombre": "INGRESOS",
            "nivel": 1,
            "naturaleza": "CREDITO",
            "tipo_cuenta": "INGRESO",
            "acepta_movimiento": False,
        },
        {
            "codigo": "41",
            "nombre": "OPERACIONALES",
            "nivel": 2,
            "naturaleza": "CREDITO",
            "tipo_cuenta": "INGRESO",
            "acepta_movimiento": False,
            "padre": "4",
        },
        {
            "codigo": "4135",
            "nombre": "COMERCIO AL POR MAYOR Y MENOR",
            "nivel": 3,
            "naturaleza": "CREDITO",
            "tipo_cuenta": "INGRESO",
            "acepta_movimiento": True,
            "padre": "41",
        },
        # GASTOS
        {
            "codigo": "5",
            "nombre": "GASTOS",
            "nivel": 1,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "EGRESO",
            "acepta_movimiento": False,
        },
        {
            "codigo": "51",
            "nombre": "OPERACIONALES DE ADMINISTRACIÓN",
            "nivel": 2,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "EGRESO",
            "acepta_movimiento": False,
            "padre": "5",
        },
        {
            "codigo": "5105",
            "nombre": "GASTOS DE PERSONAL",
            "nivel": 3,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "EGRESO",
            "acepta_movimiento": True,
            "padre": "51",
        },
        {
            "codigo": "5195",
            "nombre": "DIVERSOS",
            "nivel": 3,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "EGRESO",
            "acepta_movimiento": True,
            "padre": "51",
        },
        # COSTOS
        {
            "codigo": "6",
            "nombre": "COSTOS DE VENTAS",
            "nivel": 1,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "COSTOS",
            "acepta_movimiento": False,
        },
        {
            "codigo": "61",
            "nombre": "COSTO DE VENTAS Y PRESTACIÓN DE SERVICIOS",
            "nivel": 2,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "COSTOS",
            "acepta_movimiento": False,
            "padre": "6",
        },
        {
            "codigo": "6135",
            "nombre": "COMERCIO AL POR MAYOR Y MENOR",
            "nivel": 3,
            "naturaleza": "DEBITO",
            "tipo_cuenta": "COSTOS",
            "acepta_movimiento": True,
            "padre": "61",
        },
    ]

    cuentas_map: Dict[str, UUID] = {}

    for cuenta_data in cuentas:
        padre_codigo = cuenta_data.pop("padre", None)
        existing = (
            db.query(CuentasContables)
            .filter(CuentasContables.codigo == cuenta_data["codigo"], CuentasContables.tenant_id == tenant_id)
            .first()
        )

        if not existing:
            cuenta_padre_id = cuentas_map.get(padre_codigo) if padre_codigo else None
            cuenta = CuentasContables(tenant_id=tenant_id, cuenta_padre_id=cuenta_padre_id, **cuenta_data)
            db.add(cuenta)
            db.flush()
            cuentas_map[cuenta_data["codigo"]] = cuenta.id
        else:
            cuentas_map[cuenta_data["codigo"]] = existing.id

    db.commit()
    logger.info(f"  {len(cuentas_map)} cuentas PUC creadas/verificadas")
    return cuentas_map


# ============================================================================
# SEED: CONFIGURACIÓN CONTABLE (tenant-scoped)
# ============================================================================


def seed_configuracion_contable(db: Session, tenant_id: UUID, cuentas_map: Dict[str, UUID]):
    """Crea configuración contable básica."""
    logger.info("Creando configuración contable...")

    configs = [
        {
            "concepto": "VENTA_CONTADO",
            "cuenta_debito_id": cuentas_map.get("1105"),
            "cuenta_credito_id": cuentas_map.get("4135"),
            "descripcion": "Venta de contado: Débito Caja, Crédito Ventas",
        },
        {
            "concepto": "VENTA_CREDITO",
            "cuenta_debito_id": cuentas_map.get("1305"),
            "cuenta_credito_id": cuentas_map.get("4135"),
            "descripcion": "Venta a crédito: Débito Clientes, Crédito Ventas",
        },
        {
            "concepto": "IVA_VENTAS",
            "cuenta_debito_id": None,
            "cuenta_credito_id": cuentas_map.get("2408"),
            "descripcion": "IVA generado en ventas",
        },
        {
            "concepto": "COSTO_VENTAS",
            "cuenta_debito_id": cuentas_map.get("6135"),
            "cuenta_credito_id": cuentas_map.get("1435"),
            "descripcion": "Costo de mercancía vendida",
        },
        {
            "concepto": "COMPRA_CONTADO",
            "cuenta_debito_id": cuentas_map.get("1435"),
            "cuenta_credito_id": cuentas_map.get("1105"),
            "descripcion": "Compra de mercancía de contado",
        },
        {
            "concepto": "PRODUCCION",
            "cuenta_debito_id": cuentas_map.get("1435"),
            "cuenta_credito_id": cuentas_map.get("1430"),
            "descripcion": "Producción: Débito Mercancías, Crédito Productos en Proceso",
        },
    ]

    for cfg in configs:
        existing = (
            db.query(ConfiguracionContable)
            .filter(ConfiguracionContable.tenant_id == tenant_id, ConfiguracionContable.concepto == cfg["concepto"])
            .first()
        )
        if not existing:
            config = ConfiguracionContable(tenant_id=tenant_id, **cfg)
            db.add(config)

    db.commit()
    logger.info("  Configuración contable creada")


# ============================================================================
# SEED: MEDIOS DE PAGO (tenant-scoped)
# ============================================================================


def seed_medios_pago(db: Session, tenant_id: UUID):
    """Crea medios de pago."""
    logger.info("Creando medios de pago...")

    medios = [
        {"nombre": "Efectivo", "tipo": "EFECTIVO", "requiere_referencia": False},
        {"nombre": "Transferencia Bancaria", "tipo": "TRANSFERENCIA", "requiere_referencia": True},
        {"nombre": "Tarjeta Débito", "tipo": "TARJETA_DEBITO", "requiere_referencia": True},
        {"nombre": "Tarjeta Crédito", "tipo": "TARJETA_CREDITO", "requiere_referencia": True},
    ]

    for medio_data in medios:
        existing = (
            db.query(MediosPago)
            .filter(MediosPago.nombre == medio_data["nombre"], MediosPago.tenant_id == tenant_id)
            .first()
        )
        if not existing:
            medio = MediosPago(tenant_id=tenant_id, estado=True, **medio_data)
            db.add(medio)

    db.commit()


# ============================================================================
# SEED: TERCEROS (tenant-scoped)
# ============================================================================


def seed_terceros(db: Session, tenant_id: UUID):
    """Crea terceros de prueba."""
    logger.info("Creando terceros...")

    terceros = [
        {
            "tipo_documento": "NIT",
            "numero_documento": "222222222222",
            "nombre": "CLIENTE MOSTRADOR",
            "tipo_tercero": "CLIENTE",
            "email": "mostrador@demo.com",
            "telefono": "0000000",
            "direccion": "N/A",
            "estado": True,
        },
        {
            "tipo_documento": "NIT",
            "numero_documento": "900123456",
            "nombre": "DISTRIBUIDORA REGIONAL S.A.S",
            "tipo_tercero": "CLIENTE",
            "email": "ventas@distribuidora.co",
            "telefono": "3001234567",
            "direccion": "Calle 100 #20-30, Bogotá",
            "estado": True,
        },
        {
            "tipo_documento": "CC",
            "numero_documento": "1234567890",
            "nombre": "MARÍA GÓMEZ",
            "tipo_tercero": "CLIENTE",
            "email": "maria@example.com",
            "telefono": "3009876543",
            "direccion": "Carrera 50 #10-20, Medellín",
            "estado": True,
        },
        {
            "tipo_documento": "NIT",
            "numero_documento": "800987654",
            "nombre": "PROVEEDORA INSUMOS LTDA",
            "tipo_tercero": "PROVEEDOR",
            "email": "ventas@proveedorainsumos.co",
            "telefono": "6017654321",
            "direccion": "Zona Industrial, Bogotá",
            "estado": True,
        },
        {
            "tipo_documento": "NIT",
            "numero_documento": "800111222",
            "nombre": "EMPAQUES DEL VALLE S.A",
            "tipo_tercero": "PROVEEDOR",
            "email": "contacto@empaquesdelvalle.com",
            "telefono": "6023334455",
            "direccion": "Calle 5 #30-40, Cali",
            "estado": True,
        },
    ]

    for tercero_data in terceros:
        existing = (
            db.query(Terceros)
            .filter(Terceros.numero_documento == tercero_data["numero_documento"], Terceros.tenant_id == tenant_id)
            .first()
        )
        if not existing:
            tercero = Terceros(tenant_id=tenant_id, **tercero_data)
            db.add(tercero)
            logger.info(f"  Tercero: {tercero_data['nombre']}")

    db.commit()


# ============================================================================
# SEED: PRODUCTOS (tenant-scoped)
# ============================================================================


def seed_productos(db: Session, tenant_id: UUID):
    """Crea productos de prueba genéricos para solopreneurs."""
    logger.info("Creando productos...")

    productos = [
        # Materias primas / Insumos
        {
            "codigo_interno": "INS-001",
            "nombre": "Materia Prima A",
            "descripcion": "Insumo principal de producción",
            "categoria": "Insumo",
            "unidad_medida": "KILOGRAMO",
            "maneja_inventario": True,
            "porcentaje_iva": Decimal("19.00"),
            "tipo_iva": "Gravado",
            "precio_venta": Decimal("18000.00"),
            "stock_minimo": Decimal("50.00"),
            "stock_maximo": Decimal("500.00"),
        },
        {
            "codigo_interno": "INS-002",
            "nombre": "Saborizante Premium",
            "descripcion": "Saborizante natural para confitería",
            "categoria": "Insumo",
            "unidad_medida": "LITRO",
            "maneja_inventario": True,
            "porcentaje_iva": Decimal("19.00"),
            "tipo_iva": "Gravado",
            "precio_venta": Decimal("45000.00"),
            "stock_minimo": Decimal("5.00"),
            "stock_maximo": Decimal("50.00"),
        },
        {
            "codigo_interno": "INS-003",
            "nombre": "Empaque Kraft 15x20",
            "descripcion": "Bolsa de empaque artesanal",
            "categoria": "Insumo",
            "unidad_medida": "UNIDAD",
            "maneja_inventario": True,
            "porcentaje_iva": Decimal("19.00"),
            "tipo_iva": "Gravado",
            "precio_venta": Decimal("2000.00"),
            "stock_minimo": Decimal("100.00"),
            "stock_maximo": Decimal("1000.00"),
        },
        {
            "codigo_interno": "INS-004",
            "nombre": "Frasco Vidrio 200ml",
            "descripcion": "Envase de vidrio para producto terminado",
            "categoria": "Insumo",
            "unidad_medida": "UNIDAD",
            "maneja_inventario": True,
            "porcentaje_iva": Decimal("19.00"),
            "tipo_iva": "Gravado",
            "precio_venta": Decimal("3500.00"),
            "stock_minimo": Decimal("50.00"),
            "stock_maximo": Decimal("500.00"),
        },
        # Productos terminados
        {
            "codigo_interno": "PROD-001",
            "nombre": "Producto Terminado A",
            "descripcion": "Producto artesanal terminado 200g",
            "categoria": "Producto_Propio",
            "unidad_medida": "UNIDAD",
            "maneja_inventario": True,
            "porcentaje_iva": Decimal("19.00"),
            "tipo_iva": "Gravado",
            "precio_venta": Decimal("35000.00"),
            "stock_minimo": Decimal("10.00"),
            "stock_maximo": Decimal("100.00"),
        },
        {
            "codigo_interno": "PROD-002",
            "nombre": "Producto Terminado B",
            "descripcion": "Producto artesanal terminado variante",
            "categoria": "Producto_Propio",
            "unidad_medida": "UNIDAD",
            "maneja_inventario": True,
            "porcentaje_iva": Decimal("19.00"),
            "tipo_iva": "Gravado",
            "precio_venta": Decimal("35000.00"),
            "stock_minimo": Decimal("10.00"),
            "stock_maximo": Decimal("100.00"),
        },
        # Producto tercero
        {
            "codigo_interno": "TERC-001",
            "nombre": "Candelabro Decorativo Dorado",
            "descripcion": "Candelabro decorativo importado para reventa",
            "categoria": "Producto_Tercero",
            "unidad_medida": "UNIDAD",
            "maneja_inventario": True,
            "porcentaje_iva": Decimal("19.00"),
            "tipo_iva": "Gravado",
            "precio_venta": Decimal("85000.00"),
            "stock_minimo": Decimal("5.00"),
            "stock_maximo": Decimal("30.00"),
        },
    ]

    for producto_data in productos:
        existing = (
            db.query(Productos)
            .filter(Productos.codigo_interno == producto_data["codigo_interno"], Productos.tenant_id == tenant_id)
            .first()
        )
        if not existing:
            producto = Productos(tenant_id=tenant_id, estado=True, **producto_data)
            db.add(producto)
            logger.info(f"  Producto: {producto_data['nombre']}")

    db.commit()


# ============================================================================
# SEED: INVENTARIOS INICIALES (tenant-scoped)
# ============================================================================


def seed_inventarios_iniciales(db: Session, tenant_id: UUID):
    """Crea inventarios iniciales."""
    logger.info("Creando inventarios iniciales...")

    inventarios_data = [
        {"codigo_producto": "INS-001", "cantidad": Decimal("200.00"), "costo": Decimal("12000.00")},
        {"codigo_producto": "INS-002", "cantidad": Decimal("20.00"), "costo": Decimal("35000.00")},
        {"codigo_producto": "INS-003", "cantidad": Decimal("500.00"), "costo": Decimal("1200.00")},
        {"codigo_producto": "INS-004", "cantidad": Decimal("200.00"), "costo": Decimal("2500.00")},
        {"codigo_producto": "PROD-001", "cantidad": Decimal("30.00"), "costo": Decimal("14500.00")},
        {"codigo_producto": "PROD-002", "cantidad": Decimal("25.00"), "costo": Decimal("14800.00")},
        {"codigo_producto": "TERC-001", "cantidad": Decimal("10.00"), "costo": Decimal("50000.00")},
    ]

    for inv_data in inventarios_data:
        producto = (
            db.query(Productos)
            .filter(Productos.codigo_interno == inv_data["codigo_producto"], Productos.tenant_id == tenant_id)
            .first()
        )

        if not producto:
            continue

        existing = (
            db.query(Inventarios)
            .filter(Inventarios.producto_id == producto.id, Inventarios.tenant_id == tenant_id)
            .first()
        )

        if not existing:
            valor_total = inv_data["cantidad"] * inv_data["costo"]
            inventario = Inventarios(
                tenant_id=tenant_id,
                producto_id=producto.id,
                cantidad_disponible=inv_data["cantidad"],
                costo_promedio_ponderado=inv_data["costo"],
                valor_total=valor_total,
            )
            db.add(inventario)
            logger.info(f"  Inventario: {producto.nombre} - {inv_data['cantidad']} uds @ ${inv_data['costo']}")

    db.commit()


# ============================================================================
# SEED: CRM DEFAULTS
# ============================================================================


def seed_crm_defaults():
    """Crea pipeline default 'Ventas General' con 5 etapas estándar para todos los tenants activos."""
    from ..datos.modelos_crm import CrmPipeline, CrmStage

    db = SessionLocal()
    logger.info("=" * 60)
    logger.info("SEED CRM: Creando pipelines y stages default...")
    logger.info("=" * 60)

    try:
        # Obtener todos los tenants activos
        tenants = db.query(Tenants).filter(Tenants.estado.in_(["activo", "trial"])).all()

        for tenant in tenants:
            # Verificar si ya tiene pipeline default
            existing = (
                db.query(CrmPipeline)
                .filter(CrmPipeline.tenant_id == tenant.id, CrmPipeline.es_default.is_(True))
                .first()
            )

            if existing:
                logger.info(f"  Tenant '{tenant.nombre}' ya tiene pipeline default. Skipping.")
                continue

            # Crear pipeline default
            pipeline = CrmPipeline(
                tenant_id=tenant.id,
                nombre="Ventas General",
                descripcion="Pipeline por defecto para gestión de oportunidades de venta",
                es_default=True,
                color="#3B82F6",
            )
            db.add(pipeline)
            db.flush()  # Para obtener el ID del pipeline

            # Crear 5 stages estándar
            stages_data = [
                {"nombre": "Lead", "orden": 1, "probabilidad": 10},
                {"nombre": "Calificado", "orden": 2, "probabilidad": 25},
                {"nombre": "Propuesta", "orden": 3, "probabilidad": 50},
                {"nombre": "Negociación", "orden": 4, "probabilidad": 75},
                {"nombre": "Ganado", "orden": 5, "probabilidad": 100},
            ]

            for stage_data in stages_data:
                stage = CrmStage(
                    tenant_id=tenant.id,
                    pipeline_id=pipeline.id,
                    nombre=stage_data["nombre"],
                    orden=stage_data["orden"],
                    probabilidad=stage_data["probabilidad"],
                )
                db.add(stage)

            logger.info(f"  ✓ Pipeline 'Ventas General' creado para '{tenant.nombre}' con 5 etapas")

        db.commit()
        logger.info("=" * 60)
        logger.info("SEED CRM COMPLETADO")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error ejecutando seed CRM: {str(e)}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================


def run_all_seeders():
    """Ejecuta todos los seeders en orden."""
    db = SessionLocal()

    try:
        logger.info("=" * 60)
        logger.info("INICIANDO SEEDERS")
        logger.info("=" * 60)

        # 1. Planes (global)
        plan_id = seed_planes(db)

        # 2. Superadmin + Tenant demo
        tenant_id, admin_id = seed_superadmin_and_tenant(db, plan_id)

        # 3. Secuencias (tenant-scoped)
        seed_secuencias(db, tenant_id)

        # 4. Cuentas contables PUC (tenant-scoped)
        cuentas_map = seed_cuentas_contables(db, tenant_id)

        # 5. Configuración contable (tenant-scoped)
        seed_configuracion_contable(db, tenant_id, cuentas_map)

        # 6. Medios de pago (tenant-scoped)
        seed_medios_pago(db, tenant_id)

        # 7. Terceros (tenant-scoped)
        seed_terceros(db, tenant_id)

        # 8. Productos (tenant-scoped)
        seed_productos(db, tenant_id)

        # 9. Inventarios iniciales (tenant-scoped)
        seed_inventarios_iniciales(db, tenant_id)

        logger.info("=" * 60)
        logger.info("SEEDERS COMPLETADOS EXITOSAMENTE")
        logger.info("=" * 60)
        logger.info("")
        logger.info("CREDENCIALES DE ACCESO:")
        logger.info(f"  Tenant ID: {tenant_id}")
        logger.info("  Superadmin:  superadmin@chandelier.com / superadmin123")
        logger.info("  Admin:       admin@example.com / admin123")
        logger.info("  Operador:    operador@emprendedora.co / operador123")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error ejecutando seeders: {str(e)}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_all_seeders()
