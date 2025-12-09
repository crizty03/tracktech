import mysql.connector

try:
    conn = mysql.connector.connect(host='localhost', user='root', password='', database='garment_db')
    cursor = conn.cursor()
    
    # Check Last 3 Months (Oct 1 - Dec 31)
    query = """
    SELECT SUM(day_achieved) 
    FROM production_data 
    WHERE buyer_name = 'Adidas' 
    AND production_date BETWEEN '2024-10-01' AND '2024-12-31'
    """
    
    cursor.execute(query)
    result = cursor.fetchone()[0]
    print(f"Verified Last 3 Months Result: {result}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
