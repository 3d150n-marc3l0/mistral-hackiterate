# --- Variables ---
IMAGE_NAME = sentinel-daily
PORT = 8501

# --- Docker Commands ---

.PHONY: build
build: ## Build the Docker image
	docker build -t $(IMAGE_NAME) .

.PHONY: up
up: ## Run the container
	docker run -d --name $(IMAGE_NAME) -p $(PORT):$(PORT) --env-file .env $(IMAGE_NAME)

.PHONY: down
down: ## Stop and remove the container
	docker stop $(IMAGE_NAME) || true
	docker rm $(IMAGE_NAME) || true

.PHONY: logs
logs: ## Show container logs
	docker logs -f $(IMAGE_NAME)

# --- Local Commands (without Docker) ---

.PHONY: run
run: ## Run the app locally with uv
	uv run streamlit run src/sentinel/app.py

.PHONY: test
test: ## Run tests with uv
	uv run pytest tests/ -v

# --- Maintenance ---

.PHONY: clean
clean: ## Clean generated logs, outputs and python cache
	rm -rf logs/*
	rm -rf outputs/*
	find . -type d -name "__pycache__" -exec rm -rf {} +

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
