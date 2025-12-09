import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'garment_db'
}

def find_incomplete_order():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Check styles where total production is LESS than order quantity
        query = """
        SELECT style_no, SUM(day_achieved) as total, MAX(order_quantity) as qty
        FROM production_data
        GROUP BY style_no
        HAVING total < qty
        LIMIT 5
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if rows:
            print("Found Incomplete Orders (Good for Testing Prediction):")
            for r in rows:
                pct = (r['total'] / r['qty']) * 100
                print(f"Style: {r['style_no']} | Produced: {r['total']} / {r['qty']} ({pct:.1f}%)")
        else:
            print("No incomplete orders found. All styles in DB are finished.")
            
        conn.close()
    except Exception as e:
        print(e)

if __name__ == '__main__':
    find_incomplete_order()
