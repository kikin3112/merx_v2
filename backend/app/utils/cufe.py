"""
Generador de CUFE (Código Único de Factura Electrónica).
Implementa Resolución DIAN 000042/2016 y 000012/2021.
"""

import hashlib
from decimal import Decimal


def generar_cufe(
    nit_emisor: str,
    fecha_hora: str,
    numero_factura: str,
    valor_total: str,
    valor_iva: str,
    codigo_tipo_operacion: str,
    nit_receptor: str,
    tipo_ambiente: str,
    llave_tecnica: str,
) -> str:
    """
    Genera CUFE usando SHA-384 según Resolución DIAN 000042/2016.

    Args:
        nit_emisor: NIT del emisor sin dígito de verificación
        fecha_hora: Timestamp en formato "YYYYMMDDHHmmss"
        numero_factura: Número de la factura (ej: "SETP990000001")
        valor_total: Valor total con 2 decimales como string (ej: "1500000.00")
        valor_iva: Valor IVA con 2 decimales como string (ej: "285000.00")
        codigo_tipo_operacion: "01" = venta nacional, "02" = exportación
        nit_receptor: NIT o documento del receptor
        tipo_ambiente: "1" = producción, "2" = habilitación/pruebas
        llave_tecnica: Clave técnica asignada por DIAN al rango de numeración

    Returns:
        Hash SHA-384 en hexadecimal (96 caracteres).
    """
    cadena = (
        f"{nit_emisor}"
        f"{fecha_hora}"
        f"{numero_factura}"
        f"{valor_total}"
        f"{valor_iva}"
        f"{codigo_tipo_operacion}"
        f"{nit_receptor}"
        f"{tipo_ambiente}"
        f"{llave_tecnica}"
    )
    return hashlib.sha384(cadena.encode("utf-8")).hexdigest()


def formatear_valor_cufe(valor: Decimal) -> str:
    """
    Formatea un Decimal para uso en la cadena CUFE (2 decimales fijos).

    Args:
        valor: Monto monetario

    Returns:
        String con exactamente 2 decimales (ej: "1500000.00")
    """
    return f"{valor:.2f}"
