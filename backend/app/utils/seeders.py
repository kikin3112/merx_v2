"""
Seeders: Datos iniciales para desarrollo y testing.
Ejecutar con: python -m app.utils.seeders
"""

from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Dict

from ..datos.db import SessionLocal
from ..datos.modelos import (
    Usuarios, Terceros, Productos, CuentasContables,
    MediosPago, ConfiguracionContable, Inventarios, Secuencias
)
from ..utils.seguridad import hash_password
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


# ============================================================================
# SEED: SECUENCIAS
# ============================================================================

def seed_secuencias(db: Session):
    """Crea secuencias para numeración automática"""
    logger.info("Creando secuencias...")

    secuencias = [
        {"nombre": "VENTAS", "prefijo": "VEN-", "siguiente_numero": 1, "longitud_numero": 6},
        {"nombre": "COMPRAS", "prefijo": "CMP-", "siguiente_numero": 1, "longitud_numero": 6},
        {"nombre": "COTIZACIONES", "prefijo": "COT-", "siguiente_numero": 1, "longitud_numero": 6},
        {"nombre": "ORDENES_PRODUCCION", "prefijo": "OP-", "siguiente_numero": 1, "longitud_numero": 6},
        {"nombre": "ASIENTOS", "prefijo": "ASI-", "siguiente_numero": 1, "longitud_numero": 6},
    ]

    for seq_data in secuencias:
        existing = db.query(Secuencias).filter(
            Secuencias.nombre == seq_data["nombre"]
        ).first()

        if not existing:
            secuencia = Secuencias(**seq_data)
            db.add(secuencia)
            logger.info(f"✓ Secuencia creada: {seq_data['nombre']}")

    db.commit()


# ============================================================================
# SEED: USUARIOS
# ============================================================================

def seed_usuarios(db: Session):
    """Crea usuarios de prueba"""
    logger.info("Creando usuarios...")

    usuarios = [
        # Admin
        {"email": "admin@merx.com", "nombre": "Administrador Sistema",
         "password_hash": hash_password("admin123"), "rol": "admin", "estado": True},

        # Operadores
        {"email": "operador@merx.com", "nombre": "Operador Ventas",
         "password_hash": hash_password("operador123"), "rol": "operador", "estado": True},
        {"email": "vendedor@merx.com", "nombre": "Laura Martínez",
         "password_hash": hash_password("vendedor123"), "rol": "operador", "estado": True},

        # Contadores
        {"email": "contador@merx.com", "nombre": "Contador General",
         "password_hash": hash_password("contador123"), "rol": "contador", "estado": True},
    ]

    for user_data in usuarios:
        existing = db.query(Usuarios).filter(
            Usuarios.email == user_data["email"]
        ).first()

        if not existing:
            user = Usuarios(**user_data)
            db.add(user)
            # Extraer password simple del email para logging
            pwd = user_data["email"].split("@")[0] + "123"
            logger.info(f"✓ Usuario: {user_data['email']} / {pwd}")

    db.commit()


# ============================================================================
# SEED: CUENTAS CONTABLES
# ============================================================================

def seed_cuentas_contables(db: Session) -> Dict[str, str]:
    """Crea plan de cuentas PUC básico"""
    logger.info("Creando plan de cuentas...")

    cuentas = [
        # ACTIVOS
        {"codigo": "1", "nombre": "ACTIVO", "nivel": 1, "naturaleza": "DEBITO",
         "tipo_cuenta": "ACTIVO", "acepta_movimiento": False},
        {"codigo": "11", "nombre": "DISPONIBLE", "nivel": 2, "naturaleza": "DEBITO",
         "tipo_cuenta": "ACTIVO", "acepta_movimiento": False, "padre": "1"},
        {"codigo": "1105", "nombre": "CAJA", "nivel": 3, "naturaleza": "DEBITO",
         "tipo_cuenta": "ACTIVO", "acepta_movimiento": True, "padre": "11"},
        {"codigo": "1110", "nombre": "BANCOS", "nivel": 3, "naturaleza": "DEBITO",
         "tipo_cuenta": "ACTIVO", "acepta_movimiento": True, "padre": "11"},

        # DEUDORES
        {"codigo": "13", "nombre": "DEUDORES", "nivel": 2, "naturaleza": "DEBITO",
         "tipo_cuenta": "ACTIVO", "acepta_movimiento": False, "padre": "1"},
        {"codigo": "1305", "nombre": "CLIENTES", "nivel": 3, "naturaleza": "DEBITO",
         "tipo_cuenta": "ACTIVO", "acepta_movimiento": True, "padre": "13"},

        # INVENTARIOS
        {"codigo": "14", "nombre": "INVENTARIOS", "nivel": 2, "naturaleza": "DEBITO",
         "tipo_cuenta": "ACTIVO", "acepta_movimiento": False, "padre": "1"},
        {"codigo": "1435", "nombre": "MERCANCÍAS", "nivel": 3, "naturaleza": "DEBITO",
         "tipo_cuenta": "ACTIVO", "acepta_movimiento": True, "padre": "14"},

        # PASIVOS
        {"codigo": "2", "nombre": "PASIVO", "nivel": 1, "naturaleza": "CREDITO",
         "tipo_cuenta": "PASIVO", "acepta_movimiento": False},
        {"codigo": "22", "nombre": "PROVEEDORES", "nivel": 2, "naturaleza": "CREDITO",
         "tipo_cuenta": "PASIVO", "acepta_movimiento": False, "padre": "2"},
        {"codigo": "2205", "nombre": "PROVEEDORES NACIONALES", "nivel": 3,
         "naturaleza": "CREDITO", "tipo_cuenta": "PASIVO", "acepta_movimiento": True, "padre": "22"},

        # IVA
        {"codigo": "2408", "nombre": "IVA POR PAGAR", "nivel": 3, "naturaleza": "CREDITO",
         "tipo_cuenta": "PASIVO", "acepta_movimiento": True, "padre": "2"},

        # PATRIMONIO
        {"codigo": "3", "nombre": "PATRIMONIO", "nivel": 1, "naturaleza": "CREDITO",
         "tipo_cuenta": "PATRIMONIO", "acepta_movimiento": False},
        {"codigo": "3105", "nombre": "CAPITAL", "nivel": 3, "naturaleza": "CREDITO",
         "tipo_cuenta": "PATRIMONIO", "acepta_movimiento": True, "padre": "3"},

        # INGRESOS
        {"codigo": "4", "nombre": "INGRESOS", "nivel": 1, "naturaleza": "CREDITO",
         "tipo_cuenta": "INGRESO", "acepta_movimiento": False},
        {"codigo": "4135", "nombre": "VENTAS", "nivel": 3, "naturaleza": "CREDITO",
         "tipo_cuenta": "INGRESO", "acepta_movimiento": True, "padre": "4"},

        # COSTOS
        {"codigo": "6", "nombre": "COSTOS", "nivel": 1, "naturaleza": "DEBITO",
         "tipo_cuenta": "COSTOS", "acepta_movimiento": False},
        {"codigo": "6135", "nombre": "COSTO DE VENTAS", "nivel": 3, "naturaleza": "DEBITO",
         "tipo_cuenta": "COSTOS", "acepta_movimiento": True, "padre": "6"},
    ]

    cuentas_map = {}

    for cuenta_data in cuentas:
        existing = db.query(CuentasContables).filter(
            CuentasContables.codigo == cuenta_data["codigo"]
        ).first()

        if not existing:
            padre_codigo = cuenta_data.pop("padre", None)
            cuenta_padre_id = cuentas_map.get(padre_codigo) if padre_codigo else None

            cuenta = CuentasContables(**cuenta_data, cuenta_padre_id=cuenta_padre_id)
            db.add(cuenta)
            db.flush()
            cuentas_map[cuenta_data["codigo"]] = cuenta.id
            logger.info(f"✓ Cuenta: {cuenta_data['codigo']} - {cuenta_data['nombre']}")

    db.commit()
    return cuentas_map


# ============================================================================
# SEED: CONFIGURACIÓN CONTABLE
# ============================================================================

def seed_configuracion_contable(db: Session, cuentas_map: Dict[str, str]):
    """Crea configuración contable básica"""
    logger.info("Creando configuración contable...")

    existing = db.query(ConfiguracionContable).first()
    if existing:
        logger.info("⚠ Configuración ya existe")
        return

    def get_cuenta_id(codigo: str):
        cuenta = db.query(CuentasContables).filter(
            CuentasContables.codigo == codigo
        ).first()
        if not cuenta:
            raise ValueError(f"Cuenta {codigo} no encontrada")
        return cuenta.id

    config = ConfiguracionContable(
        concepto="DEFAULT",
        cuenta_debito_id=get_cuenta_id("1105"),
        cuenta_credito_id=get_cuenta_id("4135"),
        descripcion="Configuración contable por defecto"
    )

    db.add(config)
    db.commit()
    logger.info("✓ Configuración contable creada")


# ============================================================================
# SEED: MEDIOS DE PAGO
# ============================================================================

def seed_medios_pago(db: Session):
    """Crea medios de pago"""
    logger.info("Creando medios de pago...")

    medios = [
        {"nombre": "Efectivo", "tipo": "EFECTIVO", "requiere_referencia": False},
        {"nombre": "Transferencia", "tipo": "TRANSFERENCIA", "requiere_referencia": True},
        {"nombre": "Tarjeta Débito", "tipo": "TARJETA_DEBITO", "requiere_referencia": True},
        {"nombre": "Tarjeta Crédito", "tipo": "TARJETA_CREDITO", "requiere_referencia": True},
    ]

    for medio_data in medios:
        existing = db.query(MediosPago).filter(
            MediosPago.nombre == medio_data["nombre"]
        ).first()

        if not existing:
            medio = MediosPago(**medio_data, estado=True)
            db.add(medio)
            logger.info(f"✓ Medio de pago: {medio_data['nombre']}")

    db.commit()


# ============================================================================
# SEED: TERCEROS
# ============================================================================

def seed_terceros(db: Session):
    """Crea terceros de prueba"""
    logger.info("Creando terceros...")

    terceros = [
        # Clientes
        {"tipo_documento": "NIT", "numero_documento": "900123456",
         "nombre": "CLIENTE EJEMPLO S.A.S", "tipo_tercero": "CLIENTE",
         "email": "cliente@example.com", "telefono": "3001234567",
         "direccion": "Calle 100 #20-30", "estado": True},

        {"tipo_documento": "CC", "numero_documento": "1234567890",
         "nombre": "JUAN PÉREZ", "tipo_tercero": "CLIENTE",
         "email": "juan@example.com", "telefono": "3009876543",
         "direccion": "Carrera 50 #10-20", "estado": True},

        # Proveedores
        {"tipo_documento": "NIT", "numero_documento": "800987654",
         "nombre": "PROVEEDOR EJEMPLO LTDA", "tipo_tercero": "PROVEEDOR",
         "email": "proveedor@example.com", "telefono": "6017654321",
         "direccion": "Zona Industrial", "estado": True},
    ]

    for tercero_data in terceros:
        existing = db.query(Terceros).filter(
            Terceros.numero_documento == tercero_data["numero_documento"]
        ).first()

        if not existing:
            tercero = Terceros(**tercero_data)
            db.add(tercero)
            logger.info(f"✓ Tercero: {tercero_data['nombre']}")

    db.commit()


# ============================================================================
# SEED: PRODUCTOS
# ============================================================================

def seed_productos(db: Session):
    """Crea productos de prueba"""
    logger.info("Creando productos...")

    productos = [
        # Insumos
        {"codigo_interno": "INS-001", "codigo_barras": "7701234567890",
         "nombre": "Parafina Premium", "descripcion": "Parafina de alta calidad",
         "categoria": "Insumo", "unidad_medida": "KILOGRAMO",
         "maneja_inventario": True, "porcentaje_iva": Decimal("19.00"),
         "tipo_iva": "Gravado", "precio_venta": Decimal("15000.00"),
         "stock_minimo": Decimal("100.00"), "stock_maximo": Decimal("500.00")},

        # Productos Propios
        {"codigo_interno": "PROD-001", "codigo_barras": "7701234567891",
         "nombre": "Vela Aromática Lavanda", "descripcion": "Vela aromática 200g",
         "categoria": "Producto_Propio", "unidad_medida": "UNIDAD",
         "maneja_inventario": True, "porcentaje_iva": Decimal("19.00"),
         "tipo_iva": "Gravado", "precio_venta": Decimal("25000.00"),
         "stock_minimo": Decimal("20.00"), "stock_maximo": Decimal("100.00")},

        # Productos de Terceros
        {"codigo_interno": "TERC-001", "codigo_barras": "7709876543210",
         "nombre": "Candelabro Decorativo", "descripcion": "Para reventa",
         "categoria": "Producto_Tercero", "unidad_medida": "UNIDAD",
         "maneja_inventario": True, "porcentaje_iva": Decimal("19.00"),
         "tipo_iva": "Gravado", "precio_venta": Decimal("85000.00"),
         "stock_minimo": Decimal("5.00"), "stock_maximo": Decimal("30.00")},
    ]

    for producto_data in productos:
        existing = db.query(Productos).filter(
            Productos.codigo_interno == producto_data["codigo_interno"]
        ).first()

        if not existing:
            producto = Productos(**producto_data, estado=True)
            db.add(producto)
            logger.info(f"✓ Producto: {producto_data['nombre']}")

    db.commit()


# ============================================================================
# SEED: INVENTARIOS
# ============================================================================

def seed_inventarios_iniciales(db: Session):
    """Crea inventarios iniciales"""
    logger.info("Creando inventarios iniciales...")

    inventarios_data = [
        {"codigo_producto": "INS-001", "cantidad": Decimal("250.00"), "costo": Decimal("8500.00")},
        {"codigo_producto": "PROD-001", "cantidad": Decimal("50.00"), "costo": Decimal("12000.00")},
        {"codigo_producto": "TERC-001", "cantidad": Decimal("15.00"), "costo": Decimal("50000.00")},
    ]

    for inv_data in inventarios_data:
        producto = db.query(Productos).filter(
            Productos.codigo_interno == inv_data["codigo_producto"]
        ).first()

        if not producto:
            continue

        existing = db.query(Inventarios).filter(
            Inventarios.producto_id == producto.id
        ).first()

        if not existing:
            valor_total = inv_data["cantidad"] * inv_data["costo"]
            inventario = Inventarios(
                producto_id=producto.id,
                cantidad_disponible=inv_data["cantidad"],
                costo_promedio_ponderado=inv_data["costo"],
                valor_total=valor_total
            )
            db.add(inventario)
            logger.info(f"✓ Inventario: {producto.nombre} - {inv_data['cantidad']} unidades")

    db.commit()


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def run_all_seeders():
    """Ejecuta todos los seeders en orden"""
    db = SessionLocal()

    try:
        logger.info("=" * 60)
        logger.info("🌱 INICIANDO SEEDERS")
        logger.info("=" * 60)

        seed_secuencias(db)
        seed_usuarios(db)
        cuentas_map = seed_cuentas_contables(db)
        seed_configuracion_contable(db, cuentas_map)
        seed_medios_pago(db)
        seed_terceros(db)
        seed_productos(db)
        seed_inventarios_iniciales(db)

        logger.info("=" * 60)
        logger.info("✅ SEEDERS COMPLETADOS EXITOSAMENTE")
        logger.info("=" * 60)
        logger.info("")
        logger.info("📋 CREDENCIALES DE ACCESO:")
        logger.info("  👤 Admin:     admin@merx.com / admin123")
        logger.info("  👤 Operador:  operador@merx.com / operador123")
        logger.info("  👤 Contador:  contador@merx.com / contador123")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Error ejecutando seeders: {str(e)}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_all_seeders()