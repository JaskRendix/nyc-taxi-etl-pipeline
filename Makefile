# --- Variables ---
BACKEND_DIR = backend
FRONTEND_DIR = frontend
PYTHON = python3
PIPELINE = run_pipeline.py

# --- Commands ---

.PHONY: help setup db-up pipeline dev-ui dev-api clean

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install everything (Python + Node + Prisma)
	pip install -r requirements.txt
	cd $(BACKEND_DIR) && npm install
	cd $(FRONTEND_DIR) && npm install
	cd $(BACKEND_DIR) && npx prisma generate

db-up: ## Start the Postgres Docker container
	docker-compose up -d

pipeline: ## Run the Python ETL process
	$(PYTHON) $(PIPELINE)

dev-api: ## Start the Node.js / Prisma Backend
	cd $(BACKEND_DIR) && npm run dev

dev-ui: ## Start the React / Vite Frontend
	cd $(FRONTEND_DIR) && npm run dev

dev: ## Run Backend and Frontend together (Requires 'npm install -g concurrently')
	npx concurrently "make dev-api" "make dev-ui"

clean: ## Stop Docker and remove build artifacts
	docker-compose down
	rm -rf $(BACKEND_DIR)/node_modules $(FRONTEND_DIR)/node_modules
	rm -rf $(BACKEND_DIR)/dist $(FRONTEND_DIR)/dist
