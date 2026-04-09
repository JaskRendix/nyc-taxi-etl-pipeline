# --- Variables ---
BACKEND_DIR = backend
FRONTEND_DIR = frontend
PYTHON = python3
PIPELINE = run_pipeline.py

# --- Commands ---

.PHONY: help setup db-up pipeline dev-ui dev-api dev clean

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install Python + Frontend dependencies
	pip install -r requirements.txt
	cd $(FRONTEND_DIR) && npm install

db-up: ## Start the Postgres Docker container
	docker-compose up -d

pipeline: ## Run the Python ETL process
	$(PYTHON) $(PIPELINE)

dev-api: ## Start the FastAPI backend
	cd $(BACKEND_DIR) && uvicorn main:app --reload --port 3001

dev-ui: ## Start the React / Vite frontend
	cd $(FRONTEND_DIR) && npm run dev

dev: ## Run Backend and Frontend together
	npx concurrently "make dev-api" "make dev-ui"

clean: ## Stop Docker and remove build artifacts
	docker-compose down
	rm -rf $(FRONTEND_DIR)/node_modules
	rm -rf $(FRONTEND_DIR)/dist
