from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import mysql.connector
import joblib
import os
import json
from query_interpreter import QueryInterpreter
from summary_engine import SummaryEngine
import numpy as np
from predict_engine import PredictEngine
from fastapi.responses import FileResponse

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Modules
# Load Modules
nlp = None
summary_engine = None
predictor = None

@app.on_event("startup")
async def startup_event():
    global nlp, summary_engine, predictor
    print("Initializing AI Models...")
    nlp = QueryInterpreter()
    summary_engine = SummaryEngine()
    predictor = PredictEngine()
    print("AI Models initialized successfully.")

# DB Config
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'garment_db'
}

class QueryRequest(BaseModel):
    text: str

class PredictRequest(BaseModel):
    style_no: str
    order_qty: int = 0 # Optional if fetching from DB
    line_no: int = 0
    fabric_gsm: int = 0

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.get("/")
def read_root():
    return FileResponse('frontend/index.html')

@app.post("/ask")
def process_query(request: QueryRequest):
    try:
        interpretation = nlp.interpret(request.text)
        
        # Check for Prediction Intent
        if interpretation.get('type') == 'prediction':
            style = interpretation.get('style_no')
            if not style:
                return {"summary_text": "I understood you want a prediction, but I couldn't identify the Style Number (e.g. ST150).", "table_data": [], "chart_data": {}}
            
            # Call Prediction Engine
            pred_result = predictor.predict_order(style)
            if "error" in pred_result:
                 return {"summary_text": f"Error: {pred_result['error']}", "table_data": [], "chart_data": {}}
            
            # Format Prediction as a conversational summary (using HTML for frontend)
            summary = (
                f"<b>Prediction for {style}</b>:<br><br>"
                f"&bull; <b>Estimated Completion</b>: In {pred_result['estimated_days']} days.<br>"
                f"&bull; <b>Risk Level</b>: {pred_result['risk']}<br>"
                f"&bull; <b>Remaining Qty</b>: {pred_result['remaining_qty']} pcs<br>"
                f"&bull; <b>Current Rate</b>: {pred_result.get('predicted_daily_rate', 0)} pcs/day"
            )
            
            return {
                "summary_text": summary,
                "table_data": [pred_result], # Show details in table
                "chart_data": {}
            }

        # Handling Risk Overview (Vague "Will we finish?" queries)
        if interpretation.get('type') == 'risk_overview':
             report = predictor.get_active_risk_report()
             if "error" in report:
                  return {"summary_text": f"Error generating risk report: {report['error']}"}
             
             styles = report.get('styles', [])
             if not styles:
                  return {"summary_text": "No active order risks detected at the moment."}
                  
             # Build summary
             summary = "<b>Risk Overview (Active Orders)</b>:<br>Here are the completion estimates for the currently active styles:<br>"
             
             return {
                 "summary_text": summary,
                 "table_data": styles,
                 "chart_data": {}
             }

        # SQL Query Flow
        sql = interpretation['sql']
        params = interpretation['params']
        
        # 2. Execute SQL
        conn = get_db_connection()
        df = pd.read_sql(sql, conn, params=params)
        conn.close()
        
        # 3. Generate Insight
        metric = interpretation['parsed_query']['metric']
        context = interpretation['parsed_query']
        
        summary_res = summary_engine.generate_summary(df, metric, context)
        
        # 4. Format Data for Charts
        chart_data = {}
        if not df.empty and 'production_date' in df.columns and metric == 'efficiency':
             chart_data = {
                 'labels': df['production_date'].astype(str).tolist(),
                 'values': df['efficiency'].tolist()
             }
        elif not df.empty and 'buyer_name' in df.columns:
            # Aggregate for chart if too many rows
             agg = df.groupby('buyer_name')['day_achieved'].sum().reset_index()
             chart_data = {
                 'labels': agg['buyer_name'].tolist(),
                 'values': agg['day_achieved'].tolist()
             }
             
        # Convert df to records for Table
        table_data = df.head(50).fillna('').to_dict(orient='records')
        
        return {
            "summary_text": summary_res['summary'],
            "recommendations": summary_res['recommendations'],
            "table_data": table_data,
            "chart_data": chart_data,
            "sql_debug": sql
        }
        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict")
def predict_completion(req: PredictRequest):
    # Direct API endpoint using the same engine
    result = predictor.predict_order(req.style_no)
    return result

# Mount static files for UI
if not os.path.exists("frontend"):
    os.makedirs("frontend")

app.mount("/static", StaticFiles(directory="frontend"), name="static")
