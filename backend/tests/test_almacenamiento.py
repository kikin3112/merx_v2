"""
Unit tests for ServicioAlmacenamiento image methods.
Tests: subir_imagen, obtener_imagen_bytes (enabled/disabled).
"""

from io import BytesIO
from unittest.mock import MagicMock, patch

from app.servicios.servicio_almacenamiento import ServicioAlmacenamiento

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service_enabled() -> ServicioAlmacenamiento:
    """Return a ServicioAlmacenamiento instance with a mocked S3 client."""
    with patch("app.servicios.servicio_almacenamiento.settings") as mock_settings:
        mock_settings.S3_ENABLED = True
        mock_settings.S3_BUCKET = "test-bucket"
        mock_settings.S3_REGION = "us-east-1"
        mock_settings.AWS_ACCESS_KEY_ID = "AKIATEST"
        mock_settings.AWS_SECRET_ACCESS_KEY = "secret"
        mock_settings.S3_ENDPOINT_URL = None
        # Patch boto3.client so __init__ doesn't actually connect
        with patch("boto3.client") as mock_boto3:
            mock_boto3.return_value = MagicMock()
            svc = ServicioAlmacenamiento()
    return svc


def _make_service_disabled() -> ServicioAlmacenamiento:
    """Return a ServicioAlmacenamiento instance with S3 disabled."""
    with patch("app.servicios.servicio_almacenamiento.settings") as mock_settings:
        mock_settings.S3_ENABLED = False
        svc = ServicioAlmacenamiento()
    return svc


# ---------------------------------------------------------------------------
# Tests: subir_imagen
# ---------------------------------------------------------------------------


def test_subir_imagen():
    """subir_imagen returns correct S3 key when S3 is enabled."""
    svc = _make_service_enabled()
    mock_client = MagicMock()
    svc._client = mock_client

    with patch("app.servicios.servicio_almacenamiento.settings") as mock_settings:
        mock_settings.S3_ENABLED = True
        mock_settings.S3_BUCKET = "test-bucket"
        key = svc.subir_imagen(b"imagedata", "tenant-id", "logo", "png")

    assert key == "tenants/tenant-id/logo.png"
    mock_client.put_object.assert_called_once()
    call_kwargs = mock_client.put_object.call_args.kwargs
    assert call_kwargs["Key"] == "tenants/tenant-id/logo.png"
    assert call_kwargs["ContentType"] == "image/png"
    assert call_kwargs["Body"] == b"imagedata"


def test_subir_imagen_s3_disabled():
    """subir_imagen returns None when S3 is disabled — no S3 call made."""
    svc = _make_service_disabled()
    mock_client = MagicMock()
    svc._client = mock_client

    key = svc.subir_imagen(b"imagedata", "tenant-id", "logo", "png")

    assert key is None
    mock_client.put_object.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: obtener_imagen_bytes
# ---------------------------------------------------------------------------


def test_obtener_imagen_bytes():
    """obtener_imagen_bytes returns raw bytes from S3 object body."""
    svc = _make_service_enabled()
    mock_client = MagicMock()
    svc._client = mock_client

    expected_bytes = b"\x89PNG\r\nfakeimage"
    mock_body = BytesIO(expected_bytes)
    mock_client.get_object.return_value = {"Body": mock_body}

    with patch("app.servicios.servicio_almacenamiento.settings") as mock_settings:
        mock_settings.S3_ENABLED = True
        mock_settings.S3_BUCKET = "test-bucket"
        result = svc.obtener_imagen_bytes("tenants/tenant-id/logo.png")

    assert result == expected_bytes
    mock_client.get_object.assert_called_once()


def test_obtener_imagen_bytes_s3_disabled():
    """obtener_imagen_bytes returns None when S3 is disabled."""
    svc = _make_service_disabled()
    mock_client = MagicMock()
    svc._client = mock_client

    result = svc.obtener_imagen_bytes("tenants/tenant-id/logo.png")

    assert result is None
    mock_client.get_object.assert_not_called()
