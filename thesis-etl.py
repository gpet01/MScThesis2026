import mysql.connector
import redis

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="thesis"
)

cursor = db.cursor(dictionary=True)

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)
