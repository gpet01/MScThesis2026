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