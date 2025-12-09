import mysql.connector
import time

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'garment_db'
}

print("Attempting to connect to DB...")
start = time.time()
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    print("Connection successful!")
    conn.close()
    print(f"Time taken: {time.time() - start:.2f}s")
except Exception as e:
    print(f"Connection failed: {e}")
    print(f"Time taken: {time.time() - start:.2f}s")
