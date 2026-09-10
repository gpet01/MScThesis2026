import time
import random
import statistics
import mysql.connector
import redis
from datetime import date, timedelta

# Configuration
NUM_WRITE_OPS = 50000
WARMUP = 5
START_ORDER_ID = 2_000_000
WARMUP_ORDER_ID = 3_000_000
NUM_USERS = 1000

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

# ------
# Data preparation
# ------
orders_data = [
    (START_ORDER_ID + i, random.randint(1, NUM_USERS), str(date(2025,1,1)))
    for i in range(NUM_WRITE_OPS)
]

warmup_data = [
    (WARMUP_ORDER_ID + i, random.randint(1, NUM_USERS), str(date(2025,1,1)))
    for i in range(WARMUP)
]

# ----------------------
# MySQL Benchmark Insert
# ----------------------

def mysql_insert():
    # Warmup
    for order_id, user_id, order_date in warmup_data:
        cursor.execute(
            "INSERT INTO orders (id, user_id, order_date) VALUES (%s, %s, %s)",
            (order_id, user_id, order_date)
        )
        mysql_conn.commit()

    # Κανονικές μετρήσεις
    times = []
    for order_id, user_id, order_date in orders_data:
        start = time.perf_counter()
        cursor.execute(
            "INSERT INTO orders (id, user_id, order_date) VALUES (%s, %s, %s)",
            (order_id, user_id, order_date)
        )
        mysql_conn.commit()
        times.append((time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)

# ---------------------------
# MySQL Benchmarks - DELETE
# ---------------------------
def mysql_delete():
    # Warmup - διαγραφή των εγγραφών που έμειναν από το mysql_insert()
    for order_id, _, _ in warmup_data:
        cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        mysql_conn.commit()

    # Κανονικές μετρήσεις
    times = []
    for order_id, _, _ in orders_data:
        start = time.perf_counter()
        cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        mysql_conn.commit()
        times.append((time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)