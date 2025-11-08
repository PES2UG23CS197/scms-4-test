from db.connection import get_connection

# PRODUCT FUNCTIONS
def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Products")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def add_product(sku, name, description, threshold):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Products (sku, name, description, threshold) VALUES (%s, %s, %s, %s)",
                   (sku, name, description, threshold))
    conn.commit()
    write_log(1, f"Created product {sku}")
    cursor.close()
    conn.close()

def update_product(sku, name, description, threshold):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Products SET name=%s, description=%s, threshold=%s WHERE sku=%s",
                   (name, description, threshold, sku))
    conn.commit()
    write_log(1, f"Updated product {sku}")
    cursor.close()
    conn.close()

def delete_product(sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Inventory WHERE sku = %s", (sku,))
    cursor.execute("DELETE FROM Products WHERE sku = %s", (sku,))
    conn.commit()
    write_log(1, f"Deleted product {sku}")
    cursor.close()
    conn.close()


# INVENTORY FUNCTIONS
def get_inventory():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Inventory.inventory_id, Inventory.sku, Inventory.location, Inventory.quantity,
               Products.threshold, Products.name
        FROM Inventory
        JOIN Products ON Inventory.sku = Products.sku
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def add_inventory(sku, location, quantity):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Inventory (sku, location, quantity) VALUES (%s, %s, %s)",
                   (sku, location, quantity))
    conn.commit()
    write_log(1, f"Added inventory for {sku} at {location}: {quantity}")
    cursor.close()
    conn.close()

def update_inventory(sku, location, quantity):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Inventory
        SET quantity = %s
        WHERE sku = %s AND location = %s
    """, (quantity, sku, location))
    conn.commit()
    write_log(1, f"Updated inventory for {sku} at {location}: {quantity}")
    cursor.close()
    conn.close()


def delete_inventory_for_sku(sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Inventory WHERE sku = %s", (sku,))
    conn.commit()
    cursor.close()
    conn.close()

def get_low_stock():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.sku, p.name, i.location, i.quantity, p.threshold
        FROM Inventory i
        JOIN Products p ON i.sku = p.sku
        WHERE i.quantity < p.threshold AND i.location NOT LIKE 'Retail Hub%'
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_products_by_warehouse(location):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Inventory.sku, Products.name, Inventory.quantity
        FROM Inventory
        JOIN Products ON Inventory.sku = Products.sku
        WHERE Inventory.location = %s
    """, (location,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# LOGISTICS FUNCTIONS
def move_product(sku, origin, destination, quantity, transport_cost):
    conn = get_connection()
    cursor = conn.cursor()

    sku = sku.strip().upper()
    origin = origin.strip()
    destination = destination.strip()

    cursor.execute("SELECT quantity FROM Inventory WHERE sku = %s AND location = %s", (sku, origin))
    result = cursor.fetchone()
    if not result or result[0] < quantity:
        conn.rollback()
        cursor.close()
        conn.close()
        raise Exception("Insufficient stock at origin")

    cursor.execute("UPDATE Inventory SET quantity = quantity - %s WHERE sku = %s AND location = %s",
                   (quantity, sku, origin))

    cursor.execute("SELECT quantity FROM Inventory WHERE sku = %s AND location = %s", (sku, destination))
    if cursor.fetchone():
        cursor.execute("UPDATE Inventory SET quantity = quantity + %s WHERE sku = %s AND location = %s",
                       (quantity, sku, destination))
    else:
        cursor.execute("INSERT INTO Inventory (sku, location, quantity) VALUES (%s, %s, %s)",
                       (sku, destination, quantity))

    cursor.execute("INSERT INTO Logistics (sku, origin, destination, transport_cost) VALUES (%s, %s, %s, %s)",
                   (sku, origin, destination, transport_cost))

    conn.commit()
    write_log(1, f"Moved {quantity} of {sku} from {origin} to {destination} (₹{transport_cost:.2f})")
    cursor.close()
    conn.close()


def get_route_cost(origin, destination):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cost FROM Routes WHERE origin = %s AND destination = %s
    """, (origin, destination))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

# ORDER FUNCTIONS
def place_order(sku, quantity, customer_name, customer_location):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Orders (sku, quantity, customer_name, customer_location, status)
        VALUES (%s, %s, %s, %s, 'Pending')
    """, (sku, quantity, customer_name, customer_location))
    conn.commit()
    cursor.close()
    conn.close()

def get_orders(username=None, role="Admin"):
    conn = get_connection()
    cursor = conn.cursor()
    if role == "User":
        cursor.execute("""
            SELECT order_id, sku, quantity, customer_name, customer_location, status
            FROM Orders
            WHERE customer_name = %s
            ORDER BY order_id DESC
        """, (username,))
    else:
        cursor.execute("""
            SELECT order_id, sku, quantity, customer_name, customer_location, status
            FROM Orders
            ORDER BY order_id DESC
        """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results



def update_order_status(order_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Orders SET status = %s WHERE order_id = %s
    """, (status, order_id))
    conn.commit()
    cursor.close()
    conn.close()

# FORECAST FUNCTIONS
def get_forecast():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sku, forecast_value, forecast_date FROM DemandForecast
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def add_forecast(sku, forecast_value, forecast_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO DemandForecast (sku, forecast_value, forecast_date)
        VALUES (%s, %s, %s)
    """, (sku, forecast_value, forecast_date))
    conn.commit()
    write_log(1, f"Forecasted {forecast_value} units of {sku} for {forecast_date}")
    cursor.close()
    conn.close()

def get_inventory_for_sku(sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT location, quantity FROM Inventory
        WHERE sku = %s AND quantity > 0
        ORDER BY quantity DESC
    """, (sku,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_cheapest_route(origin, destination):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cost FROM Routes
        WHERE origin = %s AND destination = %s
        ORDER BY cost ASC LIMIT 1
    """, (origin, destination))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def fulfill_order(order_id, sku, quantity):
    inventory_sources = get_inventory_for_sku(sku)
    for location, available_qty in inventory_sources:
        move_qty = min(quantity, available_qty)
        cost = get_cheapest_route(location, "Customer")
        if cost is None:
            continue  # Skip if no route

        move_product(sku, location, "Customer", move_qty, cost)
        quantity -= move_qty
        if quantity <= 0:
            break

def delete_order(order_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Orders WHERE order_id = %s", (order_id,))
    conn.commit()
    cursor.close()
    conn.close()

def place_order(sku, quantity, customer_name, customer_location):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Orders (sku, quantity, customer_name, customer_location, status)
        VALUES (%s, %s, %s, %s, 'Pending')
    """, (sku, quantity, customer_name, customer_location))
    conn.commit()
    cursor.close()
    conn.close()

def move_order_to_customer(order_id, sku, quantity, origin, destination):
    cost_per_unit = get_route_cost(origin, destination)
    if cost_per_unit is None:
        raise Exception("No route found")
    total_cost = cost_per_unit * quantity
    move_product(sku, origin, destination, quantity, total_cost)
    write_log(1, f"Moved order #{order_id}: {quantity} of {sku} from {origin} to {destination}")

def get_all_warehouse_locations():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT location FROM Inventory")
    results = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results

def get_valid_origins_for_destination(destination, sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT r.origin
        FROM Routes r
        JOIN Inventory i ON r.origin = i.location
        WHERE r.destination = %s AND i.sku = %s AND i.quantity > 0
    """, (destination, sku))
    results = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results

def get_customer_locations():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT destination FROM Routes WHERE destination LIKE 'Retail Hub%'")
    results = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results

def get_inventory_locations_for_sku(sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT location FROM Inventory WHERE sku = %s", (sku,))
    results = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results

def get_locations():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT origin FROM Routes")
    origins = [row[0] for row in cursor.fetchall() if not row[0].startswith("Retail Hub")]
    cursor.execute("SELECT DISTINCT destination FROM Routes")
    destinations = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return origins, destinations

def get_inventory_for_forecast(sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(quantity) FROM Inventory WHERE sku = %s", (sku,))
    result = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return result or 0

def get_cheapest_route_details(origin, destination):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cost, distance_km FROM Routes
        WHERE origin = %s AND destination = %s
        ORDER BY cost ASC LIMIT 1
    """, (origin, destination))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return {"cost": result[0], "distance": result[1]} if result else None

def generate_summary_report():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Orders WHERE status = 'Processed'")
    processed_orders = cursor.fetchone()[0]

    cursor.execute("""
        SELECT DISTINCT i.sku
        FROM Inventory i
        JOIN Products p ON i.sku = p.sku
        WHERE i.quantity < p.threshold AND i.location NOT LIKE 'Retail Hub%'
    """)
    low_stock_skus = cursor.fetchall()
    low_stock_items = len(low_stock_skus)

    cursor.execute("SELECT SUM(transport_cost) FROM Logistics")
    total_logistics_cost = cursor.fetchone()[0] or 0

    cursor.close()
    conn.close()

    return {
        "Total Orders": total_orders,
        "Processed Orders": processed_orders,
        "Low Stock Items": low_stock_items,
        "Total Logistics Cost": total_logistics_cost
    }


def write_log(user_id, action):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Logs (user_id, action) VALUES (%s, %s)", (user_id, action))
    conn.commit()
    cursor.close()
    conn.close()

def suggest_cheapest_origin(sku, destination):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.location, r.cost
        FROM Inventory i
        JOIN Routes r ON i.location = r.origin AND r.destination = %s
        WHERE i.sku = %s AND i.quantity > 0 AND i.location NOT LIKE 'Retail Hub%'
        ORDER BY r.cost ASC
        LIMIT 1
    """, (destination, sku))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return {"origin": result[0], "cost": result[1]} if result else None

def get_logistics_records():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sku, origin, destination, transport_cost
        FROM Logistics
        ORDER BY logistics_id DESC
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_logs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, action
        FROM Logs
        ORDER BY log_id DESC
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def reset_simulation():
    conn = get_connection()
    cursor = conn.cursor()

    # Clear dynamic tables in dependency-safe order
    cursor.execute("DELETE FROM Orders")
    cursor.execute("DELETE FROM Logistics")
    cursor.execute("DELETE FROM DemandForecast")
    cursor.execute("DELETE FROM Reports")
    cursor.execute("DELETE FROM Logs")
    cursor.execute("DELETE FROM Inventory")
    cursor.execute("DELETE FROM Products")
    cursor.execute("DELETE FROM Routes")
    cursor.execute("DELETE FROM Users")

    # Reset AUTO_INCREMENT counters
    cursor.execute("ALTER TABLE Users AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE Orders AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE Logistics AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE DemandForecast AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE Reports AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE Logs AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE Inventory AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE Routes AUTO_INCREMENT = 1")

    # Reinsert Users
    cursor.execute("INSERT INTO Users (username, password, role) VALUES (%s, %s, %s)", ('admin1', 'adminpass123', 'Admin'))
    cursor.execute("INSERT INTO Users (username, password, role) VALUES (%s, %s, %s)", ('user1', 'userpass123', 'User'))

    # Reinsert Products
    products = [
        ('SKU001', 'Laptop', 'High-performance laptop', 5),
        ('SKU002', 'Smartphone', 'Latest model smartphone', 10),
        ('SKU003', 'Router', 'Dual-band WiFi router', 8)
    ]
    cursor.executemany(
        "INSERT INTO Products (sku, name, description, threshold) VALUES (%s, %s, %s, %s)",
        products
    )

    # Reinsert Inventory
    inventory = [
        ('SKU001', 'Warehouse A', 20),
        ('SKU002', 'Warehouse B', 15),
        ('SKU003', 'Warehouse A', 5)
    ]
    cursor.executemany(
        "INSERT INTO Inventory (sku, location, quantity) VALUES (%s, %s, %s)",
        inventory
    )

    # Reinsert Routes
    routes = [
        ('Warehouse A', 'Retail Hub 1', 150.00, 25.5),
        ('Warehouse A', 'Retail Hub 2', 120.00, 5.0),
        ('Warehouse A', 'Retail Hub 3', 90.00, 10.0),
        ('Warehouse B', 'Retail Hub 1', 70.00, 15.0),
        ('Warehouse B', 'Retail Hub 2', 100.00, 25.0),
        ('Warehouse B', 'Retail Hub 3', 175.00, 30.0),
        ('Warehouse B', 'Warehouse A', 80.00, 20.0),
        ('Warehouse A', 'Warehouse B', 100.00, 30.0)
    ]
    cursor.executemany(
        "INSERT INTO Routes (origin, destination, cost, distance_km) VALUES (%s, %s, %s, %s)",
        routes
    )

    # Commit all inserts before logging
    conn.commit()

    # Log the reset action (user_id 1 must exist now)
    write_log(1, "Simulation reset to initial state")

    cursor.close()
    conn.close()

def validate_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, role FROM Users WHERE username = %s AND password = %s", (username, password))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return {"user_id": result[0], "role": result[1]}
    return None

def create_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Users (username, password, role)
        VALUES (%s, %s, 'User')
    """, (username, password))
    conn.commit()
    cursor.close()
    conn.close()




