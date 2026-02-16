# 🚕 NYC Taxi ETL Pipeline

A production‑style ETL pipeline for processing NYC Yellow Taxi trip data.  
It demonstrates a clean, modular architecture with extraction, transformation, validation, and loading into a Dockerized PostgreSQL database.

## ✨ Features
- Modular ETL structure (`extract/transform/validate/load`)
- Config‑driven thresholds and file paths (`config.yaml`)
- Logging for traceable execution
- Data validation with schema and logical checks
- Dockerized PostgreSQL for reproducible loading
- Virtual environment isolation
- Ready for extension (Streamlit, clustering, APIs, Airflow)

## 📦 Setup

### 1. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Start PostgreSQL via Docker
```bash
docker-compose up -d
```

This launches a Postgres 15 instance on port **5432** with a `taxi` database.

## ▶️ Run the Pipeline
```bash
python3 run_pipeline.py
```

The pipeline will:

1. **Extract** data from CSV/Parquet  
2. **Transform** it using config‑driven rules  
3. **Validate** schema and logical constraints  
4. **Load** cleaned data into:
   - `output/cleaned_output.csv`
   - PostgreSQL table `yellowcab_cleaned`

## 🗄 Verify Data in PostgreSQL (optional)
```bash
docker exec -it taxi_postgres psql -U postgres -d taxi
SELECT COUNT(*) FROM yellowcab_cleaned;
```
