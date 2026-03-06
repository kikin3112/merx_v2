"""
Script interactivo para soft-delete de tenants de prueba.
Requiere confirmación explícita antes de cualquier cambio.

Tenants PROTEGIDOS (nunca se tocan):
  - e44828e5-e76b-48df-b3a4-1555ffb7e321  (Luz de Luna)
  - [agregar D'Aroma ID aquí antes de ejecutar]

Uso:
  cd backend
  python -m scripts.cleanup_test_tenants
"""

import os
import sys
from datetime import datetime, timezone

# Agregar el directorio raíz del backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# TENANTS REALES — NUNCA TOCAR
TENANTS_REALES: set[str] = {
    "e44828e5-e76b-48df-b3a4-1555ffb7e321",  # Luz de Luna
    # Agregar el UUID de D'Aroma aquí antes de ejecutar en producción
}


def main() -> None:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    db_url = os.environ.get("DB_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: Define DB_URL o DATABASE_URL antes de ejecutar.")
        sys.exit(1)

    engine = create_engine(str(db_url))
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Listar todos los tenants activos
        rows = db.execute(
            text("SELECT id, nombre, created_at FROM tenants WHERE deleted_at IS NULL ORDER BY created_at")
        ).fetchall()

        if not rows:
            print("No hay tenants activos.")
            return

        print("\n=== TENANTS ACTIVOS ===")
        candidatos = []
        for row in rows:
            tid = str(row[0])
            nombre = row[1]
            created = row[2]
            protegido = tid in TENANTS_REALES
            status = "[PROTEGIDO]" if protegido else "[CANDIDATO]"
            print(f"  {status} {tid}  {nombre}  ({created})")
            if not protegido:
                candidatos.append((tid, nombre))

        if not candidatos:
            print("\nNo hay tenants candidatos para eliminar.")
            return

        print(f"\n{len(candidatos)} tenants candidatos para soft-delete.")
        print(f"{len(TENANTS_REALES)} tenants protegidos (intocables).")
        confirmacion = input("\n¿Confirmar soft-delete de los candidatos? Escribe 'yes' para continuar: ").strip()

        if confirmacion != "yes":
            print("Operación cancelada.")
            return

        ahora = datetime.now(timezone.utc)
        ids_candidatos = [c[0] for c in candidatos]
        placeholders = ", ".join(f"'{tid}'" for tid in ids_candidatos)

        db.execute(
            text(f"UPDATE tenants SET deleted_at = :ahora WHERE id IN ({placeholders})"),
            {"ahora": ahora},
        )
        db.commit()

        print(f"\nSoft-delete completado: {len(candidatos)} tenants archivados.")
        for tid, nombre in candidatos:
            print(f"  - {nombre} ({tid})")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
