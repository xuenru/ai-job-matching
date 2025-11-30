.PHONY: help sync install-dev format lint type-check test test-cov clean run

help:
	@echo "Available commands:"
	@echo "  make sync          - Sync dependencies with uv"
	@echo "  make install-dev   - Install with dev dependencies"
	@echo "  make format        - Format code with black and isort"
	@echo "  make lint          - Lint code with ruff"
	@echo "  make type-check    - Type check with mypy"
	@echo "  make test          - Run tests with pytest"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make clean         - Remove cache and build artifacts"
	@echo "  make run           - Run the job matching pipeline"
	@echo "  make check-all     - Run all checks (format, lint, type-check, test)"

sync:
	uv sync

install-dev:
	uv sync --extra dev

format:
	@echo "Running isort..."
	uv run isort agents/ core/ workflows/ tests/ cli.py
	@echo "Running black..."
	uv run black agents/ core/ workflows/ tests/ cli.py
	@echo "✓ Code formatted successfully"

lint:
	@echo "Running ruff..."
	uv run ruff check agents/ core/ workflows/ tests/ cli.py
	@echo "✓ Linting complete"

type-check:
	@echo "Running mypy..."
	uv run mypy agents/ core/ workflows/ cli.py
	@echo "✓ Type checking complete"

test:
	@echo "Running tests..."
	uv run pytest tests/
	@echo "✓ Tests complete"

test-cov:
	@echo "Running tests with coverage..."
	uv run pytest tests/ --cov=agents --cov=core --cov=workflows --cov-report=term-missing --cov-report=html
	@echo "✓ Coverage report generated in htmlcov/"

clean:
	@echo "Cleaning cache and artifacts..."
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .mypy_cache .ruff_cache .pytest_cache
	rm -rf htmlcov/ .coverage
	rm -rf cache/*.json cache/*.log
	rm -rf output/*.json
	@echo "✓ Clean complete"

run:
	@echo "Running job matching pipeline..."
	uv run python cli.py run-all

check-all: format lint type-check test
	@echo "✓ All checks passed!"
