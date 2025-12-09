
import numpy as np
import sklearn
import joblib

print("Core ML libraries imported successfully.")

# Test code simulation
try:
    import pandas
    print("WARNING: Pandas is still importable (local env?), but should not be used.")
except ImportError:
    print("Success: Pandas is not available.")
