from contextlib import asynccontextmanager
from typing import AsyncGenerator
import uuid
import time

from sqlalchemy import text
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

from slowapi.errors import RateLimitExceeded

from .config import settings
from .utils.logger import (
    setup_logger,
    set_request_context,
    clear_request_context,
    log_performance
)
from .utils.rate_limiter import limiter
from .datos.db import engine, SessionLocal

# Importar todos los routers
from .rutas import (
    auth,
    cartera,
    compras,
    contabilidad,
    cotizaciones,
    crm,
    cuentas_contables,
    facturas,
    inventarios,
    medios_pago,
    ordenes_produccion,
    productos,
    recetas,
    reportes,
    terceros,
    usuarios,
    ventas,
    tenants
)

# Middleware de contexto de tenant
from .middleware.tenant_context import TenantContextMiddleware

# Configuración de Logger
logger = setup_logger(__name__)


# ============================================================================
# LIFESPAN EVENTS (FastAPI 0.109+)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Maneja eventos de inicio y cierre de la aplicación.
    Reemplaza los deprecados @app.on_event("startup") y @app.on_event("shutdown")
    """
    # STARTUP
    logger.info("=" * 60)
    logger.info(f"🚀 Iniciando {settings.APP_NAME}")
    logger.info(f"📦 Versión: {settings.APP_VERSION}")
    logger.info(f"🌍 Entorno: {settings.ENVIRONMENT.upper()}")
    logger.info(f"🔧 Debug: {settings.DEBUG}")
    logger.info("=" * 60)

    # Verificar conexión a base de datos
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Conexión a base de datos verificada")
    except Exception as e:
        logger.error(f"❌ Error conectando a base de datos: {str(e)}")
        raise

    # Log de configuración CORS
    logger.info(f"🌐 CORS configurado para: {', '.join(settings.cors_origins_list[:3])}...")

    # Advertencias de seguridad
    if settings.is_production and settings.DEBUG:
        logger.warning("⚠️  DEBUG activado en PRODUCCIÓN - ESTO ES UN RIESGO DE SEGURIDAD")

    if settings.is_production and "localhost" in settings.CORS_ORIGINS.lower():
        logger.warning("⚠️  CORS permite localhost en PRODUCCIÓN - Verifica configuración")

    logger.info("✅ Aplicación iniciada correctamente")
    logger.info("=" * 60)

    yield  # La aplicación se ejecuta

    # SHUTDOWN
    logger.info("🛑 Cerrando aplicación...")
    engine.dispose()
    logger.info("✅ Pool de conexiones cerrado")


# ============================================================================
# CREACIÓN DE LA APLICACIÓN
# ============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema ERP Contable para PyMEs - API REST",
    lifespan=lifespan,
    docs_url=f"{settings.API_PREFIX}/docs" if not settings.is_production else None,
    redoc_url=f"{settings.API_PREFIX}/redoc" if not settings.is_production else None,
    openapi_url=f"{settings.API_PREFIX}/openapi.json" if not settings.is_production else None
)

# Registrar limiter en el state de la app (requerido por slowapi)
app.state.limiter = limiter


# ============================================================================
# MIDDLEWARE DE REQUEST TRACKING
# ============================================================================

class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware que asigna request_id único a cada request y lo incluye en logs.
    También mide el tiempo de respuesta de cada request.
    """

    async def dispatch(self, request: Request, call_next):
        # Generar request_id único
        request_id = str(uuid.uuid4())

        # Intentar obtener user_id del estado del request (si ya fue autenticado)
        user_id = None

        # Establecer contexto para logging
        set_request_context(
            request_id=request_id,
            user_id=user_id
        )

        # Medir tiempo de respuesta
        start_time = time.time()

        try:
            # Agregar request_id al estado del request (accesible en endpoints)
            request.state.request_id = request_id

            # Log de request entrante
            logger.info(
                f"→ {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "client_ip": request.client.host if request.client else None
                }
            )

            # Procesar request
            response = await call_next(request)

            # Calcular duración
            duration_ms = (time.time() - start_time) * 1000

            # Log de respuesta
            logger.info(
                f"← {request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)",
                extra={
                    "status_code": response.status_code,
                    "duration_ms": duration_ms
                }
            )

            # Agregar header con request_id en la respuesta
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"✗ {request.method} {request.url.path} - ERROR ({duration_ms:.2f}ms)",
                exc_info=e,
                extra={"duration_ms": duration_ms}
            )
            raise

        finally:
            # Limpiar contexto
            clear_request_context()


# ============================================================================
# MIDDLEWARE DE SEGURIDAD
# ============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Agrega headers de seguridad a todas las respuestas.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Headers de seguridad
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        if settings.is_production:
            # HSTS solo en producción (requiere HTTPS)
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


# ============================================================================
# CONFIGURACIÓN DE MIDDLEWARE
# ============================================================================

# 1. Request tracking (debe ser el primero)
app.add_middleware(RequestContextMiddleware)

# 2. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. Tenant Context (para RLS multi-tenant)
app.add_middleware(TenantContextMiddleware)

# 4. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explícito, no "*"
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID", "Accept"],
    expose_headers=["X-Request-ID"],
    max_age=settings.CORS_MAX_AGE
)

# 4. Trusted Host (protección contra HTTP Host header attacks)
if settings.is_production:
    # En producción, configurar hosts permitidos
    allowed_hosts = ["api.tudominio.com", "www.tudominio.com"]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)


# ============================================================================
# MANEJADORES DE ERRORES GLOBALES
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Maneja errores de validación de Pydantic (422).
    Devuelve formato consistente con detalles de los errores.
    """
    logger.warning(
        f"Validation error en {request.url.path}",
        extra={"errors": exc.errors()}
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Error de validación en los datos enviados",
            "errors": exc.errors()
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """
    Maneja errores de lógica de negocio (ValueError).
    Devuelve un 400 Bad Request.
    """
    logger.warning(f"Business logic error en {request.url.path}: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Maneja HTTPException de FastAPI.
    Agrega logging antes de retornar la respuesta.
    """
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code} en {request.url.path}: {exc.detail}")
    else:
        logger.warning(f"HTTP {exc.status_code} en {request.url.path}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Maneja cualquier excepción no capturada.
    Devuelve un 500 Internal Server Error sin exponer detalles internos.
    """
    logger.error(
        f"Unhandled exception en {request.url.path}",
        exc_info=exc
    )

    # En desarrollo, mostrar el error completo
    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Error interno del servidor",
                "error": str(exc),
                "type": type(exc).__name__
            }
        )

    # En producción, ocultar detalles
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Error interno del servidor. Por favor contacte al administrador.",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Maneja errores de rate limiting (429 Too Many Requests).
    """
    logger.warning(
        f"Rate limit excedido: {request.method} {request.url.path}",
        extra={"ip": request.client.host if request.client else "unknown"}
    )
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Demasiadas solicitudes. Intente de nuevo en un momento.",
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """
    Maneja rutas no encontradas (404).
    """
    logger.warning(f"Ruta no encontrada: {request.method} {request.url.path}")

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": f"Ruta no encontrada: {request.method} {request.url.path}",
            "available_routes": f"{settings.API_PREFIX}/docs"
        }
    )


# ============================================================================
# RUTAS RAÍZ
# ============================================================================

@app.get("/", tags=["Sistema"])
def read_root():
    """
    Health check básico.
    Retorna información del sistema.
    """
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": f"{settings.API_PREFIX}/docs" if not settings.is_production else None
    }


@app.get("/health", tags=["Sistema"])
def health_check():
    """
    Health check completo incluyendo base de datos.
    Útil para orquestadores (Kubernetes, Docker Swarm, etc.)
    """
    health_status = {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

    # Verificar conexión a base de datos
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status["status"] = "unhealthy"
        health_status["database"] = "disconnected"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )

    return health_status


# ============================================================================
# INCLUSIÓN DE ROUTERS
# ============================================================================

# Todos los routers usan el prefijo de la API
prefix = settings.API_PREFIX

# Autenticación (sin prefijo adicional, solo /api/v1/auth)
app.include_router(auth.router, prefix=f"{prefix}/auth", tags=["Autenticación"])

# Multi-Tenancy
app.include_router(tenants.router, prefix=f"{prefix}/tenants", tags=["Tenants"])

# Módulos principales
app.include_router(usuarios.router, prefix=f"{prefix}/usuarios", tags=["Usuarios"])
app.include_router(terceros.router, prefix=f"{prefix}/terceros", tags=["Terceros"])
app.include_router(productos.router, prefix=f"{prefix}/productos", tags=["Productos"])

# Operaciones
app.include_router(ventas.router, prefix=f"{prefix}/ventas", tags=["Ventas"])
app.include_router(compras.router, prefix=f"{prefix}/compras", tags=["Compras"])
app.include_router(cotizaciones.router, prefix=f"{prefix}/cotizaciones", tags=["Cotizaciones"])
app.include_router(ordenes_produccion.router, prefix=f"{prefix}/ordenes-produccion", tags=["Producción"])

# CRM
app.include_router(crm.router, prefix=f"{prefix}")

# Inventarios
app.include_router(inventarios.router, prefix=f"{prefix}/inventarios", tags=["Inventarios"])

# Contabilidad
app.include_router(cuentas_contables.router, prefix=f"{prefix}/cuentas-contables", tags=["Contabilidad"])
app.include_router(contabilidad.router, prefix=f"{prefix}/contabilidad", tags=["Contabilidad"])

# Cartera y finanzas
app.include_router(cartera.router, prefix=f"{prefix}/cartera", tags=["Cartera"])
app.include_router(medios_pago.router, prefix=f"{prefix}/medios-pago", tags=["Medios de Pago"])

# Facturas
app.include_router(facturas.router, prefix=f"{prefix}/facturas", tags=["Facturas"])

# Reportes
app.include_router(reportes.router, prefix=f"{prefix}/reportes", tags=["Reportes"])

# Recetas
app.include_router(recetas.router, prefix=f"{prefix}/recetas", tags=["Recetas"])


# ============================================================================
# ENDPOINTS DE ADMINISTRACIÓN
# ============================================================================

@app.post(f"{prefix}/admin/seed", tags=["Administración"])
def ejecutar_seeds(
        current_user=None  # TODO: Agregar dependency de autenticación admin
):
    """
    Ejecuta la siembra de datos iniciales.

    ⚠️ ADVERTENCIA: Este endpoint debe estar protegido por autenticación.
    Solo usuarios con rol 'admin' deberían poder ejecutarlo.
    """
    # TODO: Descomentar cuando el sistema de auth esté completo
    # if current_user.rol != "admin":
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Requiere permisos de administrador"
    #     )

    try:
        from .utils.seeders import run_all_seeders

        logger.info("Ejecutando seeders...")
        run_all_seeders()
        logger.info("✅ Seeders completados")

        return {
            "status": "success",
            "message": "Datos iniciales generados correctamente"
        }
    except Exception as e:
        logger.error(f"Error ejecutando seeders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ejecutando seeders: {str(e)}"
        )


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    # Configuración desde environment o defaults
    host = "0.0.0.0"
    port = 8000
    reload = settings.DEBUG  # Auto-reload solo en desarrollo

    logger.info(f"Iniciando servidor en http://{host}:{port}")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True
    )