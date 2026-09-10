
import time
import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def wait_for_index(name):
    """Περιμένει να ολοκληρωθεί το indexing"""
    while True:
        info = r.execute_command("FT.INFO", name)
        d = dict(zip(info[::2], info[1::2]))
        if float(d.get("percent_indexed", 1)) >= 1 and int(d.get("indexing", 0)) == 0:
            return
        time.sleep(0.5)


def drop_index(name):
    try:
        r.execute_command("FT.DROPINDEX", name)
    except redis.ResponseError:
        pass


# ---------- 1) Δημιουργία ευρετηρίων στα hashes ----------
drop_index("product_idx")
drop_index("order_idx")

r.execute_command(
    "FT.CREATE", "product_idx", "ON", "HASH", "PREFIX", "1", "product:",
    "SCHEMA", "name", "TEXT", "price", "NUMERIC", "SORTABLE", "category", "TAG",
)
r.execute_command(
    "FT.CREATE", "order_idx", "ON", "HASH", "PREFIX", "1", "order:",
    "SCHEMA", "user_id", "TAG",
)
print("Ευρετήρια product_idx, order_idx δημιουργήθηκαν. Αναμονή indexing...")
wait_for_index("product_idx")
wait_for_index("order_idx")
print("Το indexing ολοκληρώθηκε.\n")


def show(title, *cmd):
    print("=" * 70)
    print(title)
    print("Εντολή:", " ".join(str(c) for c in cmd))
    print("-" * 70)
    res = r.execute_command(*cmd)
    # res[0] = πλήθος γραμμών που επιστράφηκαν, μετά ζεύγη πεδίων ανά ομάδα
    groups = res[1:]
    for row in groups[:10]:  # Είναι οι 10 πρώτες γραμμές
        print(dict(zip(row[::2], row[1::2])))
    if len(groups) > 10:
        print(f"... (εμφανίζονται 10 από {len(groups)} ομάδες)")
    print()


# ---------- 2) Τρία aggregation queries  ----------
show("Πλήθος παραγγελιών ανά χρήστη  (SQL: COUNT(*) GROUP BY user_id)",
     "FT.AGGREGATE", "order_idx", "*",
     "GROUPBY", "1", "@user_id",
     "REDUCE", "COUNT", "0", "AS", "order_count")

show("Συνολική αξία προϊόντων ανά κατηγορία  (SQL: SUM(price) GROUP BY category)",
     "FT.AGGREGATE", "product_idx", "*",
     "GROUPBY", "1", "@category",
     "REDUCE", "SUM", "1", "@price", "AS", "total_price")

show("Μέση τιμή ανά κατηγορία  (SQL: AVG(price) GROUP BY category)",
     "FT.AGGREGATE", "product_idx", "*",
     "GROUPBY", "1", "@category",
     "REDUCE", "AVG", "1", "@price", "AS", "avg_price")

r.close()