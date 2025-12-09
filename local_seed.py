
import mysql.connector
import os
import sys

# Get credentials from user input (or hardcode for this script run)
print("--- Railway Database Seeder ---")
print("Enter the details from Railway Public Networking:")

host = input("DB Host (e.g. switchyard.proxy.rlwy.net): ").strip()
port = input("DB Port (e.g. 33182): ").strip()
user = input("DB User (usually root): ").strip()
password = input("DB Password: ").strip()
database = input("DB Name (usually railway): ").strip()

config = {
    'host': host,
    'port': int(port) if port.isdigit() else 3306,
    'user': user,
    'password': password,
    'database': database
}

print(f"\nConnecting to {host}:{port}...")

try:
    conn = mysql.connector.connect(**config)
    print("SUCCESS: Connected to Railway!")
    
    cursor = conn.cursor()
    
    # Read Schema
    print("Reading schema.sql...")
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()
        
    # Python mysql connector doesn't like multiple statements in one execute unless configured
    # easier to split by ';'
    statements = schema_sql.split(';')
    
    print("Creating Tables...")
    for stmt in statements:
        if stmt.strip():
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f"Schema Warning: {e}")
                
    conn.commit()
    print("Schema applied.")
    
    # Import Data
    # We will reuse the logic from import_data.py but without the huge loop right now
    # Just to test, let's insert a few test rows using import_data logic
    # Actually, let's just ask if they want to run the full import_data
    
    print("\nDo you want to run the full data import (import_data.py) to this remote DB? (y/n)")
    choice = input("> ").lower()
    
    if choice == 'y':
        # Reuse import_data logic
        import import_data
        # Monkey patch config
        import_data.DB_CONFIG = config
        
        # Monkey patch the generator loop count in insert_data? 
        # No, insert_data hardcodes 1000000. 
        # Let's redefine insert_data locally or just run a smaller loop here.
        
        print("Starting Data Import (Targeting 1,000 rows - Minimum Viable Data)...")
        # Explicitly Drop Table to free space hard
        try:
            print("Dropping table to free space...")
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS production_data")
            conn.commit()
        except Exception as e:
            print(f"Drop warning: {e}")

        import_data.create_table(conn)
        
        query = """
        INSERT INTO production_data (
            order_no, buyer_name, style_no, order_quantity, production_date,
            day_target, day_achieved, hour_1, hour_2, hour_3, hour_4, 
            hour_5, hour_6, hour_7, hour_8, fabric_type, fabric_gsm, 
            color, planned_fabric_meters, actual_fabric_used, rejection, 
            rework, planned_cut_quantity, actual_cut_quantity, operator_code, line_no
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Generate 1,000 rows (Extremely safe <1MB)
        count = 0
        for batch in import_data.generate_dummy_data(1000):
            cursor.executemany(query, batch)
            conn.commit()
            count += len(batch)
            print(f"Inserted {count} rows...")
            
        print("Data Import Complete!")
    
    conn.close()
    print("Done.")
    
except Exception as e:
    print(f"\nCONNECTION ERROR: {e}")
    print("Double check your Host and Port!")
