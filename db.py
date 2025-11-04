# db.py
import sqlite3
from datetime import datetime
import binascii, hashlib

DB_PATH = "data/estoque.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ------ senha ------
def verify_password(stored_hash_hex, stored_salt_hex, password_attempt: str):
    salt = binascii.unhexlify(stored_salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password_attempt.encode("utf-8"), salt, 200_000)
    return binascii.hexlify(dk).decode() == stored_hash_hex

# ------ usuários ------
def get_user_by_username(username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row

def create_user(username, password_hash_hex, salt_hex, role="common"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, password_hash, salt, role, created_at) VALUES (?, ?, ?, ?, ?)",
                (username, password_hash_hex, salt_hex, role, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def list_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role, created_at FROM users ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_user_by_id(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# ------ produtos ------
def create_product(name, description, quantity, unit_price, created_by=None):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute("""
        INSERT INTO products (name, description, quantity, unit_price, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, description, quantity, unit_price, created_by, now))
    conn.commit()
    conn.close()

def update_product(prod_id, name, description, quantity, unit_price):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute("""
        UPDATE products
        SET name = ?, description = ?, quantity = ?, unit_price = ?, updated_at = ?
        WHERE id = ?
    """, (name, description, quantity, unit_price, now, prod_id))
    conn.commit()
    conn.close()

def delete_product(prod_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (prod_id,))
    conn.commit()
    conn.close()

def list_products():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_product_by_id(prod_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id = ?", (prod_id,))
    row = cur.fetchone()
    conn.close()
    return row
