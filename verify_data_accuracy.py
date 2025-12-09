import mysql.connector
from datetime import date, timedelta

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'garment_db'
}

# Anchor Date (Known from previous steps)
ANCHOR_DATE = date(2024, 12, 31)

def get_sum(buyer, start_date=None, end_date=None):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        if start_date and end_date:
            query = "SELECT SUM(day_achieved) FROM production_data WHERE buyer_name = %s AND production_date BETWEEN %s AND %s"
            params = (buyer, start_date, end_date)
        else:
            query = "SELECT SUM(day_achieved) FROM production_data WHERE buyer_name = %s"
            params = (buyer,)
            
        cursor.execute(query, params)
        result = cursor.fetchone()[0]
        conn.close()
        return result if result else 0
    except Exception as e:
        print(f"Error: {e}")
        return 0

# specific scenarios from user
scenarios = [
    {"label": "Adidas All-Time", "buyer": "Adidas", "days": None, "user_value": 114179970},
    {"label": "Adidas 7 Days",   "buyer": "Adidas", "days": 7,    "user_value": 1267886},
    {"label": "Puma All-Time",   "buyer": "Puma",   "days": None, "user_value": 114240308},
    {"label": "Adidas 30 Days",  "buyer": "Adidas", "days": 30,   "user_value": 4900495},
    {"label": "Adidas 1 Day",    "buyer": "Adidas", "days": 1,    "user_value": 329668},
    {"label": "Puma 30 Days",    "buyer": "Puma",   "days": 30,   "user_value": 4824161},
    {"label": "Puma 1 Day",      "buyer": "Puma",   "days": 1,    "user_value": 298246},
]

print(f"{'SCENARIO':<20} | {'DB RANGE START':<12} | {'DB VALUE':<15} | {'USER VALUE':<15} | {'MATCH?'}")
print("-" * 80)

for s in scenarios:
    if s["days"]:
        # Logic: start = anchor - days
        # 7 days -> Dec 24 to Dec 31
        start = ANCHOR_DATE - timedelta(days=s["days"])
        end = ANCHOR_DATE
        db_val = get_sum(s["buyer"], start, end)
        range_str = str(start)
    else:
        db_val = get_sum(s["buyer"])
        range_str = "ALL TIME"
        
    s_val = s["user_value"]
    # Check match within float tolerance or exact
    match = "✅ YES" if int(db_val) == int(s_val) else f"❌ NO (Diff: {int(db_val) - int(s_val)})"
    
    print(f"{s['label']:<20} | {range_str:<12} | {int(db_val):<15} | {int(s_val):<15} | {match}")
