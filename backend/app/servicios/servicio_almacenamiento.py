"""
Servicio de almacenamiento S3/R2 para PDFs y archivos.
Compatible con AWS S3, Cloudflare R2, DigitalOcean Spaces.
"""

import uuid
from typing import Optional

from ..config import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ServicioAlmacenamiento:
    """Gestiona el almacenamiento de archivos en S3/R2."""

    def __init__(self):
        self._client = None
        if self.is_enabled:
            try:
                import boto3
                kwargs = {
                    'service_name': 's3',
                    'region_name': settings.S3_REGION,
                }
                if settings.AWS_ACCESS_KEY_ID:
                    kwargs['aws_access_key_id'] = settings.AWS_ACCESS_KEY_ID
                if settings.AWS_SECRET_ACCESS_KEY:
                    kwargs['aws_secret_access_key'] = settings.AWS_SECRET_ACCESS_KEY
                if settings.S3_ENDPOINT_URL:
                    kwargs['endpoint_url'] = settings.S3_ENDPOINT_URL

                self._client = boto3.client(**kwargs)
                logger.info("S3 client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}")
                self._client = None

    @property
    def is_enabled(self) -> bool:
        return getattr(settings, 'S3_ENABLED', False)

    def subir_pdf(
        self,
        contenido: bytes,
        tenant_id: str,
        tipo: str,
        nombre_archivo: str,
    ) -> Optional[str]:
        """
        Sube un PDF a S3.

        Args:
            contenido: bytes del archivo
            tenant_id: ID del tenant
            tipo: tipo de documento (facturas, cotizaciones)
            nombre_archivo: nombre descriptivo

        Returns:
            S3 key del archivo, o None si S3 no está habilitado
        """
        if not self.is_enabled or not self._client:
            return None

        file_uuid = str(uuid.uuid4())
        key = f"{tenant_id}/{tipo}/{file_uuid}-{nombre_archivo}.pdf"

        try:
            self._client.put_object(
                Bucket=settings.S3_BUCKET,
                Key=key,
                Body=contenido,
                ContentType='application/pdf',
            )
            logger.info(f"PDF uploaded to S3: {key}")
            return key
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            return None

    def obtener_url_presigned(self, key: str) -> Optional[str]:
        """
        Genera una URL presignada para descargar un archivo.

        Args:
            key: S3 key del archivo

        Returns:
            URL presignada con expiración de 24h, o None
        """
        if not self.is_enabled or not self._client:
            return None

        try:
            url = self._client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.S3_BUCKET,
                    'Key': key,
                },
                ExpiresIn=settings.S3_PRESIGNED_URL_EXPIRY,
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None

    def eliminar_archivo(self, key: str) -> bool:
        """Elimina un archivo de S3."""
        if not self.is_enabled or not self._client:
            return False

        try:
            self._client.delete_object(
                Bucket=settings.S3_BUCKET,
                Key=key,
            )
            logger.info(f"File deleted from S3: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting from S3: {e}")
            return False
