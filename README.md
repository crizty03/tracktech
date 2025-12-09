# AI-Powered Garment Production Analytics Chatbot

A production-ready system to query 1 Million rows of garment production data using natural language, featuring an AI analytics engine and a Dashboard UI.

## 🚀 Features
- **Natural Language Querying**: "Show efficiency for H&M last week" -> SQL.
- **Micro-Batch Processing**: Optimized for large MySQL datasets (1M rows).
- **AI Summary Engine**: Generates insights, warnings, and recommendations.
- **Predictive Analytics**: Random Forest model to predict order completion.
- **Interactive UI**: Chat interface with dynamic Chart.js visualizations.

## 📂 Project Structure
```
.
├── main.py                 # FastAPI Backend
├── query_interpreter.py    # NLP Logic
├── summary_engine.py       # AI Insights Logic
├── train_model.py          # ML Model Training
├── import_data.py          # Data Generation & Import
├── schema.sql              # Database Schema
├── analysis.ipynb          # Data Analysis Notebook
├── requirements.txt        # Python Dependencies
└── frontend/
    └── index.html          # Chatbot UI
```

## 🛠️ Setup Instructions

### 1. Prerequisites
- Python 3.8+
- MySQL Server (Running)

### 2. Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn pandas mysql-connector-python scikit-learn joblib matplotlib tqdm
   ```

### 3. Database Setup
1. Open `import_data.py` and configure your MySQL credentials (if not `root`/no-password).
2. Run the import script to generate 1M dummy records and populate the DB:
   ```bash
   python import_data.py
   ```
   *Note: This may take a minute.*

### 4. Train ML Model
Train the predictive model:
```bash
python train_model.py
```
This saves `production_model.pkl`.

### 5. Run the Application
Start the backend server:
```bash
uvicorn main:app --reload
```
The API will run at `http://127.0.0.1:8000`.

### 6. Access the Dashboard
Open your browser and navigate to:
`http://127.0.0.1:8000/`

## 💡 Usage Examples
Try typing these queries in the chat:
- "Show efficiency for last week"
- "Give me rejection summary for H&M"
- "Fabric wastage report for Single Jersey"
- "Predict completion for style ST150"

## 🧪 API Endpoints
- `POST /ask`: Main NLP query endpoint.
- `POST /predict`: Prediction endpoint.
