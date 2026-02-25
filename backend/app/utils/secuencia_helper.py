from uuid import UUID

from sqlalchemy.orm import Session

from ..datos.modelos import Secuencias


def generar_numero_secuencia(db: Session, nombre_secuencia: str, tenant_id: UUID) -> str:
    """
    Genera el siguiente número de una secuencia filtrada por tenant.

    Args:
        db: Sesión de base de datos activa
        nombre_secuencia: Nombre de la secuencia (ej: 'VENTAS', 'COMPRAS', 'OP')
        tenant_id: UUID del tenant

    Returns:
        String formateado (ej: 'VEN-000001', 'CMP-000042', 'OP-000015')

    Raises:
        ValueError: Si la secuencia no existe
    """
    # Obtener secuencia con lock FOR UPDATE (evita race conditions)
    secuencia = (
        db.query(Secuencias)
        .filter(Secuencias.tenant_id == tenant_id, Secuencias.nombre == nombre_secuencia)
        .with_for_update()
        .first()
    )

    if not secuencia:
        raise ValueError(f"Secuencia '{nombre_secuencia}' no encontrada para este tenant")

    # Generar número formateado
    numero_actual = secuencia.siguiente_numero
    numero_formateado = f"{secuencia.prefijo}{str(numero_actual).zfill(secuencia.longitud_numero)}"

    # Incrementar para próxima vez
    secuencia.siguiente_numero = numero_actual + 1

    # El commit se hace en el servicio que llama esta función

    return numero_formateado


def crear_secuencia_si_no_existe(
    db: Session, nombre: str, prefijo: str, tenant_id: UUID, longitud_numero: int = 6
) -> None:
    """
    Crea una secuencia si no existe (útil para seeders).

    Args:
        db: Sesión de base de datos
        nombre: Nombre único de la secuencia
        prefijo: Prefijo a usar (ej: 'VEN-', 'CMP-')
        tenant_id: UUID del tenant
        longitud_numero: Longitud del número (default 6)
    """
    existe = db.query(Secuencias).filter(Secuencias.tenant_id == tenant_id, Secuencias.nombre == nombre).first()

    if not existe:
        nueva_secuencia = Secuencias(
            tenant_id=tenant_id, nombre=nombre, prefijo=prefijo, siguiente_numero=1, longitud_numero=longitud_numero
        )
        db.add(nueva_secuencia)


def obtener_siguiente_numero_preview(db: Session, nombre_secuencia: str, tenant_id: UUID) -> str:
    """
    Obtiene una vista previa del siguiente número SIN incrementar la secuencia.

    Args:
        db: Sesión de base de datos
        nombre_secuencia: Nombre de la secuencia
        tenant_id: UUID del tenant

    Returns:
        String formateado del siguiente número (sin consumir la secuencia)
    """
    secuencia = (
        db.query(Secuencias).filter(Secuencias.tenant_id == tenant_id, Secuencias.nombre == nombre_secuencia).first()
    )

    if not secuencia:
        raise ValueError(f"Secuencia '{nombre_secuencia}' no encontrada para este tenant")

    return f"{secuencia.prefijo}{str(secuencia.siguiente_numero).zfill(secuencia.longitud_numero)}"
