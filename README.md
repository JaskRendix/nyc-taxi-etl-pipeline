# NYC Taxi ETL Pipeline

This project processes NYC Yellow Taxi trip data. System components include a Python ETL pipeline, a PostgreSQL database, a FastAPI backend, a React dashboard, and a scikit-learn regression model.

Data flow: raw data $\rightarrow$ database $\rightarrow$ API $\rightarrow$ UI.

---

# Project Structure

```
nyc-taxi-etl-pipeline/
├── pipeline/               # ETL and ML scripts
├── backend/                # FastAPI backend
│   └── core/               # Model binaries and metrics
├── frontend/               # React dashboard
├── tests/                  # Test suite
├── data/                   # Input files
├── output/                 # Output files
├── config.yaml             # Pipeline configuration
├── docker-compose.yml      # PostgreSQL container definition
└── Makefile                # Task runner
```

---

# Setup

## 1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## 2. Install dependencies

```bash
make setup
```

## 3. Start PostgreSQL

```bash
make db-up
```

---

# Run the ETL Pipeline

```bash
make pipeline
```

```mermaid
flowchart LR
    A[Extract] --> B[Transform]
    B --> C[Validate]
    C --> D[Load]
```

Pipeline steps:

1. Extract data from disk.
2. Transform data using rules from `config.yaml`.
3. Validate schema and logical constraints.
4. Load data into `output/cleaned_output.csv` and the PostgreSQL table `yellowcab_cleaned`.

---

# Train the ML Model

```bash
make train
```

```mermaid
flowchart LR
    A[Load from DB] --> B[Extract Features]
    B --> C[Train Linear Regression]
    C --> D[Save Artifacts]
```

This script:

1. Connects to PostgreSQL to read the cleaned dataset.
2. Extracts feature columns.
3. Trains a Linear Regression model.
4. Computes evaluation metrics (MAE, RMSE, R²).
5. Saves model binaries to `backend/core/fare_model.pkl` and metrics to `backend/core/metrics.json`.

---

# Backend API (FastAPI)

```bash
make dev-api
```

The server runs on `http://localhost:3001`.

Key endpoints:

* `GET /api/stats` — Returns table statistics.
* `POST /api/predict` — Loads the trained model and returns a predicted fare amount.

---

# Frontend Dashboard

```bash
make dev-ui
```

The dashboard runs on `http://localhost:5173`. Uses React 18.

---

# Run Backend and Frontend Together

```bash
make dev
```

---

# Verify Data in PostgreSQL

```bash
docker exec -it taxi_postgres psql -U postgres -d taxi
SELECT COUNT(*) FROM yellowcab_cleaned;
```

---

# Clean Up

```bash
make clean
```
