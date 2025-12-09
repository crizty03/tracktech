
import joblib
import json

try:
    artifacts = joblib.load('model_order_completion.pkl')
    le_style = artifacts['le_style']
    le_buyer = artifacts['le_buyer']

    # LabelEncoder has classes_ attribute
    style_map = {str(label): int(idx) for idx, label in enumerate(le_style.classes_)}
    buyer_map = {str(label): int(idx) for idx, label in enumerate(le_buyer.classes_)}

    data = {
        "style_map": style_map,
        "buyer_map": buyer_map
    }

    with open("encoders.json", "w") as f:
        json.dump(data, f)
        
    print("Encoders exported to encoders.json")
except Exception as e:
    print(f"Error: {e}")
