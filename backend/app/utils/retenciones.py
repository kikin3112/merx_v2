"""
Motor de retenciones colombianas (ReteICA, ReteIVA, RetefFuente).
UVT 2026 = $52,374 COP (Decreto DIAN).
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

UVT_2026 = Decimal("52374")

# Tablas de retefuente por concepto (Art. 383 ET y Decreto 2418/2013)
TABLAS_RETEFUENTE: dict[str, dict] = {
    "compras": {
        "umbral_uvt": Decimal("10"),
        "tasa_declarante": Decimal("0.025"),
        "tasa_no_declarante": Decimal("0.035"),
    },
    "servicios": {
        "umbral_uvt": Decimal("4"),
        "tasa_declarante": Decimal("0.04"),
        "tasa_no_declarante": Decimal("0.06"),
    },
    "honorarios": {
        "umbral_uvt": Decimal("0"),
        "tasa_declarante": Decimal("0.11"),
        "tasa_no_declarante": Decimal("0.11"),
    },
    "arrendamiento_bienes_muebles": {
        "umbral_uvt": Decimal("0"),
        "tasa_declarante": Decimal("0.04"),
        "tasa_no_declarante": Decimal("0.04"),
    },
    "arrendamiento_bienes_raices": {
        "umbral_uvt": Decimal("0"),
        "tasa_declarante": Decimal("0.035"),
        "tasa_no_declarante": Decimal("0.035"),
    },
}


def calcular_retefuente(
    monto: Decimal,
    concepto: str = "compras",
    es_declarante: bool = True,
) -> Decimal:
    """
    Calcula RetefFuente según concepto y condición tributaria del proveedor.

    Args:
        monto: Base gravable (sin IVA)
        concepto: Tipo de transacción (compras, servicios, honorarios, etc.)
        es_declarante: True si el proveedor es declarante de renta

    Returns:
        Valor a retener. Retorna $0 si el monto está por debajo del umbral UVT.
    """
    config = TABLAS_RETEFUENTE.get(concepto)
    if not config:
        return Decimal("0.00")

    umbral = config["umbral_uvt"] * UVT_2026
    if monto < umbral:
        return Decimal("0.00")

    tasa = config["tasa_declarante"] if es_declarante else config["tasa_no_declarante"]
    return (monto * tasa).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_reteiva(
    monto_iva: Decimal,
    es_responsable_iva: bool = True,
) -> Decimal:
    """
    Calcula ReteIVA (15% del IVA generado, Art. 437-1 ET).
    Solo aplica a grandes contribuyentes y autorretenedores.

    Args:
        monto_iva: Valor del IVA de la transacción
        es_responsable_iva: Si el receptor es responsable del IVA

    Returns:
        Valor de ReteIVA a retener.
    """
    if not es_responsable_iva:
        return Decimal("0.00")
    return (monto_iva * Decimal("0.15")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_reteica(
    monto: Decimal,
    tasa_por_mil: Optional[Decimal] = None,
) -> Decimal:
    """
    Calcula ReteICA según la tarifa municipal (‰ — por mil).

    Args:
        monto: Base gravable
        tasa_por_mil: Tarifa en pesos por cada $1,000. Ej: Decimal("4.14") para Bogotá.
                      Si None, retorna $0 (no configurado).

    Returns:
        Valor de ReteICA a retener.
    """
    if tasa_por_mil is None:
        return Decimal("0.00")
    tasa = tasa_por_mil / Decimal("1000")
    return (monto * tasa).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
