RDBMS to Redis Migration & Benchmark

This is the code behind my thesis, where I migrate a relational e-commerce dataset (users, products, orders, order items) from MySQL into Redis and compare how the two perform on the same set of queries.

The idea was simple: build a dataset big enough to be realistic (1M orders), move it into Redis using the access patterns that actually make sense there (hashes, sets, sorted sets, lists), and then measure read/write performance side by side instead of just assuming Redis is "faster."

What's in here
dataset.py — generates the dataset directly in MySQL (users, categories, products, orders, order items). Truncates and regenerates everything from scratch every time it's run, so be careful running this if you have data you want to keep.
thesis-etl.py — reads the current MySQL data and loads it into Redis, mapping each table to the Redis structure that fits it best (hashes for entities, sets for category lookups, sorted sets for price range queries, lists for one-to-many relations like a user's orders).
validation.py — sanity check that MySQL and Redis actually hold the same data after the ETL runs. Samples random records and compares them field by field.
benchmark.py — read benchmarks. Runs the same queries against MySQL and Redis (user lookup, order lookup, order items, category filter, price range) and reports mean/stdev response times.
benchmark_write.py — write benchmarks (insert/delete) for orders, same idea, MySQL vs Redis.
redis_search.py / redis_aggr.py — separate scripts exploring RediSearch (FT.SEARCH / FT.AGGREGATE) on top of the Redis hashes, since that's a different way of querying than the direct key lookups used elsewhere.
Setup

You'll need MySQL and Redis running locally (Redis needs the RediSearch module if you want to run redis_search.py / redis_aggr.py — a plain redis-server won't have FT.* commands, so I used Redis Stack for that part).

bash
pip install -r requirements.txt

Create a MySQL database called thesis2026 with the following tables before running anything: users, categories, products, orders, order_items. The connection settings (host/user/password) are hardcoded at the top of each script for localhost — change them there if your setup is different.

Running it

Order matters here:

python dataset.py — builds the dataset in MySQL
python thesis-etl.py — copies it into Redis
python validation.py — confirms both sides match
python benchmark.py and python benchmark_write.py — run the actual comparisons

If you regenerate the dataset with dataset.py, re-run thesis-etl.py afterwards or Redis will be out of sync with MySQL.

Notes

Everything is seeded with plain random, so numbers will vary a bit between runs — the benchmark scripts print mean ± standard deviation over 100 repeats (with a short warmup) to smooth that out a little.