
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from summary_engine import SummaryEngine
from predict_engine import PredictEngine

print("Testing SummaryEngine...")
try:
    engine = SummaryEngine()
    test_rows = [{'efficiency': 80, 'buyer_name': 'TestBuyer'}]
    res = engine.generate_summary(test_rows, 'efficiency', {})
    print("SummaryEngine OK:", res)
except Exception as e:
    print("SummaryEngine FAILED:", e)

print("\nTesting PredictEngine...")
try:
    # We can't easily test predict without DB/Model, but we can check if class loads without import error
    predictor = PredictEngine()
    print("PredictEngine loaded:", predictor.loaded)
except Exception as e:
    print("PredictEngine FAILED:", e)
