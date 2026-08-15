import random
from datetime import date, timedelta
import mysql.connector

NUM_USERS = 1000
NUM_PRODUCTS = 300
NUM_ORDERS = 1_000_000
MIN_ITEMS_PER_ORDER = 2
MAX_ITEMS_PER_ORDER = 5

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="thesis2026"
)

cursor = db.cursor()


def insert_in_batches(cursor, query, data, batch_size=1000):
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        cursor.executemany(query,batch)

#Reset Tables
cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
cursor.execute("TRUNCATE TABLE order_items")
cursor.execute("TRUNCATE TABLE orders")
cursor.execute("TRUNCATE TABLE products")
cursor.execute("TRUNCATE TABLE categories")
cursor.execute("TRUNCATE TABLE users")
cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
db.commit()

#Categories
categories = [
    "Laptops", "Phones", "Accessories", "Monitors", "Storage",
    "Audio", "Gaming", "Networking", "Smart Home", "Peripherals"
]

category_data = [(i + 1, categories[i]) for i in range(len(categories))]
insert_in_batches(
    cursor,
    "INSERT INTO categories (id, name) VALUES (%s, %s)",
    category_data
)
db.commit()


#Users
user_data = [
    (i, f"User{i}", random.randint(18,65), f"user{i}@example.com")
    for i in range(1, NUM_USERS + 1)
]

insert_in_batches(
    cursor,
    "INSERT INTO users(id, name, age, email) VALUES (%s, %s, %s, %s)",
    user_data
)

db.commit()

cursor.close()
db.close()