# -----------------------------
# NYC Taxi ETL Pipeline Makefile
# -----------------------------

.PHONY: help venv install db stop-db logs run clean dashboard

help:
    @echo "Available commands:"
    @echo "  make venv        Create virtual environment"
    @echo "  make install     Install Python dependencies"
    @echo "  make db          Start PostgreSQL via Docker"
    @echo "  make stop-db     Stop PostgreSQL container"
    @echo "  make run         Run the ETL pipeline"
    @echo "  make dashboard   Launch Streamlit dashboard"
    @echo "  make clean       Remove Python cache files"

# -----------------------------
# Virtual environment
# -----------------------------

venv:
    python3 -m venv venv

install:
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt

# -----------------------------
# Docker database
# -----------------------------

db:
    docker-compose up -d

stop-db:
    docker-compose down

logs:
    docker logs -f taxi_postgres

# -----------------------------
# Run pipeline
# -----------------------------

run:
    ./venv/bin/python3 run_pipeline.py

# -----------------------------
# Streamlit dashboard
# -----------------------------

dashboard:
    ./venv/bin/streamlit run dashboard/app.py

# -----------------------------
# Cleanup
# -----------------------------

clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
