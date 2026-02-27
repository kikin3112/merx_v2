"""
Test inventory concurrency with pessimistic locking.
Verifies that race conditions are prevented during concurrent stock operations.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from uuid import UUID

import pytest
from app.datos.modelos import Inventarios, Productos
from app.servicios.servicio_inventario import ServicioInventario, TipoMovimiento


def test_concurrent_stock_deductions_prevent_negative(db_session, tenant_admin_token):
    """
    Concurrent sales should not cause negative stock due to pessimistic locking.

    Scenario:
    - Product has stock=10
    - 3 concurrent transactions try to deduct 8 units each
    - Expected: Only 1 succeeds, 2 fail with "Stock insuficiente"
    - Final stock: 2 (10 - 8)
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])

    # Create product with stock=10
    producto = Productos(
        tenant_id=tenant_id,
        nombre="Test Vela",
        codigo_interno="TEST-001",
        precio_venta=Decimal("10000"),
        porcentaje_iva=Decimal("19"),
        categoria="Producto_Propio",
        unidad_medida="UNIDAD",
        maneja_inventario=True,
        estado=True,
    )
    db_session.add(producto)
    db_session.flush()

    inventario = Inventarios(
        tenant_id=tenant_id,
        producto_id=producto.id,
        cantidad_disponible=Decimal("10"),
        costo_promedio_ponderado=Decimal("5000"),
        valor_total=Decimal("50000"),
    )
    db_session.add(inventario)
    db_session.commit()

    # Try 3 concurrent sales of 8 units each (total 24, but only 10 available)
    def deduct_stock():
        """Attempt to deduct 8 units from stock."""
        servicio = ServicioInventario(db_session, tenant_id)
        try:
            servicio.crear_movimiento(producto_id=producto.id, tipo=TipoMovimiento.SALIDA, cantidad=Decimal("8"))
            db_session.commit()
            return "success"
        except ValueError as e:
            db_session.rollback()
            if "Stock insuficiente" in str(e):
                return "insufficient_stock"
            return f"error: {str(e)}"
        except Exception as e:
            db_session.rollback()
            return f"error: {str(e)}"

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(deduct_stock) for _ in range(3)]
        results = [future.result() for future in as_completed(futures)]

    # Verify results
    success_count = results.count("success")
    insufficient_count = results.count("insufficient_stock")

    assert success_count == 1, f"Expected 1 success, got {success_count}. Results: {results}"
    assert insufficient_count == 2, f"Expected 2 insufficient_stock, got {insufficient_count}. Results: {results}"

    # Verify final stock
    db_session.refresh(inventario)
    assert inventario.cantidad_disponible == Decimal("2"), f"Expected stock=2, got {inventario.cantidad_disponible}"


def test_concurrent_entries_update_avg_cost_correctly(db_session, tenant_admin_token):
    """
    Concurrent inventory entries should correctly update weighted average cost.

    Scenario:
    - Product has stock=10 @ $5000 (total: $50,000)
    - 2 concurrent entries: +5 @ $6000 and +5 @ $7000
    - Expected final: stock=20, avg_cost calculated correctly
    """
    tenant_id = UUID(tenant_admin_token["tenant_id"])

    producto = Productos(
        tenant_id=tenant_id,
        nombre="Test Materia Prima",
        codigo_interno="MP-001",
        precio_venta=Decimal("0"),
        porcentaje_iva=Decimal("19"),
        categoria="Insumo",
        unidad_medida="UNIDAD",
        maneja_inventario=True,
        estado=True,
    )
    db_session.add(producto)
    db_session.flush()

    inventario = Inventarios(
        tenant_id=tenant_id,
        producto_id=producto.id,
        cantidad_disponible=Decimal("10"),
        costo_promedio_ponderado=Decimal("5000"),
        valor_total=Decimal("50000"),
    )
    db_session.add(inventario)
    db_session.commit()

    def add_stock(cantidad: Decimal, costo: Decimal):
        """Add stock with specific cost."""
        servicio = ServicioInventario(db_session, tenant_id)
        try:
            servicio.crear_movimiento(
                producto_id=producto.id, tipo=TipoMovimiento.ENTRADA, cantidad=cantidad, costo_unitario=costo
            )
            db_session.commit()
            return "success"
        except Exception as e:
            db_session.rollback()
            return f"error: {str(e)}"

    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(add_stock, Decimal("5"), Decimal("6000"))
        future2 = executor.submit(add_stock, Decimal("5"), Decimal("7000"))
        results = [future1.result(), future2.result()]

    # Both should succeed
    assert results.count("success") == 2, f"Expected 2 successes, got {results}"

    # Verify final state
    db_session.refresh(inventario)
    assert inventario.cantidad_disponible == Decimal("20"), f"Expected stock=20, got {inventario.cantidad_disponible}"

    # Expected average cost: (10*5000 + 5*6000 + 5*7000) / 20 = 115000/20 = 5750
    expected_avg = Decimal("5750")
    assert (
        inventario.costo_promedio_ponderado == expected_avg
    ), f"Expected avg_cost={expected_avg}, got {inventario.costo_promedio_ponderado}"


def test_production_with_concurrent_ingredient_usage(db_session, tenant_admin_token):
    """
    Concurrent production processes should not cause negative ingredient stock.

    Scenario:
    - Ingredient has stock=100
    - 2 concurrent production processes each need 60 units
    - Expected: Only 1 succeeds, 1 fails with "Stock insuficiente"
    """
    # This test would require full recipe setup
    # Placeholder for now - to be implemented after recipe fixtures are created
    pytest.skip("Requires recipe fixtures - implement in Phase 2")
