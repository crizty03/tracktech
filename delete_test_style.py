import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'garment_db'
}

def delete_test_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        style = "TEST_STYLE_NEW"
        
        # Check if it exists first
        cursor.execute("SELECT COUNT(*) FROM production_data WHERE style_no = %s", (style,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute("DELETE FROM production_data WHERE style_no = %s", (style,))
            conn.commit()
            print(f"Successfully deleted {count} rows for style '{style}'.")
        else:
            print(f"Style '{style}' not found. Nothing to delete.")
            
        conn.close()
    except Exception as e:
        print(e)

if __name__ == '__main__':
    delete_test_data()
