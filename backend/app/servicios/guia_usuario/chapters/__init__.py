"""
Módulos de capítulos para la guía de usuario.
Contiene las clases Chapter para cada sección de la guía.
"""

from backend.app.servicios.guia_usuario.chapters.quickstart import QuickStartChapter
from backend.app.servicios.guia_usuario.chapters.auth import AuthChapter
from backend.app.servicios.guia_usuario.chapters.products import ProductsChapter
from backend.app.servicios.guia_usuario.chapters.margin_calc import MarginCalculatorChapter
from backend.app.servicios.guia_usuario.chapters.crm import CRMChapter
from backend.app.servicios.guia_usuario.chapters.quotations import QuotationsChapter
from backend.app.servicios.guia_usuario.chapters.billing import BillingChapter
from backend.app.servicios.guia_usuario.chapters.pos import POSChapter

__all__ = [
    "QuickStartChapter",
    "AuthChapter",
    "ProductsChapter",
    "MarginCalculatorChapter",
    "CRMChapter",
    "QuotationsChapter",
    "BillingChapter",
    "POSChapter",
]
