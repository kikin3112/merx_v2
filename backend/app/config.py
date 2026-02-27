"""
Configuración global de la aplicación.
Utiliza Pydantic Settings para validación y carga desde variables de entorno.
"""

import secrets
from typing import Any, List, Literal, Optional

from pydantic import Field, PostgresDsn, ValidationError, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración global de la aplicación.

    Variables de entorno requeridas (.env):
    - DB_URL: postgresql://user:pass@host:port/dbname
    - SECRET_KEY: Clave secreta para JWT (mínimo 32 caracteres)

    Variables opcionales:
    - ENVIRONMENT: development|staging|production (default: development)
    - DEBUG: true|false (default: false)
    - LOG_LEVEL: DEBUG|INFO|WARNING|ERROR|CRITICAL (default: INFO)
    """

    # ============================================================================
    # ENTORNO
    # ============================================================================

    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development", description="Entorno de ejecución"
    )

    DEBUG: bool = Field(default=False, description="Modo debug (solo para development)")

    # ============================================================================
    # BASE DE DATOS
    # ============================================================================

    DB_URL: Optional[PostgresDsn] = Field(
        default=None, description="URL de conexión PostgreSQL (postgresql://user:pass@host:port/db)"
    )

    DATABASE_URL: Optional[str] = Field(
        default=None, description="URL de conexión PostgreSQL (alias para Railway/Render)"
    )

    DB_POOL_SIZE: int = Field(default=10, ge=5, le=50, description="Tamaño del pool de conexiones")

    DB_MAX_OVERFLOW: int = Field(
        default=20, ge=10, le=100, description="Máximo de conexiones adicionales sobre el pool"
    )

    DB_POOL_RECYCLE: int = Field(
        default=3600, ge=300, description="Segundos antes de reciclar conexiones (default: 1 hora)"
    )

    DB_POOL_TIMEOUT: int = Field(
        default=30, ge=5, le=120, description="Timeout en segundos para obtener conexión del pool"
    )

    DB_STATEMENT_TIMEOUT: int = Field(
        default=30000,
        ge=1000,
        le=300000,
        description="PostgreSQL statement_timeout en milisegundos (previene queries infinitos)",
    )

    DB_IDLE_IN_TRANSACTION_TIMEOUT: int = Field(
        default=60000,
        ge=1000,
        le=600000,
        description="PostgreSQL idle_in_transaction_session_timeout en milisegundos (previene locks prolongados)",
    )

    # ============================================================================
    # APLICACIÓN
    # ============================================================================

    APP_NAME: str = Field(default="MERX - Sistema contable para PyMEs", max_length=100)

    APP_VERSION: str = Field(
        default="1.0.0", pattern=r"^\d+\.\d+\.\d+$", description="Versión semántica (MAJOR.MINOR.PATCH)"
    )

    API_PREFIX: str = Field(default="/api/v1", description="Prefijo para todas las rutas de la API")

    # ============================================================================
    # ERROR TRACKING (SENTRY)
    # ============================================================================

    SENTRY_DSN: Optional[str] = Field(
        default=None, description="Sentry DSN para error tracking (opcional, solo production/staging)"
    )

    # ============================================================================
    # CORS
    # ============================================================================

    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost:5173",
        description="Orígenes permitidos para CORS (separados por coma)",
    )

    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Permitir envío de cookies/credenciales en CORS")

    CORS_MAX_AGE: int = Field(
        default=600, ge=0, description="Tiempo en segundos para cachear respuestas preflight CORS"
    )

    ALLOWED_HOSTS: str = Field(
        # TODO: Aterrizar esto a dominios específicos en producción.
        # Se agrega '*' temporalmente para permitir health checks de Railway.
        default="localhost,127.0.0.1,0.0.0.0,*",
        description="Hosts permitidos para TrustedHostMiddleware (separados por coma)",
    )

    # ============================================================================
    # JWT / SEGURIDAD
    # ============================================================================

    SECRET_KEY: Optional[str] = Field(
        default=None, min_length=32, description="Clave secreta para JWT (mínimo 32 caracteres)"
    )

    ALGORITHM: str = Field(
        default="HS256", pattern="^(HS256|HS384|HS512)$", description="Algoritmo de encriptación JWT"
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, ge=5, le=1440, description="Tiempo de expiración del access token en minutos"
    )

    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, ge=1, le=30, description="Tiempo de expiración del refresh token en días"
    )

    # ============================================================================
    # LOGGING
    # ============================================================================

    LOG_LEVEL: str = Field(
        default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$", description="Nivel de logging"
    )

    LOG_FORMAT: Literal["json", "text"] = Field(
        default="json", description="Formato de logs (json para producción, text para development)"
    )

    # ============================================================================
    # RATE LIMITING
    # ============================================================================

    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Activar rate limiting")

    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=10, le=1000, description="Requests máximos por minuto por IP")

    # ============================================================================
    # S3 / ALMACENAMIENTO
    # ============================================================================

    S3_ENABLED: bool = Field(default=False, description="Habilitar almacenamiento S3/R2")

    S3_BUCKET: str = Field(default="chandelier-documents", description="Nombre del bucket S3")

    S3_REGION: str = Field(default="us-east-1", description="Región del bucket S3")

    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, description="AWS Access Key ID")

    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, description="AWS Secret Access Key")

    S3_ENDPOINT_URL: Optional[str] = Field(default=None, description="URL del endpoint S3 (para R2, Spaces, etc.)")

    S3_PRESIGNED_URL_EXPIRY: int = Field(
        default=86400, ge=3600, description="Expiración de URLs presignadas en segundos (default: 24h)"
    )

    # ============================================================================
    # CLERK
    # ============================================================================

    CLERK_SECRET_KEY: Optional[str] = Field(default=None, description="Clerk secret key (sk_test_...)")

    CLERK_WEBHOOK_SECRET: Optional[str] = Field(default=None, description="Clerk webhook signing secret (whsec_...)")

    # ============================================================================
    # TIMEOUTS
    # ============================================================================

    REQUEST_TIMEOUT: int = Field(default=30, ge=5, le=300, description="Timeout para requests HTTP en segundos")

    # ============================================================================
    # CONFIGURACIÓN DE PYDANTIC
    # ============================================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignora variables extra en .env
        validate_default=True,
    )

    # ============================================================================
    # VALIDADORES
    # ============================================================================

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key_strength(cls, v: Optional[str]) -> Optional[str]:
        """
        Valida que el SECRET_KEY tenga suficiente entropía.
        No debe ser un valor obvio o de ejemplo.
        """
        if v is None:
            return v

        forbidden_values = [
            "changeme",
            "secret",
            "password",
            "12345678901234567890123456789012",
            "your-secret-key-here",
            "supersecret",
            "my-secret-key",
        ]

        if v.lower() in forbidden_values:
            raise ValueError(
                "SECRET_KEY es inseguro. Use: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

        # Validar que no sea solo caracteres repetidos
        if len(set(v)) < 10:
            raise ValueError(
                "SECRET_KEY tiene baja entropía (pocos caracteres únicos). "
                "Use: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

        return v

    @field_validator("DEBUG")
    @classmethod
    def validate_debug_in_production(cls, v: bool, info) -> bool:
        """
        Asegura que DEBUG esté desactivado en producción.
        """
        # 'info.data' contiene los campos ya validados
        environment = info.data.get("ENVIRONMENT", "development")

        if environment == "production" and v is True:
            raise ValueError("DEBUG no puede estar activado en producción por razones de seguridad")

        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_in_production(cls, v: str, info) -> str:
        """
        Valida que CORS no permita '*' en producción.
        """
        environment = info.data.get("ENVIRONMENT", "development")

        if environment == "production" and ("*" in v or "localhost" in v.lower()):
            raise ValueError(
                "CORS_ORIGINS no puede contener '*' o 'localhost' en producción. "
                "Especifica los dominios exactos permitidos."
            )

        return v

    @field_validator("DB_URL")
    @classmethod
    def validate_db_ssl_in_production(cls, v: PostgresDsn, info) -> PostgresDsn:
        """
        Recomienda SSL para conexiones DB en producción.
        """
        environment = info.data.get("ENVIRONMENT", "development")

        if environment == "production" and v:
            url_str = str(v)
            if "sslmode" not in url_str.lower():
                # Solo advertencia, no error (algunas DBs manejan SSL automáticamente)
                import warnings

                warnings.warn(
                    "Considera agregar '?sslmode=require' a DB_URL en producción para conexiones seguras", UserWarning
                )

        return v

    @model_validator(mode="before")
    @classmethod
    def resolve_database_url(cls, data: Any) -> Any:
        """
        Resolve DB_URL from DATABASE_URL (Railway/Render convention).
        Generate a default SECRET_KEY for development if not provided.
        """
        if isinstance(data, dict):
            # If DB_URL not set but DATABASE_URL is, use DATABASE_URL
            if not data.get("DB_URL") and data.get("DATABASE_URL"):
                data["DB_URL"] = data["DATABASE_URL"]

            # If SECRET_KEY not set in development, generate one
            environment = data.get("ENVIRONMENT", "development")
            if not data.get("SECRET_KEY") and environment == "development":
                data["SECRET_KEY"] = "dev_secret_key_for_development_only_min_32_chars"  # nosec B105

            # In production, both must be set
            if environment == "production":
                if not data.get("DB_URL") and not data.get("DATABASE_URL"):
                    raise ValueError("DB_URL or DATABASE_URL is required in production")
                if not data.get("SECRET_KEY"):
                    raise ValueError("SECRET_KEY is required in production")

        return data

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================

    @computed_field
    @property
    def cors_origins_list(self) -> List[str]:
        """
        Convierte CORS_ORIGINS de string separado por comas a lista limpia.
        Elimina espacios y entradas vacías.
        """
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @computed_field
    @property
    def allowed_hosts_list(self) -> List[str]:
        """
        Convierte ALLOWED_HOSTS de string separado por comas a lista limpia.
        Elimina espacios y entradas vacías.
        """
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

    @computed_field
    @property
    def is_production(self) -> bool:
        """Indica si está en entorno de producción"""
        return self.ENVIRONMENT == "production"

    @computed_field
    @property
    def is_development(self) -> bool:
        """Indica si está en entorno de desarrollo"""
        return self.ENVIRONMENT == "development"

    @computed_field
    @property
    def is_staging(self) -> bool:
        """Indica si está en entorno de staging"""
        return self.ENVIRONMENT == "staging"

    @computed_field
    @property
    def resolved_db_url(self) -> str:
        """Return the resolved database URL (DB_URL or DATABASE_URL)"""
        if self.DB_URL:
            return str(self.DB_URL)
        if self.DATABASE_URL:
            return self.DATABASE_URL
        raise ValueError("No database URL configured")


# ============================================================================
# INSTANCIA GLOBAL (SINGLETON)
# ============================================================================

try:
    settings = Settings()
except ValidationError as e:
    print("❌ ERROR EN CONFIGURACIÓN:")
    print(e)
    print("\n💡 AYUDA:")
    print("1. Asegúrate de tener un archivo .env en la raíz del proyecto")
    print("2. Variables requeridas: DB_URL, SECRET_KEY")
    print("3. Genera SECRET_KEY con: python -c 'import secrets; print(secrets.token_urlsafe(32))'")
    raise


# ============================================================================
# HELPER PARA GENERAR SECRET_KEY
# ============================================================================


def generate_secret_key() -> str:
    """
    Genera un SECRET_KEY seguro.

    Uso:
        from app.config import generate_secret_key
        print(generate_secret_key())
    """
    return secrets.token_urlsafe(32)


if __name__ == "__main__":
    # Script para generar SECRET_KEY
    print("SECRET_KEY generado:")
    print(generate_secret_key())
