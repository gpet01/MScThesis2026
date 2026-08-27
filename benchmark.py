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


#--------------------------
# Run Benchmarks
#--------------------------

mysql_user = avg_mysql_users()





#---------------------------
# Print Results
#---------------------------

print("\n=== MySQL Average Response Times (mean ±stdev) ===")
print(f"User retrieval: {mysql_user[0]:.3f} ms ± {mysql_user[1]:.3f} ms")