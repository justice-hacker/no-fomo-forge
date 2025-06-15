# NFT Batch Minter - Makefile
# Common development and deployment tasks

.PHONY: help setup install test clean run format lint

# Default target
help:
	@echo "NFT Batch Minter - Development Commands"
	@echo "======================================"
	@echo "make setup      - Set up the project (create venv and install deps)"
	@echo "make install    - Install dependencies in existing venv"
	@echo "make test       - Run all tests"
	@echo "make clean      - Clean up generated files and directories"
	@echo "make run        - Run the minter with default configuration"
	@echo "make format     - Format code with black (if installed)"
	@echo "make lint       - Run linting checks (if flake8 installed)"
	@echo "make example    - Create example configuration files"

# Set up the complete project
setup:
	@echo "Setting up NFT Batch Minter..."
	@python3 setup.py

# Install dependencies in current environment
install:
	@echo "Installing dependencies..."
	@pip install -r requirements.txt

# Run all tests
test:
	@echo "Running tests..."
	@python run_tests.py

# Run specific test
test-config:
	@python run_tests.py tests.test_config

test-minter:
	@python run_tests.py tests.test_minter

test-utils:
	@python run_tests.py tests.test_utils

# Clean up generated files
clean:
	@echo "Cleaning up..."
	@rm -rf __pycache__ src/__pycache__ tests/__pycache__
	@rm -rf .pytest_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@rm -rf *.egg-info
	@rm -rf build dist
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@echo "Clean complete!"

# Run the minter
run:
	@python main.py

# Run with verbose output
run-verbose:
	@python main.py -v

# Run in dry-run mode
dry-run:
	@python main.py --dry-run -v

# Format code (requires black)
format:
	@if command -v black >/dev/null 2>&1; then \
		echo "Formatting code with black..."; \
		black src/ tests/ main.py setup.py run_tests.py; \
	else \
		echo "Black not installed. Install with: pip install black"; \
	fi

# Lint code (requires flake8)
lint:
	@if command -v flake8 >/dev/null 2>&1; then \
		echo "Linting code with flake8..."; \
		flake8 src/ tests/ main.py --max-line-length=100 --ignore=E501,W503; \
	else \
		echo "Flake8 not installed. Install with: pip install flake8"; \
	fi

# Create example configuration files
example:
	@echo "Creating example configuration files..."
	@cp config.example.json config.json 2>/dev/null || echo "config.json already exists"
	@cp .env.example .env 2>/dev/null || echo ".env already exists"
	@echo "Example files created. Please update with your values."

# Development environment setup (with dev dependencies)
dev-setup: setup
	@echo "Installing development dependencies..."
	@pip install pytest pytest-cov black flake8 mypy

# Run tests with coverage
coverage:
	@if command -v pytest >/dev/null 2>&1; then \
		echo "Running tests with coverage..."; \
		pytest tests/ --cov=src --cov-report=html --cov-report=term; \
	else \
		echo "Pytest not installed. Install with: pip install pytest pytest-cov"; \
	fi

# Type checking (requires mypy)
typecheck:
	@if command -v mypy >/dev/null 2>&1; then \
		echo "Running type checks..."; \
		mypy src/ --ignore-missing-imports; \
	else \
		echo "Mypy not installed. Install with: pip install mypy"; \
	fi