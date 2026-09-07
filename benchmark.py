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




# -------------------------
# Redis Benchmarks
# -------------------------


#--------------------------
# Run Benchmarks
#--------------------------

mysql_user = avg_mysql_users()
mysql_order = avg_mysql_order()
mysql_items = avg_mysql_order_items()





#---------------------------
# Print Results
#---------------------------

print("\n=== MySQL Average Response Times (mean ±stdev) ===")
print(f"User retrieval: {mysql_user[0]:.3f} ms ± {mysql_user[1]:.3f} ms")
print(f"Order retrieval: {mysql_order[0]:.3f} ms ± {mysql_order[1]:.3f} ms")
print(f"Order items retrieval: {mysql_items[0]:.3f} ms ± {mysql_items[1]:.3f} ms")