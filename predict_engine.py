import joblib
import numpy as np
import mysql.connector
import os

import onnxruntime as ort
import joblib

import json
import onnxruntime as ort

class PredictEngine:
    def __init__(self, model_path='model_order_completion.onnx', encoder_path='encoders.json'):
        try:
            # Load ONNX Model
            self.sess = ort.InferenceSession(model_path)
            
            # Load Encoders
            with open(encoder_path, 'r') as f:
                self.encoders = json.load(f)
                
            self.loaded = True
        except Exception as e:
            print(f"Error loading ONNX model/encoders: {e}")
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
        cursor = conn.cursor(dictionary=True)
        # Getting the latest snapshot of the style
        query = """
        SELECT * FROM production_data 
        WHERE style_no = %s 
        ORDER BY production_date DESC LIMIT 1
        """
        cursor.execute(query, (style_no,))
        row = cursor.fetchone()
        
        # We also need cumulative sum to calculate remaining qty correctly
        agg_query = """
        SELECT SUM(day_achieved) as total_produced 
        FROM production_data WHERE style_no = %s
        """
        cursor.execute(agg_query, (style_no,))
        res = cursor.fetchone()
        total_produced = res['total_produced'] if res and res['total_produced'] else 0
        
        conn.close()
        return row, total_produced

    def predict_order(self, style_no):
        if not self.loaded:
            return {"error": "Model not loaded"}

        row, total_produced = self.get_latest_data(style_no)
        
        if not row:
            return {"error": f"Style {style_no} not found in history."}
            
        # Prepare Features (Mirroring train_model.py)
        # 1. Encoders (Handle unseen labels gracefully)
        style_enc = self.encoders['style_map'].get(str(row['style_no']), 0)
        buyer_enc = self.encoders['buyer_map'].get(str(row['buyer_name']), 0)
            
        # 2. Calculated features
        remaining = max(0, row['order_quantity'] - total_produced)
        daily_eff = (row['day_achieved'] / row['day_target']) if row['day_target'] else 0
        
        # Approximating Trend (Using current daily eff as proxy)
        eff_trend = daily_eff 
        
        fabric_var = 0
        if row['planned_fabric_meters']:
            fabric_var = (row['actual_fabric_used'] - row['planned_fabric_meters']) / row['planned_fabric_meters']
            
        hour_output = sum([row[f'hour_{i}'] for i in range(1, 9)])
        
        # Build feature list explicitly in the correct order for the model
        # Feature order: ['style_encoded', 'buyer_encoded', 'order_quantity', 'cumulative_achieved', 'remaining_qty', 'daily_efficiency', 'efficiency_trend', 'fabric_variance', 'hour_output', 'rejection', 'line_no']
        
        input_data = [
            [
                float(style_enc),
                float(buyer_enc),
                float(row['order_quantity']),
                float(total_produced),
                float(remaining),
                float(daily_eff),
                float(eff_trend),
                float(fabric_var),
                float(hour_output),
                float(row['rejection']),
                float(row['line_no'])
            ]
        ]
        
        # ONNX Inference
        input_name = self.sess.get_inputs()[0].name
        label_name = self.sess.get_outputs()[0].name
        
        # We need numpy for ONNX runtime usually, or it might accept lists?
        # Standard ORT requires numpy arrays.
        # Luckily we kept numpy in requirements.txt (it is smaller than scipy)
        import numpy as np
        input_arr = np.array(input_data, dtype=np.float32)
        
        pred_onx = self.sess.run([label_name], {input_name: input_arr})[0]
        predicted_rate = pred_onx[0][0] # [[value]]
        
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
            query = "SELECT style_no FROM production_data ORDER BY production_date DESC LIMIT 1000"
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            # Deduplicate
            styles = []
            seen = set()
            for r in rows:
                if r[0] not in seen:
                    styles.append(r[0])
                    seen.add(r[0])
            
            unique_styles = styles[:5]
            
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
