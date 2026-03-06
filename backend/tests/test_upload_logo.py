"""
Integration tests for POST /api/v1/tenants/me/logo endpoint.
Tests: valid PNG upload, invalid format (gif), oversized file, non-admin role.
"""

import io
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_png_bytes(size_bytes: int = 1024) -> bytes:
    """Create a minimal valid-looking PNG file of approximately `size_bytes`."""
    # Real PNG header + IDAT chunk filler (enough for content_type sniff)
    header = b"\x89PNG\r\n\x1a\n"
    filler = b"\x00" * (size_bytes - len(header))
    return header + filler


def _make_gif_bytes() -> bytes:
    """GIF magic bytes."""
    return b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_upload_logo_endpoint(client, tenant_admin_token):
    """POST /me/logo with valid PNG + admin role → 200 with url_logo."""
    token = tenant_admin_token["token"]
    png_data = _make_png_bytes(1024)

    with patch(
        "app.servicios.servicio_almacenamiento.ServicioAlmacenamiento.subir_imagen",
        return_value="tenants/some-uuid/logo.png",
    ):
        response = client.post(
            "/api/v1/tenants/me/logo",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("logo.png", io.BytesIO(png_data), "image/png")},
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "url_logo" in data
    assert "tenants/" in str(data["url_logo"])


def test_upload_logo_formato_invalido(client, tenant_admin_token):
    """POST /me/logo with GIF content_type → 422."""
    token = tenant_admin_token["token"]
    gif_data = _make_gif_bytes()

    response = client.post(
        "/api/v1/tenants/me/logo",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("logo.gif", io.BytesIO(gif_data), "image/gif")},
    )

    assert response.status_code == 422, response.text


def test_upload_logo_tamaño_excedido(client, tenant_admin_token):
    """POST /me/logo with 3MB PNG → 422."""
    token = tenant_admin_token["token"]
    large_png = _make_png_bytes(3 * 1024 * 1024)  # 3MB

    response = client.post(
        "/api/v1/tenants/me/logo",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("big.png", io.BytesIO(large_png), "image/png")},
    )

    assert response.status_code == 422, response.text


def test_upload_logo_sin_admin(client, vendedor_token):
    """POST /me/logo with vendedor role → 403."""
    token = vendedor_token["token"]
    png_data = _make_png_bytes(1024)

    response = client.post(
        "/api/v1/tenants/me/logo",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("logo.png", io.BytesIO(png_data), "image/png")},
    )

    assert response.status_code == 403, response.text
