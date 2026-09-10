
import time
import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def wait_for_index(name):
    while True:
        info = r.execute_command("FT.INFO", name)
        d = dict(zip(info[::2], info[1::2]))
        if float(d.get("percent_indexed", 1)) >= 1 and int(d.get("indexing", 0)) == 0:
            return
        time.sleep(0.3)


def drop(name):
    try:
        r.execute_command("FT.DROPINDEX", name)
    except redis.ResponseError:
        pass



drop("product_idx")
r.execute_command("FT.CREATE", "product_idx", "ON", "HASH", "PREFIX", "1", "product:",
                  "SCHEMA",
                  "name", "TEXT",
                  "price", "NUMERIC", "SORTABLE",
                  "category", "TAG")
print("FT.CREATE product_idx ... name TEXT, price NUMERIC SORTABLE, category TAG")
print("-> ένα ευρετήριο με 3 πεδία (3 ευρετήρια). Αναμονή indexing...")
wait_for_index("product_idx")
print("Το indexing ολοκληρώθηκε.\n")


def show(title, *cmd):
    print("=" * 74)
    print(title)
    print("Εντολή:", " ".join(str(c) for c in cmd))
    print("-" * 74)
    res = r.execute_command(*cmd)
    total = res[0]
    for i in range(1, len(res), 2):
        fields = dict(zip(res[i + 1][::2], res[i + 1][1::2]))
        print(res[i], "->", fields)
    if total == 0:
        print("(κανένα αποτέλεσμα στο τυχαίο dataset — δοκίμασε άλλο εύρος)")
    print(f"(σύνολο αποτελεσμάτων: {total})\n")


# 1) Αριθμητικό εύρος
show('Προϊόντα με τιμή 100-500  ->  FT.SEARCH product_idx "@price:[100 500]"',
     "FT.SEARCH", "product_idx", "@price:[100 500]", "LIMIT", "0", "5")

# 2) TAG + αριθμητικό εύρος
show('Προϊόντα κατηγορίας Laptops με τιμή 100-500  ->  FT.SEARCH product_idx "@category:{Laptops} @price:[100 500]"',
     "FT.SEARCH", "product_idx", "@category:{Laptops} @price:[100 500]", "LIMIT", "0", "5")

# 3) Fulltext / prefix στο name
show('Προϊόντα με όνομα που αρχίζει από "Product1"  ->  FT.SEARCH product_idx "@name:Product1*"',
     "FT.SEARCH", "product_idx", "@name:Product1*", "LIMIT", "0", "5")

r.close()