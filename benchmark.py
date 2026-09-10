import time
import random
import statistics

import mysql.connector
import redis


REPEATS = 100
WARMUP = 5
NUM_USERS = 1000
NUM_ORDERS = 1_000_000
CATEGORY_NAME = "Laptops"

mysql_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="thesis2026"
)

cursor = mysql_conn.cursor(dictionary=True)

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
    )

#---------------------
# MySQL Benchmarks
#---------------------

def avg_mysql_users():
    for _ in range(WARMUP):
        cursor.execute("SELECT * FROM users WHERE id = %s", (random.randint(1, NUM_USERS),))
        cursor.fetchall()
    times = []
    for _ in range(REPEATS):
        user_id = random.randint(1, NUM_USERS)
        start = time.perf_counter()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        cursor.fetchall()
        times.append((time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)

def avg_mysql_order():
    for _ in range(WARMUP):
        cursor.execute("SELECT * FROM orders WHERE id = %s", (random.randint(1, NUM_ORDERS),))
        cursor.fetchall()
    times = []
    for _ in range(REPEATS):
        order_id = random.randint(1, NUM_ORDERS)
        start = time.perf_counter()
        cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
        cursor.fetchall()
        times.append((time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)


def avg_mysql_order_items():
    for _ in range(WARMUP):
        cursor.execute("""
            SELECT p.name
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (random.randint(1, NUM_ORDERS),)
        )
        cursor.fetchall()
    times = []
    for _ in range(REPEATS):
        order_id = random.randint(1, NUM_ORDERS)
        start = time.perf_counter()
        cursor.execute("""
            SELECT p.name
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (order_id,) )
        cursor.fetchall()
        times.append( (time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)


def avg_mysql_category():
    for _ in range(WARMUP):
        cursor.execute("""
            SELECT p.id
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE c.name = %s
        """, (CATEGORY_NAME,))
        cursor.fetchall()
    times = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        cursor.execute("""
            SELECT p.id
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE c.name = %s
        """, (CATEGORY_NAME,))
        cursor.fetchall()
        times.append((time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)


def avg_mysql_price_range():
    for _ in range(WARMUP):
        cursor.execute("""
            SELECT p.id, p.name, p.price
            FROM products p
            WHERE p.price BETWEEN 100 AND 500
        """)
        cursor.fetchall()
    times = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        cursor.execute("""
            SELECT p.id, p.name, p.price
            FROM products p
            WHERE p.price BETWEEN 100 AND 500
        """)
        cursor.fetchall()
        times.append((time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)


# -------------------------
# Redis Benchmarks
# -------------------------


def avg_redis_user():
    for _ in range(WARMUP):
        r.hgetall(f"user:{random.randint(1, NUM_USERS)}")
    times = []
    for _ in range(REPEATS):
        user_id = random.randint(1, NUM_USERS)
        start = time.perf_counter()
        r.hgetall(f"user:{user_id}")
        times.append( (time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)

def avg_redis_order():
    for _ in range(WARMUP):
        r.hgetall(f"order:{random.randint(1, NUM_ORDERS)}")
    times = []
    for _ in range(REPEATS):
        order_id = random.randint(1, NUM_ORDERS)
        start = time.perf_counter()
        r.hgetall(f"order:{order_id}")
        times.append((time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)


def avg_redis_order_items():
    for _ in range(WARMUP):
        r.lrange(f"order:{random.randint(1, NUM_ORDERS)}:items", 0, -1)
    times = []
    for _ in range(REPEATS):
        order_id = random.randint(1, NUM_ORDERS)
        start = time.perf_counter()
        r.lrange(f"order:{order_id}:items", 0, -1)
        times.append( (time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)

def avg_redis_category():
    for _ in range(WARMUP):
        r.smembers(f"category:{CATEGORY_NAME}:products")
    times = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        r.smembers(f"category:{CATEGORY_NAME}:products")
        times.append((time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)


def avg_redis_price_range():
    for _ in range(WARMUP):
        r.zrange("products:by_price", 100, 500, byscore=True)
    times = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        r.zrange("products:by_price", 100, 500, byscore=True)
        times.append((time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)

#--------------------------
# Run Benchmarks
#--------------------------

mysql_user = avg_mysql_users()
mysql_order = avg_mysql_order()
mysql_items = avg_mysql_order_items()
mysql_category = avg_mysql_category()
mysql_price = avg_mysql_price_range()

redis_user = avg_redis_user()
redis_order = avg_redis_order()
redis_items = avg_redis_order_items()
redis_category = avg_redis_category()
redis_price = avg_redis_price_range()




#---------------------------
# Print Results
#---------------------------

print("\n=== MySQL Average Response Times (mean ± stdev) ===")
print(f"User retrieval: {mysql_user[0]:.3f} ms ± {mysql_user[1]:.3f} ms")
print(f"Order retrieval: {mysql_order[0]:.3f} ms ± {mysql_order[1]:.3f} ms")
print(f"Order items retrieval: {mysql_items[0]:.3f} ms ± {mysql_items[1]:.3f} ms")
print(f"Products by category ({CATEGORY_NAME}): {mysql_category[0]:.3f} ms ± {mysql_category[1]:.3f} ms")
print(f"Products by price range (100-500): {mysql_price[0]:.3f} ms ± {mysql_price[1]:.3f} ms")

print("\n=== Redis Average Response Times (mean ± stdev) ===")
print(f"User retrieval: {redis_user[0]:.3f} ms ± {redis_user[1]:.3f} ms")
print(f"Order retrieval: {redis_order[0]:.3f} ms ± {redis_order[1]:.3f} ms")
print(f"Order items retrieval: {redis_items[0]:.3f} ms ± {redis_items[1]:.3f} ms")
print(f"Products by category ({CATEGORY_NAME}): {redis_category[0]:.3f} ms ± {redis_category[1]:.3f} ms")
print(f"Products by price range (100-500): {redis_price[0]:.3f} ms ± {redis_price[1]:.3f} ms")

cursor.close()
mysql_conn.close()
r.close()