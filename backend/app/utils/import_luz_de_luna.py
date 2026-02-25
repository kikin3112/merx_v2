"""
Script de importación para tenant Luz De Luna.
Parsea el CSV de productos y los importa al sistema.
"""

import csv
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.datos.db import SessionLocal
from app.datos.modelos import Inventarios, Productos, Secuencias, Terceros, Usuarios
from app.datos.modelos_tenant import Planes, Suscripciones, Tenants, UsuariosTenants
from app.utils.logger import setup_logger
from app.utils.seguridad import hash_password
from sqlalchemy.orm import Session

logger = setup_logger(__name__)


# ============================================================================
# CONFIGURACIÓN DEL TENANT
# ============================================================================

TENANT_DATA = {
    "nombre": "Luz De Luna",
    "slug": "luz-de-luna",
    "nit": None,  # No tiene NIT
    "email_contacto": "luzdelunavelas30@gmail.com",
    "telefono": "3194079056",
    "direccion": "N/A",
    "ciudad": None,
    "departamento": None,
}

ADMIN_DATA = {
    "nombre": "Admin Luz De Luna",
    "email": "luzdelunavelas30@gmail.com",
    "password": "luzdeluna2024",  # Usuario puede cambiar después
}


# ============================================================================
# MAPEO DE CATEGORÍAS CSV -> SISTEMA
# ============================================================================

CATEGORY_MAP = {
    "ESENCIAS": "Insumo",
    "CERAS": "Insumo",
    "PABILOS": "Insumo",
    "EMVASES": "Insumo",
    # Sin categoría (colorantes, químicos) -> Insumo
    None: "Insumo",
    "": "Insumo",
}

# Prefijos para SKUs únicos por tipo
SKU_PREFIXES = {
    "ESENCIAS": "ESEN",
    "CERAS": "CERA",
    "PABILOS": "PABI",
    "EMVASES": "ENVS",
    None: "INS",  # Default para insumos sin categoría
    "": "INS",
}


# ============================================================================
# FUNCIONES DE PARSEO
# ============================================================================


def parse_price(value: str) -> Decimal:
    """Parsea precios del formato '$ X.XXX' o número plano."""
    if not value or not value.strip():
        return Decimal("0.00")

    # Remover símbolos de moneda y espacios
    cleaned = value.replace("$", "").replace(".", "").replace(",", "").strip()

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        logger.warning(f"No se pudo parsear precio: '{value}'")
        return Decimal("0.00")


def parse_stock(value: str) -> Decimal:
    """Parsea cantidad de stock."""
    if not value or not value.strip():
        return Decimal("0.00")

    try:
        return Decimal(value.strip())
    except InvalidOperation:
        return Decimal("0.00")


def clean_product_name(name: str) -> str:
    """Limpia y normaliza el nombre del producto."""
    if not name:
        return "Producto sin nombre"

    # Corregir caracteres especiales comunes
    name = name.replace("�", "Ñ")  # Encoding issue
    name = name.replace("ã", "Ñ")
    name = name.replace("�", "Í")

    # Limpiar espacios múltiples
    name = " ".join(name.split())

    # Capitalizar correctamente
    return name.strip().upper()


def extract_category(row: dict) -> str:
    """Extrae la categoría del CSV."""
    cat = row.get("Categoría", "").strip()
    if not cat:
        # Intentar con minúsculas por encoding
        for key in row.keys():
            if "categor" in key.lower():
                cat = row.get(key, "").strip()
                break
    return cat if cat else ""


def parse_csv(filepath: str) -> list[dict]:
    """Parsea el archivo CSV con encoding correcto."""
    products = []

    # Intentar diferentes encodings
    encodings = ["latin-1", "cp1252", "iso-8859-1", "utf-8"]

    for encoding in encodings:
        try:
            with open(filepath, "r", encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=";")

                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Extraer campos (manejar diferentes nombres de columna por encoding)
                        codigo = row.get("Código", row.get("Codigo", "")).strip()
                        nombre = row.get("Producto", "").strip()
                        categoria = extract_category(row)

                        # Precio costo
                        costo_key = None
                        for key in row.keys():
                            if "costo" in key.lower():
                                costo_key = key
                                break
                        costo = parse_price(row.get(costo_key, "0") if costo_key else "0")

                        # Precio venta
                        venta_key = None
                        for key in row.keys():
                            if "precio" in key.lower() and "venta" in key.lower():
                                venta_key = key
                                break
                        if not venta_key:
                            for key in row.keys():
                                if "venta" in key.lower():
                                    venta_key = key
                                    break
                        precio_venta = parse_price(row.get(venta_key, "0") if venta_key else "0")

                        # Stock
                        stock_key = None
                        for key in row.keys():
                            if "stock" in key.lower():
                                stock_key = key
                                break
                        stock = parse_stock(row.get(stock_key, "") if stock_key else "")

                        # Skip filas vacías o sin nombre
                        if not nombre:
                            continue

                        # Skip duplicados (mismo código + nombre)
                        if codigo and nombre:
                            products.append(
                                {
                                    "codigo_original": codigo,
                                    "nombre": clean_product_name(nombre),
                                    "categoria_raw": categoria,
                                    "costo": costo,
                                    "precio_venta": precio_venta,
                                    "stock": stock,
                                    "fila": row_num,
                                }
                            )

                    except Exception as e:
                        logger.warning(f"Error en fila {row_num}: {e}")
                        continue

                logger.info(f"CSV parseado con encoding {encoding}: {len(products)} productos")
                return products

        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.error(f"Error leyendo CSV: {e}")
            continue

    raise ValueError("No se pudo leer el archivo CSV con ningún encoding")


def generate_unique_skus(products: list[dict]) -> list[dict]:
    """Genera SKUs únicos para cada producto."""
    counters = {}
    result = []
    seen_skus = set()

    for p in products:
        cat = p["categoria_raw"] or ""
        prefix = SKU_PREFIXES.get(cat, "INS")

        # Inicializar contador si no existe
        if prefix not in counters:
            counters[prefix] = 1

        # Generar SKU único
        sku = f"{prefix}-{counters[prefix]:04d}"
        while sku in seen_skus:
            counters[prefix] += 1
            sku = f"{prefix}-{counters[prefix]:04d}"

        seen_skus.add(sku)
        counters[prefix] += 1

        p["sku"] = sku
        p["categoria"] = CATEGORY_MAP.get(cat, "Insumo")
        result.append(p)

    return result


# ============================================================================
# FUNCIONES DE BASE DE DATOS
# ============================================================================


def get_or_create_tenant(db: Session) -> tuple:
    """Crea o retorna el tenant Luz De Luna."""
    logger.info("Verificando/creando tenant Luz De Luna...")

    # Buscar tenant existente
    tenant = db.query(Tenants).filter(Tenants.slug == TENANT_DATA["slug"]).first()

    if tenant:
        logger.info(f"Tenant ya existe: {tenant.nombre} (ID: {tenant.id})")

        # Buscar admin existente
        admin = db.query(Usuarios).filter(Usuarios.email == ADMIN_DATA["email"]).first()

        return tenant.id, admin.id if admin else None

    # Obtener plan default
    plan = db.query(Planes).filter(Planes.es_default).first()
    if not plan:
        plan = db.query(Planes).first()

    if not plan:
        raise ValueError("No hay planes en la base de datos")

    # Crear tenant
    tenant = Tenants(
        nombre=TENANT_DATA["nombre"],
        slug=TENANT_DATA["slug"],
        nit=TENANT_DATA["nit"],
        email_contacto=TENANT_DATA["email_contacto"],
        telefono=TENANT_DATA["telefono"],
        direccion=TENANT_DATA["direccion"],
        ciudad=TENANT_DATA["ciudad"],
        departamento=TENANT_DATA["departamento"],
        plan_id=plan.id,
        estado="activo",
        fecha_inicio_suscripcion=datetime.now(timezone.utc),
        fecha_fin_suscripcion=datetime.now(timezone.utc) + timedelta(days=365),
    )
    db.add(tenant)
    db.flush()
    logger.info(f"Tenant creado: {tenant.nombre} (ID: {tenant.id})")

    # Crear usuario admin
    admin = Usuarios(
        nombre=ADMIN_DATA["nombre"],
        email=ADMIN_DATA["email"],
        password_hash=hash_password(ADMIN_DATA["password"]),
        rol="admin",
        estado=True,
        es_superadmin=False,
    )
    db.add(admin)
    db.flush()
    logger.info(f"Usuario admin creado: {admin.email}")

    # Relacionar admin con tenant
    rel = UsuariosTenants(
        usuario_id=admin.id,
        tenant_id=tenant.id,
        rol="admin",
        esta_activo=True,
        es_default=True,
    )
    db.add(rel)

    # Crear suscripción
    sub = Suscripciones(
        tenant_id=tenant.id,
        plan_id=plan.id,
        periodo_inicio=datetime.now(timezone.utc),
        periodo_fin=datetime.now(timezone.utc) + timedelta(days=365),
        estado="activo",
    )
    db.add(sub)

    # Crear cliente mostrador
    cliente_mostrador = Terceros(
        tenant_id=tenant.id,
        tipo_documento="NIT",
        numero_documento="222222222222",
        nombre="CLIENTE MOSTRADOR",
        tipo_tercero="CLIENTE",
        email="mostrador@luzdeluna.com",
        estado=True,
    )
    db.add(cliente_mostrador)

    # Crear secuencias
    secuencias = [
        {"nombre": "COMPRAS", "prefijo": "CMP-", "siguiente_numero": 1, "longitud_numero": 6},
        {"nombre": "COTIZACIONES", "prefijo": "COT-", "siguiente_numero": 1, "longitud_numero": 6},
        {"nombre": "ORDENES_PRODUCCION", "prefijo": "OP-", "siguiente_numero": 1, "longitud_numero": 6},
        {"nombre": "ASIENTOS", "prefijo": "ASI-", "siguiente_numero": 1, "longitud_numero": 6},
        {"nombre": "FACTURAS", "prefijo": "FAC-", "siguiente_numero": 1, "longitud_numero": 6},
    ]

    for seq_data in secuencias:
        seq = Secuencias(tenant_id=tenant.id, **seq_data)
        db.add(seq)

    db.commit()
    logger.info("Tenant, admin y configuración base creados")

    return tenant.id, admin.id


def import_products(db: Session, tenant_id, products: list[dict]) -> int:
    """Importa los productos al sistema."""
    logger.info(f"Importando {len(products)} productos...")

    imported = 0
    skipped = 0

    for p in products:
        try:
            # Verificar si ya existe por SKU
            existing = (
                db.query(Productos)
                .filter(
                    Productos.codigo_interno == p["sku"],
                    Productos.tenant_id == tenant_id,
                )
                .first()
            )

            if existing:
                logger.debug(f"Producto ya existe: {p['sku']} - {p['nombre']}")
                skipped += 1
                continue

            # Crear producto
            producto = Productos(
                tenant_id=tenant_id,
                codigo_interno=p["sku"],
                nombre=p["nombre"],
                descripcion=f"Importado desde CSV (código original: {p['codigo_original']})",
                categoria=p["categoria"],
                unidad_medida="UNIDAD",
                maneja_inventario=True,
                porcentaje_iva=Decimal("0.00"),  # Tenant configura después
                tipo_iva="Excluido",
                precio_venta=p["precio_venta"],
                estado=True,
            )
            db.add(producto)
            db.flush()

            # Crear inventario inicial si hay stock
            if p["stock"] > 0:
                inventario = Inventarios(
                    tenant_id=tenant_id,
                    producto_id=producto.id,
                    cantidad_disponible=p["stock"],
                    costo_promedio_ponderado=p["costo"] if p["costo"] > 0 else Decimal("0.00"),
                    valor_total=p["stock"] * (p["costo"] if p["costo"] > 0 else Decimal("0.00")),
                )
                db.add(inventario)

            imported += 1

            if imported % 20 == 0:
                logger.info(f"  Progreso: {imported}/{len(products)} productos")

        except Exception as e:
            logger.error(f"Error importando {p['sku']}: {e}")
            continue

    db.commit()
    logger.info(f"Importación completada: {imported} productos importados, {skipped} omitidos")

    return imported


# ============================================================================
# MAIN
# ============================================================================


def run_import(csv_path: str = None):
    """Ejecuta la importación completa."""
    if csv_path is None:
        csv_path = Path(__file__).parent.parent.parent.parent.parent / "luz_de_luna_products_seed.csv"

    logger.info("=" * 60)
    logger.info("INICIANDO IMPORTACIÓN LUZ DE LUNA")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        # 1. Parsear CSV
        logger.info(f"Leyendo archivo: {csv_path}")
        raw_products = parse_csv(str(csv_path))

        # 2. Generar SKUs únicos
        products = generate_unique_skus(raw_products)
        logger.info(f"Productos normalizados: {len(products)}")

        # 3. Crear/verificar tenant
        tenant_id, admin_id = get_or_create_tenant(db)

        # 4. Importar productos
        imported = import_products(db, tenant_id, products)

        # 5. Resumen
        logger.info("=" * 60)
        logger.info("IMPORTACIÓN COMPLETADA")
        logger.info("=" * 60)
        logger.info(f"Tenant ID: {tenant_id}")
        logger.info(f"Productos importados: {imported}")
        logger.info(f"Admin: {ADMIN_DATA['email']} / {ADMIN_DATA['password']}")
        logger.info("=" * 60)

        # Mostrar algunos productos de ejemplo
        logger.info("\nMuestra de productos importados:")
        sample = db.query(Productos).filter(Productos.tenant_id == tenant_id).limit(10).all()

        for p in sample:
            inv = db.query(Inventarios).filter(Inventarios.producto_id == p.id).first()
            stock_str = f"Stock: {inv.cantidad_disponible}" if inv else "Sin inventario"
            logger.info(f"  {p.codigo_interno} | {p.nombre[:40]:<40} | ${p.precio_venta:,.0f} | {stock_str}")

        return {
            "tenant_id": str(tenant_id),
            "admin_email": ADMIN_DATA["email"],
            "admin_password": ADMIN_DATA["password"],
            "products_imported": imported,
        }

    except Exception as e:
        logger.error(f"Error en importación: {e}", exc_info=True)
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    import sys

    csv_arg = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_import(csv_arg)
    print(f"\n✓ Importación exitosa: {result['products_imported']} productos")
