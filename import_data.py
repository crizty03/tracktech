import mysql.connector
import random
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Default empty, change if needed
    'database': 'garment_db'
}

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            # Database might not exist, connect without db to create it
            temp_config = DB_CONFIG.copy()
            del temp_config['database']
            conn = mysql.connector.connect(**temp_config)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            conn.close()
            return mysql.connector.connect(**DB_CONFIG)
        else:
            print(f"Error connecting to DB: {err}")
            return None

def create_table(conn):
    cursor = conn.cursor()
    with open("schema.sql", "r") as f:
        sql_script = f.read()
    
    # Execute statements separately
    for statement in sql_script.split(';'):
        if statement.strip():
            try:
                cursor.execute(statement)
            except mysql.connector.Error as err:
                print(f"Skipping statement due to error: {err}")
    conn.commit()
    print("Schema created successfully.")

def generate_dummy_data(num_rows=1000000):
    print(f"Generating {num_rows} rows of data...")
    
    buyers = ['H&M', 'Zara', 'Gap', 'Nike', 'Adidas', 'Puma', 'Uniqlo']
    styles = [f'ST{i}' for i in range(100, 200)]
    fabrics = ['Single Jersey', 'Fleece', 'Rib', 'Interlock', 'Pique']
    colors = ['Red', 'Blue', 'Black', 'White', 'Green', 'Yellow', 'Grey']
    start_date = datetime(2023, 1, 1)
    
    data = []
    
    # Batch generation for memory efficiency
    batch_size = 5000
    
    for _ in tqdm(range(0, num_rows, batch_size)):
        batch_data = []
        for _ in range(batch_size):
            if len(data) + len(batch_data) >= num_rows:
                break
                
            date = start_date + timedelta(days=random.randint(0, 730))
            buyer = random.choice(buyers)
            style = random.choice(styles)
            line = random.randint(1, 20)
            target = random.randint(800, 1200)
            
            # Hourly production with some logic
            hours = [random.randint(50, 150) for _ in range(8)]
            achieved = sum(hours)
            
            fabric_planned = achieved * 0.25  # Approx 250g per garment
            fabric_actual = fabric_planned * random.uniform(0.95, 1.10) # 5% less to 10% more
            
            batch_data.append((
                f"ORD{random.randint(10000, 99999)}",
                buyer,
                style,
                random.randint(1000, 50000), # order_quantity
                date.strftime('%Y-%m-%d'),
                target,
                achieved,
                hours[0], hours[1], hours[2], hours[3], hours[4], hours[5], hours[6], hours[7],
                random.choice(fabrics),
                random.randint(140, 300), # gsm
                random.choice(colors),
                round(fabric_planned, 2),
                round(fabric_actual, 2),
                random.randint(0, 50), # rejection
                random.randint(0, 100), # rework
                target + 100, # planned_cut
                achieved + random.randint(0, 50), # actual_cut
                f"OP{random.randint(1, 500)}",
                line
            ))
        yield batch_data

def insert_data(conn):
    cursor = conn.cursor()
    query = """
    INSERT INTO production_data (
        order_no, buyer_name, style_no, order_quantity, production_date,
        day_target, day_achieved, hour_1, hour_2, hour_3, hour_4, 
        hour_5, hour_6, hour_7, hour_8, fabric_type, fabric_gsm, 
        color, planned_fabric_meters, actual_fabric_used, rejection, 
        rework, planned_cut_quantity, actual_cut_quantity, operator_code, line_no
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    count = 0
    for batch in generate_dummy_data(1000000):
        cursor.executemany(query, batch)
        conn.commit()
        count += len(batch)
        print(f"Inserted {count} rows...")

if __name__ == "__main__":
    conn = get_connection()
    if conn:
        create_table(conn)
        insert_data(conn)
        conn.close()
        print("Data import complete.")
