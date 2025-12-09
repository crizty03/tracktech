import mysql.connector
import pandas as pd

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'garment_db'
}

def check_st150():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Get basic info
        cursor.execute("SELECT order_quantity FROM production_data WHERE style_no = 'ST150' LIMIT 1")
        row = cursor.fetchone()
        if not row:
            print("ST150 not found in DB")
            return
            
        order_qty = row['order_quantity']
        
        # Get total produced
        cursor.execute("SELECT SUM(day_achieved) as total FROM production_data WHERE style_no = 'ST150'")
        total_produced = cursor.fetchone()['total'] or 0
        
        remaining = order_qty - total_produced
        
        print(f"ST150 Analysis:")
        print(f"Order Expected: {order_qty}")
        print(f"Total Produced: {total_produced}")
        print(f"Remaining: {remaining}")
        
        if remaining <= 0:
            print("CONCLUSION: Order is COMPLETE. Prediction of 0 days/0 remaining is CORRECT.")
        else:
            print("CONCLUSION: Order is INCOMPLETE. Prediction engine has a bug.")
            
        conn.close()
    except Exception as e:
        print(e)
        
if __name__ == '__main__':
    check_st150()
