import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import random

# Intents
INTENTS = {
    'PREDICTION': [
        "predict completion for style {}", "when will order {} finish", "how many days for {}",                     
        "forecast for style {}", "completion date of {}", "how long to finish {}",
        "prediction for {}", "predict {}"
    ],
    'EFFICIENCY': [
        "show efficiency for {}", "efficiency of line {}", "performance of buyer {}",
        "how is line {} performing", "efficiency report for {}", "line {} efficiency"
    ],
    'WASTAGE': [
        "show wastage for {}", "fabric wastage report", "fabric loss for {}",
        "how much wastage in {}", "wastage percent for {}", "scrap report {}"
    ],
    'PRODUCTION': [
        "production summary", "show production for {}", "how many pieces made",
        "total output for {}", "production report {}", "output of {}",
        "adidas", "nike", "h&m", "show me adidas", "puma status", "uniqlo report"
    ],
    'GENERAL': [
        "hello", "hi", "who are you", "help", "what can you do", "stats",
        "good morning"
    ]
}

ENTITIES = ["ST150", "ST100", "Adidas", "Nike", "H&M", "Line 1", "Line 5", "last week", "yesterday"]

def generate_dataset(n_samples=500):
    data = []
    labels = []
    
    print(f"Generating synthetic dataset with {n_samples} samples...")
    
    for _ in range(n_samples):
        intent_name = random.choice(list(INTENTS.keys()))
        template = random.choice(INTENTS[intent_name])
        
        # Fill entity placeholders if any
        if "{}" in template:
            entity = random.choice(ENTITIES)
            text = template.format(entity)
        else:
            text = template
            
        data.append(text)
        labels.append(intent_name)
        
    return pd.DataFrame({'text': data, 'intent': labels})

def train_nlp_model():
    df = generate_dataset(1000)
    
    X_train, X_test, y_train, y_test = train_test_split(df['text'], df['intent'], test_size=0.2, random_state=42)
    
    print("Training NLP Intent Classifier (TF-IDF + LogReg)...")
    
    # Simple but effective pipeline for short text classification
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), stop_words='english')),
        ('clf', LogisticRegression(random_state=42))
    ])
    
    pipeline.fit(X_train, y_train)
    
    # Evaluate
    preds = pipeline.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, preds))
    
    # Save
    joblib.dump(pipeline, 'nlp_model.pkl')
    print("NLP Model saved to 'nlp_model.pkl'")

if __name__ == "__main__":
    train_nlp_model()
