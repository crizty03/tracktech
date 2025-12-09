import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error
import joblib
import mysql.connector

# DB Config
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'garment_db'
}

def get_full_data():
    conn = mysql.connector.connect(**DB_CONFIG)
    # Fetch all data to perform time-series feature engineering
    query = """
    SELECT * FROM production_data ORDER BY production_date ASC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def feature_engineering(df):
    print("Engineering features...")
    
    # Sort for rolling calcs
    df['production_date'] = pd.to_datetime(df['production_date'])
    df = df.sort_values(['style_no', 'production_date'])
    
    # 1. Cumulative Achieved
    df['cumulative_achieved'] = df.groupby('style_no')['day_achieved'].cumsum()
    
    # 2. Remaining Quantity
    df['remaining_qty'] = df['order_quantity'] - df['cumulative_achieved']
    # Filter out completed orders for training realistic "in-progress" scenarios
    df = df[df['remaining_qty'] > 0]
    
    # 3. Efficiency Trend (7-day rolling average)
    # Calculate daily efficiency first
    df['daily_efficiency'] = (df['day_achieved'] / df['day_target']).replace([np.inf, -np.inf], 0).fillna(0)
    df['efficiency_trend'] = df.groupby('style_no')['daily_efficiency'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )
    
    # 4. Fabric Variance
    df['fabric_variance'] = (df['actual_fabric_used'] - df['planned_fabric_meters']) / df['planned_fabric_meters']
    df['fabric_variance'] = df['fabric_variance'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # 5. Hour Output Sum
    hour_cols = [f'hour_{i}' for i in range(1, 9)]
    df['hour_output'] = df[hour_cols].sum(axis=1)

    # 6. Target Variable: Days to produce remaining qty based on current rate
    # We want the model to predict the "Current Capability" (Daily Rate)
    # Then we infer days = remaining / predicted_rate
    # So our target is actually the NEXT DAY's achievement (or current day capability)
    # But for "Order Completion", let's predict the effective daily rate directly.
    # Actually, simpler: Predict 'day_achieved' capability based on current state.
    
    return df

def train_model():
    df = get_full_data()
    df = feature_engineering(df)
    
    # Encoders
    le_style = LabelEncoder()
    le_buyer = LabelEncoder()
    df['style_encoded'] = le_style.fit_transform(df['style_no'])
    df['buyer_encoded'] = le_buyer.fit_transform(df['buyer_name'])
    
    # Features
    feature_cols = [
        'style_encoded', 'buyer_encoded', 'order_quantity', 
        'cumulative_achieved', 'remaining_qty', 'daily_efficiency', 
        'efficiency_trend', 'fabric_variance', 'hour_output', 'rejection', 'line_no'
    ]
    
    target_col = 'day_achieved' # We predict how much they can make per day
    
    X = df[feature_cols].fillna(0)
    y = df[target_col].fillna(0)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest Regressor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # Evaluate
    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    
    print(f"\nModel Accuracy (R2): {r2:.4f}")
    print(f"Mean Absolute Error: {mae:.2f} pcs")
    
    # Save everything
    artifacts = {
        'model': model,
        'le_style': le_style,
        'le_buyer': le_buyer,
        'features': feature_cols
    }
    joblib.dump(artifacts, 'model_order_completion.pkl')
    print("Model artifacts saved to 'model_order_completion.pkl'")

if __name__ == "__main__":
    train_model()
