# NYC Taxi ETL Pipeline

This project processes NYC Yellow Taxi trip data and exposes the cleaned results through a small full‑stack system.  
It includes a Python ETL pipeline, a PostgreSQL database, a Node.js API, and a React dashboard.

The goal is to show a clear end‑to‑end flow: raw data → cleaned data → database → API → UI.

## Project Structure

```
nyc-taxi-etl-pipeline/
├── pipeline/               # Python ETL logic
├── data/                   # Raw input files
├── output/                 # Cleaned output files
├── docker-compose.yml      # PostgreSQL service
│
├── backend/                # Node.js + Express + Prisma API
│   ├── prisma/schema.prisma
│   └── src/server.ts
│
├── frontend/               # React + Vite + Tailwind dashboard
│   └── src/components/Dashboard.tsx
│
└── Makefile                # Unified commands
```

---

# Setup

## 1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## 2. Install all dependencies

This installs Python packages, Node packages, and generates the Prisma client.

```bash
make setup
```

## 3. Start PostgreSQL

```bash
make db-up
```

This starts a PostgreSQL 15 container with a `taxi` database.

---

# Run the ETL Pipeline

```bash
make pipeline
```

The pipeline performs four steps:

1. Extract data from CSV or Parquet  
2. Transform it using rules defined in `config.yaml`  
3. Validate schema and logical constraints  
4. Load cleaned data into:
   - `output/cleaned_output.csv`
   - the `yellowcab_cleaned` table in PostgreSQL

---

# Backend API

The backend is a small Node.js service built with Express and Prisma.  
It exposes cleaned data through a simple HTTP API.

Start the backend:

```bash
make dev-api
```

The server runs on:

```
http://localhost:3001
```

Example endpoint:

```
GET /api/stats
```

This returns basic statistics from the `yellowcab_cleaned` table.

---

# Frontend Dashboard

The frontend is a React application styled with Tailwind.  
It displays summary metrics and can be extended with charts and maps.

Start the frontend:

```bash
make dev-ui
```

The dashboard runs on:

```
http://localhost:5173
```

---

# Run Backend and Frontend Together

```bash
make dev
```

This starts both services in parallel.

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

This stops Docker and removes build folders.
