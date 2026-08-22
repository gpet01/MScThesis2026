import mysql.connector
import redis

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="thesis2026"
)

cursor = db.cursor(dictionary=True)

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

#Reset redis everytime ETL runs
r.flushdb()

#Users
cursor.execute("SELECT * FROM users")
for user in cursor.fetchall():
    r.hset(f"user:{user['id']}", mapping={
        "name": user["name"],
        "age": user["age"],
        "email": user["email"]
    })

#Products

cursor.execute("""
SELECT p.id, p.name, p.price, c.name AS category
FROM products p
JOIN categories c ON p.category_id = c.id
"""
)

for product in cursor.fetchall():
    r.hset(f"product:{product['id']}", mapping={
        "name": product["name"],
        "price": float(product["price"]),
        "category": product["category"]
    })

    #Secondary index for category, set
    r.sadd(f"category:{product['category']}:products", product['id'])

    #Secondary index for price range queries, sorted set
    r.zadd("products:by_price", {
        str(product["id"]): float(product["price"])
    })