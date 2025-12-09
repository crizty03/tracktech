import mysql.connector
from datetime import date

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'garment_db'
}

def insert_active_order():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        style = "TEST_STYLE_NEW"
        
        # 1. Delete if exists (clean slate)
        cursor.execute("DELETE FROM production_data WHERE style_no = %s", (style,))
        
        # 2. Insert "History" for this style (so model sees a trend)
        # Order: 50,000. Produced: 15,000 over 15 days (~1000/day).
        # We insert the LAST day's record which acts as the 'latest snapshot'
        
        sql = """
        INSERT INTO production_data (
            production_date, buyer_name, style_no, order_quantity, 
            day_target, day_achieved, 
            line_no, fabric_type, fabric_gsm, 
            actual_fabric_used, planned_fabric_meters,
            rejection, rework, operator_code
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s, %s
        )
        """
        
        # Data for a recent day
        val = (
            '2024-12-31', 'TestBuyer', style, 50000, 
            1200, 1000, # Target 1200, Achieved 1000
            1, 'Single Jersey', 160,
            250, 240, # Fabric usage
            5, 10, 'OP001'
        )
        
        cursor.execute(sql, val)
        conn.commit()
        
        print(f"Inserted active test order: {style}")
        print("Order: 50,000 | Produced (Snapshot): 1,000 per day rate.")
        print("Note: In a real scenario, we'd sum up all rows. Here, the 'cumulative' calculation in 'predict_engine' might see only this row or we need multiple.")
        
        conn.close()
    except Exception as e:
        print(e)
        
if __name__ == '__main__':
    insert_active_order()
