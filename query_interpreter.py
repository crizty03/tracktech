import re
from datetime import datetime, timedelta
import json
import joblib
import pandas as pd

class QueryInterpreter:
    def __init__(self):
        self.metrics = {
            'efficiency': 'AVG(day_achieved / day_target * 100) as efficiency',
            'wastage': 'AVG((actual_fabric_used - planned_fabric_meters) / planned_fabric_meters * 100) as wastage',
            'performance': 'SUM(day_achieved) as total_production',
            'target gap': 'SUM(day_target - day_achieved) as target_gap',
            'rejection': 'SUM(rejection) as total_rejection',
            'production': 'SUM(day_achieved) as total_production'
        }
        
        # Load NLP Model
        try:
            self.nlp_model = joblib.load('nlp_model.pkl')
            self.ml_enabled = True
            print("NLP Model loaded successfully.")
        except Exception as e:
            print(f"Warning: NLP Model not found: {e}")
            self.ml_enabled = False
        
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'garment_db'
        }
        
        # Default filters (Fallback)
        self.filters = {
            'buyer_name': r'for (H&M|Zara|Gap|Nike|Adidas|Puma|Uniqlo)',
            'style_no': r'style (ST\d+)',
            'line_no': r'line (\d+)',
            'fabric_type': r'fabric (Single Jersey|Fleece|Rib|Interlock|Pique)'
        }
        
        # Try to load dynamic filters from DB
        self.load_dynamic_filters()
        
        # Load Anchor Date (Max Date in DB)
        self.anchor_date = self.fetch_max_date()

    def get_db_connection(self):
        import mysql.connector
        return mysql.connector.connect(**self.db_config)

    def fetch_max_date(self):
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(production_date) FROM production_data")
            max_date = cursor.fetchone()[0]
            conn.close()
            if max_date:
                print(f"Anchor Date set to: {max_date}")
                return max_date
            return datetime.now().date()
        except Exception as e:
            print(f"Error fetching max date: {e}")
            return datetime.now().date()

    def load_dynamic_filters(self):
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Fetch Buyers
            cursor.execute("SELECT DISTINCT buyer_name FROM production_data")
            buyers = [row[0] for row in cursor.fetchall() if row[0]]
            if buyers:
                # Escape generic regex characters just in case, and join with OR
                buyer_pattern = '|'.join([re.escape(b) for b in buyers])
                # Allow query to be "for Adidas" or just "Adidas"
                # using \b to ensure whole word match
                self.filters['buyer_name'] = f'(?:for\s+)?({buyer_pattern})'
            
            # Fetch Fabrics
            cursor.execute("SELECT DISTINCT fabric_type FROM production_data")
            fabrics = [row[0] for row in cursor.fetchall() if row[0]]
            if fabrics:
                fabric_pattern = '|'.join([re.escape(f) for f in fabrics])
                self.filters['fabric_type'] = f'(?:fabric\s+)?({fabric_pattern})'

            # Fetch Styles (Limit to 500 recently used to keep regex manageable)
            # Fetch Styles (Optimize: Fetch recent rows using index and deduplicate in Python)
            # Fetching 2000 latest rows is fast with index on production_date
            cursor.execute("SELECT style_no FROM production_data ORDER BY production_date DESC LIMIT 2000")
            raw_styles = [row[0] for row in cursor.fetchall() if row[0]]
            # Deduplicate preserving order
            styles = list(dict.fromkeys(raw_styles))[:500]
            if styles:
                style_pattern = '|'.join([re.escape(s) for s in styles])
                self.filters['style_no'] = f'(?:style\s+|order\s+|for\s+)?({style_pattern})'
                
            conn.close()
            print(f"Loaded {len(buyers)} buyers, {len(fabrics)} fabrics, {len(styles)} styles from DB.")
        except Exception as e:
            print(f"Warning: Could not load dynamic filters: {e}")

    def parse_date_range(self, query):
        # Use anchor_date as 'today' if available, else system date
        today = self.anchor_date if hasattr(self, 'anchor_date') and self.anchor_date else datetime.now().date()
        date_range = {}
        
        # Regex for dynamic dates: "last 30 days", "past 5 months", "10 days"
        # Matches: (number) (unit)
        import re
        date_match = re.search(r'(?:last|past|for)?\s*(\d+)\s*(days?|weeks?|months?)', query, re.IGNORECASE)
        
        if date_match:
            amount = int(date_match.group(1))
            unit = date_match.group(2).lower()
            
            if 'day' in unit:
                start = today - timedelta(days=amount)
            elif 'week' in unit:
                start = today - timedelta(weeks=amount)
            elif 'month' in unit:
                start = today - timedelta(days=amount * 30)
            
            date_range = {'start': str(start), 'end': str(today)}
            return date_range

        # Static Fallbacks
        if 'yesterday' in query:
            yesterday = today - timedelta(days=1)
            date_range = {'start': str(yesterday), 'end': str(yesterday)}
        elif 'last week' in query:
            start = today - timedelta(days=7)
            date_range = {'start': str(start), 'end': str(today)}
        elif 'last month' in query:
            start = today - timedelta(days=30)
            date_range = {'start': str(start), 'end': str(today)}
        else:
            # No date specified -> Return None to imply "All Time"
            return None
            
        return date_range

    def extract_filters(self, query):
        extracted_filters = {}
        for key, pattern in self.filters.items():
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                value = match.group(1)
                # Convert line number to int
                if key == 'line_no':
                    value = int(value)
                extracted_filters[key] = value
        return extracted_filters

    def predict_intent(self, query):
        if not self.ml_enabled:
            return self.valid_metric_regex(query)
            
        try:
            intent = self.nlp_model.predict([query])[0]
            # Map Intent to Metric Key
            mapping = {
                'EFFICIENCY': 'efficiency',
                'WASTAGE': 'wastage',
                'PRODUCTION': 'production',
                'PREDICTION': 'predict',
                'GENERAL': 'production' # Fallback
            }
            return mapping.get(intent, 'production')
        except:
            return self.valid_metric_regex(query)

    def valid_metric_regex(self, query):
        # Fallback to old regex
        for key in self.metrics:
            if key in query.lower():
                return key
        return "production"

    def interpret(self, query):
        query = query.lower()
        
        # 1. Identify Intent/Metric via ML
        metric_key = self.predict_intent(query)
        
        # Special Case: Prediction Intent
        filters = self.extract_filters(query)
        
        if metric_key == 'predict':
            # Extract style for prediction
            style = filters.get('style_no')
            # If no style found in filters, try regex fallback just for style
            if not style:
                # PERMISSIVE FALLBACK: Look for word coming after "style", "order", "for"
                # Matches: "style ST123", "order TEST_STYLE", "for ST_NEW"
                match = re.search(r'(?:style|order|for)\s+([A-Za-z0-9_]+)', query, re.IGNORECASE)
                if match:
                    style = match.group(1)
            
            # CRITICAL FIX: If intent is PREDICT but no style is found:
            # 1. If we HAVE other filters (like buyer 'adidas'), assume it's a PRODUCTION query.
            # 2. If NO filters at all (e.g. "Will we finish on time?"), it's a RISK OVERVIEW.
            if not style:
                if (filters.get('buyer_name') or filters.get('line_no') or filters.get('fabric_type')):
                    metric_key = 'production'
                    # Fall through to standard SQL query logic
                else:
                    # Generic prediction question -> Risk Overview
                    return {
                        "type": "risk_overview",
                        "parsed_query": {"metric": "risk_overview", "filters": {}} 
                    }
            else:
                return {
                    "type": "prediction",
                    "style_no": style,
                    "parsed_query": {"metric": "predict", "filters": filters}
                }

        # Standard SQL Query
        select_clause = self.metrics.get(metric_key, self.metrics['production'])
        
        # 2. Identify Filters (already done)
        
        # 3. Identify Date Range
        date_range = self.parse_date_range(query)
        
        # 4. Construct SQL
        if date_range:
            sql = f"SELECT {select_clause} FROM production_data WHERE production_date BETWEEN %s AND %s"
            params = [date_range['start'], date_range['end']]
        else:
            # No date -> All Time (No WHERE Clause for date)
            sql = f"SELECT {select_clause} FROM production_data WHERE 1=1"
            params = []
        
        for key, value in filters.items():
            sql += f" AND {key} = %s"
            params.append(value)
            
        return {
            "type": "sql",
            "parsed_query": {
                "metric": metric_key,
                "filters": filters,
                "date_range": date_range if date_range else "All Time"
            },
            "sql": sql,
            "params": params
        }

if __name__ == "__main__":
    nlp = QueryInterpreter()
    q = "Show fabric wastage report for Single Jersey last week"
    result = nlp.interpret(q)
    print(json.dumps(result, indent=2))
