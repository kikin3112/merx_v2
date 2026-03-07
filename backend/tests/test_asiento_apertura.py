"""
Tests for C-07: Asiento de apertura endpoint.
POST /contabilidad/asiento-apertura creates an APERTURA-type balanced entry.
"""

from uuid import UUID

from app.datos.modelos import AsientosContables, CuentasContables, Secuencias


def _headers(token_data: dict) -> dict:
    return {
        "Authorization": f"Bearer {token_data['token']}",
        "X-Tenant-ID": token_data["tenant_id"],
    }


def _seed_cuenta(db, tenant_id: UUID, codigo: str):
    cuenta = CuentasContables(
        tenant_id=tenant_id,
        codigo=codigo,
        nombre=f"Cuenta {codigo}",
        tipo_cuenta="ACTIVO" if codigo.startswith("1") else "PASIVO",
        nivel=4,
        naturaleza="DEBITO" if codigo.startswith("1") else "CREDITO",
        acepta_movimiento=True,
        estado=True,
    )
    db.add(cuenta)
    db.flush()
    return cuenta


def _seed_seq(db, tenant_id: UUID):
    seq = Secuencias(
        tenant_id=tenant_id,
        nombre="ASIENTOS",
        prefijo="AS-",
        siguiente_numero=1,
        longitud_numero=6,
    )
    db.add(seq)
    db.flush()


def test_asiento_apertura_crea_tipo_apertura(client, db_session, tenant_admin_token):
    """
    POST /contabilidad/asiento-apertura creates APERTURA type entry.
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])
    headers = _headers(tenant_admin_token)

    _seed_seq(db_session, tenant_id)
    cuenta_caja = _seed_cuenta(db_session, tenant_id, "1105")
    cuenta_capital = _seed_cuenta(db_session, tenant_id, "3115")
    db_session.commit()

    payload = {
        "fecha": "2026-01-01",
        "concepto": "Saldos iniciales empresa",
        "saldos": [
            {"cuenta_id": str(cuenta_caja.id), "debito": "5000000", "credito": "0"},
            {"cuenta_id": str(cuenta_capital.id), "debito": "0", "credito": "5000000"},
        ],
    }

    resp = client.post("/api/v1/contabilidad/asiento-apertura", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text

    data = resp.json()
    assert data["tipo_asiento"] == "APERTURA"

    # Verify in DB
    asiento = (
        db_session.query(AsientosContables)
        .filter(
            AsientosContables.tenant_id == tenant_id,
            AsientosContables.tipo_asiento == "APERTURA",
        )
        .first()
    )
    assert asiento is not None
    assert asiento.estado == "ACTIVO"


def test_asiento_apertura_desbalanceado_retorna_400(client, db_session, tenant_admin_token):
    """
    Unbalanced apertura entry (debits != credits) returns HTTP 400.
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])
    headers = _headers(tenant_admin_token)

    _seed_seq(db_session, tenant_id)
    cuenta_caja = _seed_cuenta(db_session, tenant_id, "1105")
    db_session.commit()

    payload = {
        "fecha": "2026-01-01",
        "saldos": [
            # Only debits, no matching credits → unbalanced
            {"cuenta_id": str(cuenta_caja.id), "debito": "5000000", "credito": "0"},
        ],
    }

    resp = client.post("/api/v1/contabilidad/asiento-apertura", json=payload, headers=headers)
    assert resp.status_code == 400, resp.text
