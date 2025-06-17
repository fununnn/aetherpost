.PHONY: help install test lint format type-check clean build run docker-build docker-run prod-deploy prod-stop prod-logs

# Default target
help:
	@echo "AetherPost Development Commands"
	@echo "=============================="
	@echo "install     - Install dependencies with Poetry"
	@echo "test        - Run tests with pytest"
	@echo "lint        - Run linting with flake8"
	@echo "format      - Format code with black"
	@echo "type-check  - Run type checking with mypy"
	@echo "clean       - Clean build artifacts"
	@echo "build       - Build package"
	@echo "run         - Run AetherPost CLI"
	@echo "docker-build - Build Docker image"
	@echo "docker-run  - Run in Docker container"

# Development setup
install:
	poetry install

# Testing
test:
	poetry run pytest tests/ -v

test-cov:
	poetry run pytest tests/ -v --cov=aetherpost --cov-report=html

# Code quality
lint:
	poetry run flake8 aetherpost tests

format:
	poetry run black aetherpost tests

format-check:
	poetry run black --check aetherpost tests

type-check:
	poetry run mypy aetherpost

# Security checks
security:
	poetry run safety check
	poetry run bandit -r aetherpost/

# All checks
check: lint format-check type-check security test

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Build
build: clean
	poetry build

# Run CLI
run:
	poetry run aetherpost

init:
	poetry run aetherpost init

plan:
	poetry run aetherpost plan

apply:
	poetry run aetherpost apply

stats:
	poetry run aetherpost stats

# Docker commands
docker-build:
	docker build -t aetherpost:latest .

docker-run:
	docker-compose run --rm aetherpost

docker-dev:
	docker-compose --profile dev run --rm aetherpost-dev

docker-web:
	docker-compose --profile web up aetherpost-web

# Development helpers
dev-setup: install
	pre-commit install
	@echo "Development environment setup complete!"

example:
	@echo "Creating example campaign..."
	@mkdir -p example
	@cd example && poetry run aetherpost init template example-app --type minimal
	@echo "Example created in ./example/"

demo: example
	@echo "Running demo campaign..."
	@cd example && poetry run aetherpost plan
	@echo "Demo plan complete. Run 'make demo-apply' to execute (requires credentials)"

demo-apply:
	@cd example && poetry run aetherpost apply --dry-run

# Release helpers
version:
	@poetry version

bump-patch:
	poetry version patch

bump-minor:
	poetry version minor

bump-major:
	poetry version major

# Documentation
docs:
	@echo "AetherPost Documentation"
	@echo "======================"
	@echo "See README.md for full documentation"
	@echo ""
	@echo "Quick Start:"
	@echo "1. make install"
	@echo "2. make example"
	@echo "3. make demo"

# Install pre-commit hooks
hooks:
	pre-commit install
	pre-commit run --all-files

# Quick commands for common workflows
quick-test: format lint test
	@echo "✅ Quick test suite passed!"

# Cleanup commands
clean-docker:
	@echo "🧹 Cleaning Docker resources..."
	docker system prune -f
	docker volume prune -f

clean-all: clean clean-docker
	@echo "🧹 Deep clean complete"

# Development debugging
debug:
	@echo "🔍 Debug information:"
	@echo "AetherPost Version: $(shell poetry version --short)"
	@echo "Python Version: $(shell python --version)"
# Documentation building and deployment
build-docs:
	@echo "🔨 Building documentation..."
	./scripts/build-docs.sh
	@echo "✅ Documentation built in docs-site/"

deploy-docs: build-docs
	@echo "🚀 Deploying documentation to S3..."
	./scripts/deploy-docs.sh

serve-docs: build-docs
	@echo "🌐 Serving documentation locally..."
	@echo "Open http://localhost:8000 in your browser"
	@cd docs-site && python -m http.server 8000
