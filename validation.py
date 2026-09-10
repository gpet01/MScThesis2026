import random

import mysql.connector
import redis

from dataset import product_id

# ---------------------------
# Configuration
# ---------------------------
NUM_USERS = 1000
NUM_ORDERS = 1_000_000
CATEGORY_NAME = "Laptops"
PRICE_MIN = 100
PRICE_MAX = 500
SAMPLE_SIZE = 200


mysql_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="thesis"
)
cursor = mysql_conn.cursor(dictionary=True)

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

results = []  # (όνομα σεναρίου, success, λεπτομέρεια)


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" -> {detail}" if detail else ""))


# ---------------------------
# 1. Ανάκτηση χρήστη (HGETALL user:id)
# ---------------------------
def validate_user():
    ok = True
    bad = None
    for _ in range(SAMPLE_SIZE):
        uid = random.randint(1, NUM_USERS)
        cursor.execute("SELECT name, age, email FROM users WHERE id = %s", (uid,))
        row = cursor.fetchone()
        h = r.hgetall(f"user:{uid}")
        sql_view = (str(row["name"]), str(row["age"]), str(row["email"]))
        redis_view = (h.get("name"), h.get("age"), h.get("email"))
        if sql_view != redis_view:
            ok = False
            bad = (uid, sql_view, redis_view)
            break
    record("Ανάκτηση χρήστη", ok, "" if ok else f"id={bad[0]} MySQL={bad[1]} Redis={bad[2]}")


# ---------------------------
# 2. Ανάκτηση παραγγελίας (HGETALL order:id)
# ---------------------------
def validate_order():
    ok = True
    bad = None
    for _ in range(SAMPLE_SIZE):
        oid = random.randint(1, NUM_ORDERS)
        cursor.execute("SELECT user_id, order_date FROM orders WHERE id = %s", (oid,))
        row = cursor.fetchone()
        h = r.hgetall(f"order:{oid}")
        sql_view = (str(row["user_id"]), str(row["order_date"]))
        redis_view = (h.get("user_id"), h.get("order_date"))
        if sql_view != redis_view:
            ok = False
            bad = (oid, sql_view, redis_view)
            break
    record("Ανάκτηση παραγγελίας", ok, "" if ok else f"id={bad[0]} MySQL={bad[1]} Redis={bad[2]}")


# ---------------------------
# 3. Παραγγελίες χρήστη (LRANGE user:id:orders)
# ---------------------------
def validate_user_orders():
    ok = True
    bad = None
    for _ in range(SAMPLE_SIZE):
        uid = random.randint(1, NUM_USERS)
        cursor.execute("SELECT id FROM orders WHERE user_id = %s", (uid,))
        sql_ids = {str(row["id"]) for row in cursor.fetchall()}
        redis_ids = set(r.lrange(f"user:{uid}:orders", 0, -1))
        if sql_ids != redis_ids:
            ok = False
            bad = (uid, len(sql_ids), len(redis_ids))
            break
    record("Παραγγελίες χρήστη", ok, "" if ok else f"id={bad[0]} MySQL_count={bad[1]} Redis_count={bad[2]}")


# ---------------------------
# 4. Προϊόντα παραγγελίας (LRANGE order:id:items)
#    Redis: "ProductName (qty: q)" -> συγκρίνουμε το multiset των ονομάτων
# ---------------------------
def validate_order_items():
    ok = True
    bad = None
    for _ in range(SAMPLE_SIZE):
        oid = random.randint(1, NUM_ORDERS)
        cursor.execute(
            """
            SELECT p.name
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
            """,
            (oid,),
        )
        sql_names = sorted(row["name"] for row in cursor.fetchall())
        redis_names = sorted(
            item.rsplit(" (qty:", 1)[0]
            for item in r.lrange(f"order:{oid}:items", 0, -1)
        )
        if sql_names != redis_names:
            ok = False
            bad = (oid, sql_names, redis_names)
            break
    record("Προϊόντα παραγγελίας", ok, "" if ok else f"id={bad[0]} MySQL={bad[1]} Redis={bad[2]}")


# ---------------------------
# 5. Προϊόντα ανά κατηγορία (SMEMBERS category:name:products)
# ---------------------------
def validate_category():
    cursor.execute(
        """
        SELECT p.id
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE c.name = %s
        """,
        (CATEGORY_NAME,),
    )
    sql_ids = {str(row["id"]) for row in cursor.fetchall()}
    redis_ids = set(r.smembers(f"category:{CATEGORY_NAME}:products"))
    ok = sql_ids == redis_ids
    record(
        f"Προϊόντα ανά κατηγορία ({CATEGORY_NAME})",
        ok,
        "" if ok else f"MySQL={len(sql_ids)} Redis={len(redis_ids)} diff={sql_ids ^ redis_ids}",
    )


# ---------------------------
# 6. Προϊόντα ανά εύρος τιμής (ZRANGE products:by_price min max BYSCORE)
# ---------------------------
def validate_price_range():
    cursor.execute(
        "SELECT id FROM products WHERE price BETWEEN %s AND %s",
        (PRICE_MIN, PRICE_MAX),
    )
    sql_ids = {str(row["id"]) for row in cursor.fetchall()}
    redis_ids = set(
        r.zrange("products:by_price", PRICE_MIN, PRICE_MAX, byscore=True)
    )
    ok = sql_ids == redis_ids
    record(
        "Προϊόντα ανά εύρος τιμής",
        ok,
        "" if ok else f"MySQL={len(sql_ids)} Redis={len(redis_ids)} diff={sql_ids ^ redis_ids}",
    )


# ---------------------------
# Εκτέλεση
# ---------------------------
if __name__ == "__main__":
    print(" Έλεγχος ισοδυναμίας αποτελεσμάτων MySQL vs Redis \n")

    validate_user()
    validate_order()
    validate_user_orders()
    validate_order_items()
    validate_category()
    validate_price_range()

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n Σύνολο: {passed}/{total} σενάρια πέρασαν")

    cursor.close()
    mysql_conn.close()
    r.close()


    if passed != total:
        raise SystemExit(1)