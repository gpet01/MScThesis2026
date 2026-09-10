import time
import random
import statistics
import mysql.connector
import redis
from datetime import date, timedelta

# ---------------------------
# Configuration
# ---------------------------
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
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# ---------------------------
# Προετοιμασία δεδομένων εισαγωγής
# ---------------------------
orders_data = [
    (START_ORDER_ID + i, random.randint(1, NUM_USERS), str(date(2025, 1, 1) + timedelta(days=i % 365)))
    for i in range(NUM_WRITE_OPS)
]

warmup_data = [
    (WARMUP_ORDER_ID + i, random.randint(1, NUM_USERS), str(date(2025, 1, 1) + timedelta(days=i % 365)))
    for i in range(WARMUP)
]

# ---------------------------
# MySQL Benchmarks - INSERT
# ---------------------------
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

# ---------------------------
# Redis Benchmarks - INSERT
# ---------------------------
def redis_insert():
    # Warmup
    for order_id, user_id, order_date in warmup_data:
        r.hset(f"order:{order_id}", mapping={
            "user_id": user_id,
            "order_date": order_date
        })
        r.rpush(f"user:{user_id}:orders", str(order_id))
        r.delete(f"order:{order_id}")
        r.lrem(f"user:{user_id}:orders", 0, str(order_id))

    # Κανονικές μετρήσεις
    times = []
    for order_id, user_id, order_date in orders_data:
        start = time.perf_counter()
        r.hset(f"order:{order_id}", mapping={
            "user_id": user_id,
            "order_date": order_date
        })
        r.rpush(f"user:{user_id}:orders", str(order_id))
        times.append((time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)

# ---------------------------
# Redis Benchmarks - DELETE
# ---------------------------
def redis_delete():
    # Warmup
    for order_id, user_id, order_date in warmup_data:
        r.hset(f"order:{order_id}", mapping={
            "user_id": user_id,
            "order_date": order_date
        })
        r.rpush(f"user:{user_id}:orders", str(order_id))
        r.delete(f"order:{order_id}")
        r.lrem(f"user:{user_id}:orders", 0, str(order_id))

    # Κανονικές μετρήσεις
    times = []
    for order_id, user_id, _ in orders_data:
        start = time.perf_counter()
        r.delete(f"order:{order_id}")
        r.lrem(f"user:{user_id}:orders", 0, str(order_id))
        times.append((time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)

# ---------------------------
# Εκτέλεση Benchmarks
# ---------------------------
print(f"Εκτέλεση benchmark εισαγωγής {NUM_WRITE_OPS} παραγγελιών...")
mysql_ins = mysql_insert()
redis_ins = redis_insert()

print(f"Εκτέλεση benchmark διαγραφής {NUM_WRITE_OPS} παραγγελιών...")
mysql_del = mysql_delete()
redis_del = redis_delete()

# ---------------------------
# Αποτελέσματα
# ---------------------------
print("\n=== Αποτελέσματα Write Benchmark (μέσος χρόνος ανά εγγραφή) ===")
print(f"{'Λειτουργία':<30} {'MySQL (ms)':<25} {'Redis (ms)':<25}")
print("-" * 80)
print(f"{'INSERT order':<30} {mysql_ins[0]:.3f} ± {mysql_ins[1]:.3f}          {redis_ins[0]:.3f} ± {redis_ins[1]:.3f}")
print(f"{'DELETE order':<30} {mysql_del[0]:.3f} ± {mysql_del[1]:.3f}          {redis_del[0]:.3f} ± {redis_del[1]:.3f}")

cursor.close()
mysql_conn.close()
r.close()