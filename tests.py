"""Test suite for SCMS core functionalities."""

from decimal import Decimal
import pytest

from db.queries import (
    add_product, get_all_products, update_product, delete_product,
    add_inventory, get_inventory, get_low_stock,
    move_product, get_route_cost, get_cheapest_route_details,
    place_order, get_orders, update_order_status, delete_order,
    add_forecast, get_forecast, get_inventory_for_forecast,
    generate_summary_report, get_connection
)

def test_add_update_delete_product():
    """Test adding, updating, and deleting a product."""
    sku = "TESTSKU"
    delete_product(sku)
    add_product(sku, "Test Product", "Test Desc", 5)
    products = get_all_products()
    assert any(p[0] == sku for p in products)

    update_product(sku, "Updated Name", "Updated Desc", 10)
    updated = [p for p in get_all_products() if p[0] == sku][0]
    assert updated[1] == "Updated Name"
    assert updated[2] == "Updated Desc"
    assert updated[3] == 10

    delete_product(sku)
    products = get_all_products()
    assert not any(p[0] == sku for p in products)

def test_inventory_tracking_and_alert():
    """Test inventory addition and low stock alert."""
    sku = "SKU001"
    location = "Warehouse A"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM Inventory WHERE sku = %s AND location = %s", (sku, location)
    )
    conn.commit()

    add_inventory(sku, location, 3)
    inventory = get_inventory()
    assert any(i[1] == sku and i[2] == location for i in inventory)

    low_stock = get_low_stock()
    assert any(i[0] == sku and i[2] == location for i in low_stock)

def test_move_product_and_cost():
    """Test moving product and verifying transport cost."""
    sku = "SKU001"
    origin = "Warehouse A"
    destination = "Retail Hub 1"
    quantity = 1

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM Inventory WHERE sku = %s AND location IN (%s, %s)",
        (sku, origin, destination)
    )
    cursor.execute(
        "INSERT INTO Inventory (sku, location, quantity) VALUES (%s, %s, %s)",
        (sku, origin, 20)
    )
    conn.commit()

    cost = get_route_cost(origin, destination)
    assert cost is not None

    route = get_cheapest_route_details(origin, destination)
    assert route["cost"] == cost

    move_product(sku, origin, destination, quantity, cost)
    inventory = get_inventory()
    dest_qty = [i[3] for i in inventory if i[1] == sku and i[2] == destination]
    assert dest_qty and dest_qty[0] >= quantity

def test_order_flow():
    """Test placing, updating, and deleting an order."""
    sku = "SKU001"
    user = "TestUser"
    location = "Retail Hub 1"

    place_order(sku, 2, user, location)
    orders = get_orders(user, "User")
    assert any(o[1] == sku and o[3] == user for o in orders)

    order_id = orders[0][0]
    update_order_status(order_id, "Processed")
    updated = get_orders(user, "User")[0]
    assert updated[5] == "Processed"

    delete_order(order_id)
    orders = get_orders(user, "User")
    assert not any(o[0] == order_id for o in orders)

def test_forecast_and_gap():
    """Test demand forecasting and inventory gap calculation."""
    sku = "SKU001"
    add_forecast(sku, 10, "2025-11-10")
    forecasts = get_forecast()
    assert any(f[0] == sku for f in forecasts)

    inventory = get_inventory_for_forecast(sku)
    assert isinstance(inventory, (int, float, Decimal))

def test_summary_report():
    """Test generation of summary report."""
    report = generate_summary_report()
    assert "Total Orders" in report
    assert "Processed Orders" in report
    assert "Low Stock Items" in report
    assert "Total Logistics Cost" in report

@pytest.mark.timeout(10)
def test_reset_simulation():
    """Test resetting simulation data."""
    print(">>> Entered reset_simulation")
    conn = get_connection()
    cursor = conn.cursor()

    print(">>> Deleting dependent data")
    cursor.execute("DELETE FROM DemandForecast")
    cursor.execute("DELETE FROM Orders")
    cursor.execute("DELETE FROM Inventory")
    cursor.execute("DELETE FROM Logistics")  # Added to fix FK constraint

    print(">>> Deleting Products")
    cursor.execute("DELETE FROM Products")

    print(">>> Inserting default products")
    cursor.execute(
        "INSERT INTO Products (sku, name, description, price) VALUES (%s, %s, %s, %s)",
        ("SKU001", "Product A", "Desc", 10)
    )
    cursor.execute(
        "INSERT INTO Products (sku, name, description, price) VALUES (%s, %s, %s, %s)",
        ("SKU002", "Product B", "Desc", 15)
    )
    cursor.execute(
        "INSERT INTO Products (sku, name, description, price) VALUES (%s, %s, %s, %s)",
        ("SKU003", "Product C", "Desc", 20)
    )

    conn.commit()
    print(">>> reset_simulation complete")
