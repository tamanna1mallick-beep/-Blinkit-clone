# main.py - Blinkit AI Engine (COD Version - No Razorpay)
import sqlite3
import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Blinkit AI Engine - COD")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# COD CONFIG (No Razorpay needed!)
# ============================================
COD_ENABLED = True

# ============================================
# DATABASE SETUP
# ============================================

def init_db():
    conn = sqlite3.connect("blinkit.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, price INTEGER,
                  delivery_time TEXT, image TEXT, category TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS cart
                 (product_id INTEGER, name TEXT, price INTEGER, quantity INTEGER)""")

    c.execute("""CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT)""")

    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            items TEXT NOT NULL,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'confirmed',
            payment_method TEXT DEFAULT 'cod',
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        products_data = [
            (1, "Apple", 120, "10 min delivery", "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=200", "Fruits"),
            (2, "Milk", 60, "10 min delivery", "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=200", "Dairy"),
            (3, "Bread", 40, "10 min delivery", "https://images.unsplash.com/photo-1509440159596-0df4bcaaa337?w=200", "Dairy"),
            (4, "Banana", 50, "10 min delivery", "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=200", "Fruits"),
            (5, "Eggs", 90, "10 min delivery", "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=200", "Dairy"),
            (6, "Tomato", 30, "10 min delivery", "https://images.unsplash.com/photo-1546094096-0df4bcaaa337?w=200", "Vegetables")
        ]
        c.executemany("INSERT INTO products VALUES (?,?,?,?,?,?)", products_data)

    conn.commit()
    conn.close()

init_db()

# ============================================
# DATABASE FUNCTIONS
# ============================================

def get_products_from_db():
    conn = sqlite3.connect("blinkit.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return products

def get_cart_from_db():
    conn = sqlite3.connect("blinkit.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM cart")
    cart = [dict(row) for row in c.fetchall()]
    conn.close()
    return cart

# ============================================
# PYDANTIC MODELS
# ============================================

class CartItem(BaseModel):
    product_id: int
    name: str
    price: int
    quantity: int = 1

class OrderItem(BaseModel):
    user_email: str
    items: list
    total_price: float

class ProductCreate(BaseModel):
    name: str
    price: int
    delivery_time: str
    image: str
    category: str

class OrderStatusUpdate(BaseModel):
    order_id: int
    status: str

# ============================================
# ROUTES
# ============================================

@app.get("/")
def home():
    return {
        "message": "Blinkit AI Engine is running! (COD Mode - No Payment Gateway)",
        "status": "active",
        "version": "2.0.0",
        "payment_mode": "Cash on Delivery"
    }

@app.get("/products")
def get_products():
    return {"products": get_products_from_db()}

@app.get("/products/search")
def search_products(query: str):
    conn = sqlite3.connect("blinkit.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE LOWER(name) LIKE ?", (f'%{query.lower()}%',))
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"products": products}

@app.get("/products/category/{category}")
def get_products_by_category(category: str):
    conn = sqlite3.connect("blinkit.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE LOWER(category) = ?", (category.lower(),))
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"products": products}

@app.get("/products/{product_id}")
def get_product(product_id: int):
    conn = sqlite3.connect("blinkit.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    conn.close()
    if product:
        return dict(product)
    return {"error": "Product not found"}

# ============================================
# CART
# ============================================

@app.get("/cart")
def get_cart():
    cart = get_cart_from_db()
    total = sum(item["price"] * item["quantity"] for item in cart)
    return {"cart": cart, "total": total, "count": len(cart)}

@app.post("/cart/add")
def add_to_cart(item: CartItem):
    conn = sqlite3.connect("blinkit.db")
    c = conn.cursor()
    c.execute("SELECT * FROM cart WHERE product_id = ?", (item.product_id,))
    existing = c.fetchone()
    if existing:
        c.execute("UPDATE cart SET quantity = quantity + 1 WHERE product_id = ?", (item.product_id,))
    else:
        c.execute("INSERT INTO cart VALUES (?,?,?,?)",
                  (item.product_id, item.name, item.price, item.quantity))
    conn.commit()
    c.execute("SELECT * FROM cart")
    cart = [dict(zip([column[0] for column in c.description], row)) for row in c.fetchall()]
    total = sum(i["price"] * i["quantity"] for i in cart)
    conn.close()
    return {"message": f"{item.name} added to cart!", "cart": cart, "total": total}

@app.delete("/cart/remove/{product_id}")
def remove_from_cart(product_id: int):
    conn = sqlite3.connect("blinkit.db")
    c = conn.cursor()
    c.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
    conn.commit()
    c.execute("SELECT * FROM cart")
    cart = [dict(zip([column[0] for column in c.description], row)) for row in c.fetchall()]
    total = sum(item["price"] * item["quantity"] for item in cart)
    conn.close()
    return {"message": "Item removed!", "cart": cart, "total": total}

@app.delete("/cart/clear")
def clear_cart():
    conn = sqlite3.connect("blinkit.db")
    c = conn.cursor()
    c.execute("DELETE FROM cart")
    conn.commit()
    conn.close()
    return {"message": "Cart cleared!"}

# ============================================
# AUTH
# ============================================

@app.post("/signup")
def signup(username: str, password: str):
    conn = sqlite3.connect("blinkit.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, password))
        conn.commit()
        conn.close()
        return {"message": "Signup successful!"}
    except sqlite3.IntegrityError:
        conn.close()
        return {"error": "Username already exists!"}

@app.post("/login")
def login(username: str, password: str):
    conn = sqlite3.connect("blinkit.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?",
              (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        return {"message": "Login successful!", "user": username}
    return {"error": "Invalid username or password!"}

# ============================================
# ORDERS WITH COD (NO RAZORPAY!)
# ============================================

@app.post("/create-order")
def create_order(order: OrderItem):
    conn = sqlite3.connect("blinkit.db")
    c = conn.cursor()
    items_json = json.dumps(order.items)
    
    # COD Order - directly confirmed, no payment needed!
    c.execute("INSERT INTO orders (user_email, items, total_price, status, payment_method) VALUES (?, ?, ?, ?, ?)",
              (order.user_email, items_json, order.total_price, "confirmed", "cod"))
    conn.commit()
    order_id = c.lastrowid
    conn.close()

    return {
        "status": "success",
        "message": "Order placed successfully! Cash on Delivery",
        "order_id": order_id,
        "amount": order.total_price,
        "payment_method": "cod",
        "delivery_message": "Pay Rs.{} when your order arrives!".format(order.total_price)
    }

@app.post("/update-order-status")
def update_order_status(update: OrderStatusUpdate):
    conn = sqlite3.connect("blinkit.db")
    c = conn.cursor()
    c.execute("UPDATE orders SET status = ? WHERE id = ?", (update.status, update.order_id))
    conn.commit()
    conn.close()
    return {
        "status": "success",
        "message": f"Order #{update.order_id} updated to {update.status}"
    }

@app.get("/order-history/{user_email}")
def get_order_history(user_email: str):
    conn = sqlite3.connect("blinkit.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE user_email = ? ORDER BY order_date DESC", (user_email,))
    orders = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"orders": orders}

# ============================================
# ADMIN APIs
# ============================================

@app.get("/admin/stats")
def admin_stats():
    conn = sqlite3.connect("blinkit.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM products")
    total_products = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders")
    total_orders = c.fetchone()[0]
    c.execute("SELECT SUM(total_price) FROM orders WHERE status != 'cancelled'")
    total_revenue = c.fetchone()[0] or 0
    conn.close()
    return {
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue
    }

@app.get("/admin/users")
def admin_users():
    conn = sqlite3.connect("blinkit.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, username FROM users")
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"users": users}

@app.get("/admin/orders")
def admin_orders():
    conn = sqlite3.connect("blinkit.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY order_date DESC")
    orders = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"orders": orders}

@app.post("/admin/products")
def admin_add_product(product: ProductCreate):
    conn = sqlite3.connect("blinkit.db")
    c = conn.cursor()
    c.execute("INSERT INTO products (name, price, delivery_time, image, category) VALUES (?, ?, ?, ?, ?)",
              (product.name, product.price, product.delivery_time, product.image, product.category))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return {"message": "Product added!", "id": new_id}

@app.delete("/admin/products/{product_id}")
def admin_delete_product(product_id: int):
    conn = sqlite3.connect("blinkit.db")
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return {"message": "Product deleted!"}

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)