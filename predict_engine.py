import joblib
import pandas as pd
import numpy as np
import mysql.connector
import os

class PredictEngine:
    def __init__(self, model_path='model_order_completion.pkl'):
        try:
            artifacts = joblib.load(model_path)
            self.model = artifacts['model']
            self.le_style = artifacts['le_style']
            self.le_buyer = artifacts['le_buyer']
            self.feature_cols = artifacts['features']
            self.loaded = True
        except Exception as e:
            print(f"Error loading model: {e}")
            self.loaded = False
            
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'garment_db'),
            'port': int(os.getenv('DB_PORT', 3306))
        }

    def get_latest_data(self, style_no):
        conn = mysql.connector.connect(**self.db_config)
        # Getting the latest snapshot of the style
        query = """
        SELECT * FROM production_data 
        WHERE style_no = %s 
        ORDER BY production_date DESC LIMIT 1
        """
        df = pd.read_sql(query, conn, params=(style_no,))
        
        # We also need cumulative sum to calculate remaining qty correctly
        # So we need a quick aggregation query
        agg_query = """
        SELECT SUM(day_achieved) as total_produced 
        FROM production_data WHERE style_no = %s
        """
        cursor = conn.cursor()
        cursor.execute(agg_query, (style_no,))
        total_produced = cursor.fetchone()[0] or 0
        conn.close()
        
        return df, total_produced

    def predict_order(self, style_no):
        if not self.loaded:
            return {"error": "Model not loaded"}

        df, total_produced = self.get_latest_data(style_no)
        
        if df.empty:
            return {"error": f"Style {style_no} not found in history."}
            
        row = df.iloc[0]
        
        # Prepare Features (Mirroring train_model.py)
        # 1. Encoders (Handle unseen labels gracefully)
        try:
            style_enc = self.le_style.transform([row['style_no']])[0]
        except:
            style_enc = 0 # Default/Unknown
            
        try:
            buyer_enc = self.le_buyer.transform([row['buyer_name']])[0]
        except:
            buyer_enc = 0
            
        # 2. Calculated features
        remaining = max(0, row['order_quantity'] - total_produced)
        daily_eff = (row['day_achieved'] / row['day_target']) if row['day_target'] else 0
        
        # Approximating Trend (Using current daily eff as proxy if history fetch is expensive, 
        # or we could run a 7-day query. For speed, we use current snapshot)
        eff_trend = daily_eff 
        
        fabric_var = 0
        if row['planned_fabric_meters']:
            fabric_var = (row['actual_fabric_used'] - row['planned_fabric_meters']) / row['planned_fabric_meters']
            
        hour_output = sum([row[f'hour_{i}'] for i in range(1, 9)])
        
        input_data = pd.DataFrame([{
            'style_encoded': style_enc,
            'buyer_encoded': buyer_enc,
            'order_quantity': row['order_quantity'],
            'cumulative_achieved': total_produced,
            'remaining_qty': remaining,
            'daily_efficiency': daily_eff,
            'efficiency_trend': eff_trend,
            'fabric_variance': fabric_var,
            'hour_output': hour_output,
            'rejection': row['rejection'],
            'line_no': row['line_no']
        }])
        
        # Reorder to match training
        input_data = input_data[self.feature_cols]
        
        # Predict Daily Rate capability
        predicted_rate = self.model.predict(input_data)[0]
        
        if predicted_rate <= 10: predicted_rate = 10 # Safety floor
        
        days_left = remaining / predicted_rate
        
        # Risk Logic
        risk = "Low"
        if days_left > 7: risk = "High"
        elif days_left > 3: risk = "Medium"
        
        return {
            "style_no": style_no,
            "estimated_days": round(days_left, 1),
            "remaining_qty": int(remaining),
            "predicted_daily_rate": int(predicted_rate),
            "risk": risk,
            "avg_efficiency": round(eff_trend * 100, 1)
        }

    def get_active_risk_report(self):
        if not self.loaded:
            return {"error": "Model not loaded"}
            
        try:
            conn = mysql.connector.connect(**self.db_config)
            # Find Active Styles (Most recent entry has remaining qty implied, or just check limit)
            # Better: Get distinct styles from recent 1000 entries and check prediction
            query = "SELECT style_no FROM production_data ORDER BY production_date DESC LIMIT 1000"
            df_recent = pd.read_sql(query, conn)
            conn.close()
            
            unique_styles = df_recent['style_no'].unique()[:5] # Check top 5 most recent active
            
            report = []
            for style in unique_styles:
                start = pd.Timestamp.now()
                pred = self.predict_order(style)
                # Only include valid, incomplete orders
                if "error" not in pred and pred['remaining_qty'] > 0:
                    report.append(pred)
            
            return {"styles": report}
            
        except Exception as e:
            return {"error": str(e)}
