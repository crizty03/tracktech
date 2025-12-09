
import joblib
import numpy as np
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import onnx

# Load Model
print("Loading model...")
artifacts = joblib.load('model_order_completion.pkl')
model = artifacts['model']
print("Model loaded.")

# Define input type: 11 float features
# feature_cols = ['style_encoded', 'buyer_encoded', 'order_quantity', 'cumulative_achieved', 'remaining_qty', 'daily_efficiency', 'efficiency_trend', 'fabric_variance', 'hour_output', 'rejection', 'line_no']
initial_type = [('float_input', FloatTensorType([None, 11]))]

# Convert
print("Converting to ONNX...")
onx = convert_sklearn(model, initial_types=initial_type)

# Save
with open("model_order_completion.onnx", "wb") as f:
    f.write(onx.SerializeToString())

print("ONNX model saved to 'model_order_completion.onnx'")
