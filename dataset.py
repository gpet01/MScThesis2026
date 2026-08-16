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

# Products
product_data = [
    (
        i,
        f"Product{i}",
        random.randint(1, len(categories)),
        round(random.uniform(10, 2500), 2)
    )
    for i in range(1, NUM_PRODUCTS + 1)
]

insert_in_batches(
    cursor,
    "INSERT INTO products (id, name, category_id, price) VALUES (%s, %s, %s, %s)",
    product_data
)

db.commit()

#Orders
start_date = date(2025, 1, 1)

order_data = [
    (
        i,
        random.randint(1, NUM_USERS),
        start_date + timedelta(days=random.randint(0, 450))
    )
    for i in range(1, NUM_ORDERS + 1)
]

insert_in_batches(
    cursor,
    "INSERT INTO orders (id, user_id, order_date) VALUES (%s, %s, %s)",
    order_data
)

db.commit()

#Order items

order_item_data = []
order_item_id = 1

for order_id in range(1, NUM_ORDERS + 1):
    num_items = random.randint(MIN_ITEMS_PER_ORDER, MAX_ITEMS_PER_ORDER)
    chosen_products = random.sample(range(1, NUM_PRODUCTS + 1), num_items)

    for product_id in chosen_products:
        order_item_data.append((
            order_item_id,
            order_id,
            product_id,
            random.randint(1, 3)
        ))
        order_item_id += 1

insert_in_batches(
    cursor,
    "INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (%s, %s, %s, %s)",
    order_item_data,
    batch_size=500
)

db.commit()

print("Dataset is ready!")
print(f"Users: {len(user_data)}")
print(f"Categories: {len(category_data)}")
print(f"Products: {len(product_data)}")
print(f"Orders: {len(order_data)}")
print(f"Order items: {len(order_item_data)}")

cursor.close()
db.close()