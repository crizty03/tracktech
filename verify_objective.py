import requests
import json

BASE_URL = "http://127.0.0.1:8000"

queries = [
    "Give me last week production summary",
    "Show buyer-wise performance for H&M",
    "What is the efficiency of line 5 yesterday?",
    "Show fabric wastage report for Single Jersey",
    "Predict order completion for style ST235"
]

print(f"Testing {len(queries)} User Scenarios...\n")

for q in queries:
    print(f"👉 Query: '{q}'")
    
    try:
        if "predict" in q.lower():
            # Mimic frontend logic for prediction
            style = "ST100"
            if "ST235" in q: style = "ST235"
            payload = {"style_no": style, "order_qty": 5000}
            url = f"{BASE_URL}/predict"
        else:
            payload = {"text": q}
            url = f"{BASE_URL}/ask"
            
        response = requests.post(url, json=payload)
        data = response.json()
        
        if "prediction" in q.lower():
            print(f"   ✅ Response: {data.get('predicted_daily_output', 'N/A')} pcs/day, {data.get('days_to_complete', 'N/A')} days")
        else:
            summary = data.get('summary_text', 'No summary')
            # Truncate summary for display
            display_summary = (summary[:75] + '..') if len(summary) > 75 else summary
            print(f"   ✅ NLP/SQL: Success")
            print(f"   📝 Summary: {display_summary}")
            if data.get('table_data'):
                print(f"   📊 Data: Found {len(data['table_data'])} rows")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("-" * 40)
