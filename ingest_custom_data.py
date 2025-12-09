import pandas as pd
import mysql.connector
from datetime import datetime
import sys
import os

# DB Config
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'garment_db'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def ingest_data(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    print(f"Reading {file_path}...")
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            print("Unsupported file format. Please use CSV or Excel.")
            return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Standardize Column Names (Simple mapping)
    # Map user columns to DB columns if they differ
    column_mapping = {
        'Order No': 'order_no', 'Buyer': 'buyer_name', 'Style': 'style_no', 
        'Quantity': 'order_quantity', 'Date': 'production_date', 
        'Target': 'day_target', 'Achieved': 'day_achieved',
        'Fabric': 'fabric_type', 'GSM': 'fabric_gsm', 
        'Used Fabric': 'actual_fabric_used', 'Planned Fabric': 'planned_fabric_meters',
        'Rejection': 'rejection', 'Rework': 'rework', 'Line': 'line_no'
    }
    
    df.rename(columns=column_mapping, inplace=True)
    
    # Fill missing essential columns with defaults or drop
    required_cols = ['buyer_name', 'style_no', 'day_achieved', 'line_no']
    if not all(col in df.columns for col in required_cols):
        print("Warning: Missing one or more required columns: ", required_cols)
        # In a real app, we'd do more complex mapping here
    
    # DB Connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("Inserting data into MySQL...")
    # Prepare INSERT statement
    # This assumes the CSV has matching columns to the DB or a subset.
    # For simplicity, we'll iterate and insert specific fields we care about for training
    
    query = """
    INSERT INTO production_data (
        buyer_name, style_no, order_quantity, production_date,
        day_target, day_achieved, fabric_type, fabric_gsm, 
        planned_fabric_meters, actual_fabric_used, rejection, 
        rework, line_no
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    batch_data = []
    batch_size = 5000
    
    for _, row in df.iterrows():
        # Handle Date Format
        prod_date = row.get('production_date', datetime.now().strftime('%Y-%m-%d'))
        
        batch_data.append((
            row.get('buyer_name', 'Unknown'),
            row.get('style_no', 'Unknown'),
            row.get('order_quantity', 0),
            prod_date,
            row.get('day_target', 0),
            row.get('day_achieved', 0),
            row.get('fabric_type', 'Unknown'),
            row.get('fabric_gsm', 0),
            row.get('planned_fabric_meters', 0),
            row.get('actual_fabric_used', 0),
            row.get('rejection', 0),
            row.get('rework', 0),
            row.get('line_no', 0)
        ))
        
        if len(batch_data) >= batch_size:
            cursor.executemany(query, batch_data)
            conn.commit()
            batch_data = []
            
    if batch_data:
        cursor.executemany(query, batch_data)
        conn.commit()
        
    conn.close()
    print("Data ingestion complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ingest_data(sys.argv[1])
    else:
        print("Usage: python ingest_custom_data.py <path_to_file>")
