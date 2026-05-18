# SPDX-License-Identifier: Apache-2.0

.DEFAULT_GOAL := help

PYTHON := python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python3
VENV_PIP := $(VENV)/bin/pip
SYNC_SCRIPT := scripts/sync-org-repositories.py

##@ General

.PHONY: help
help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Setup

.PHONY: venv
venv: $(VENV)/bin/activate ## Create Python virtual environment and install dependencies

$(VENV)/bin/activate: requirements.txt
	@if [ -d "$(VENV)" ]; then \
		echo "Updating Python virtual environment in $(VENV)..."; \
		$(VENV_PIP) install --upgrade pip; \
		$(VENV_PIP) install -r requirements.txt; \
		touch $(VENV)/bin/activate; \
	else \
		echo "Creating Python virtual environment in $(VENV)..."; \
		$(PYTHON) -m venv $(VENV); \
		echo "Installing dependencies..."; \
		$(VENV_PIP) install --upgrade pip; \
		$(VENV_PIP) install -r requirements.txt; \
	fi
	@echo ""
	@echo "✓ Virtual environment ready at $(VENV)"
	@echo ""
	@echo "To activate the virtual environment, run:"
	@echo "  source $(VENV)/bin/activate"
	@echo ""

##@ Lint

.PHONY: lint
lint: lint-yaml lint-python ## Run all linters

.PHONY: lint-yaml
lint-yaml: $(VENV)/bin/activate ## Lint YAML files
	@echo "Linting YAML files..."
	@$(VENV)/bin/yamllint -c .yamllint.yml .

.PHONY: lint-python
lint-python: $(VENV)/bin/activate ## Lint Python files
	@echo "Linting Python files..."
	@$(VENV)/bin/ruff check scripts/ tests/

##@ Sync

.PHONY: sync-dry-run
sync-dry-run: $(VENV)/bin/activate ## Run sync script in dry-run mode
	@echo "Running sync script in dry-run mode..."
	@$(VENV_PYTHON) $(SYNC_SCRIPT) --org complytime --dry-run

##@ Test

.PHONY: test
test: $(VENV)/bin/activate ## Run all tests
	@echo "Running all tests..."
	@$(VENV_PYTHON) -m pytest tests/ -v

##@ Clean

.PHONY: clean
clean: ## Remove generated artifacts (cache, pyc files)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf megalinter-reports

.PHONY: clean-venv
clean-venv: ## Remove Python virtual environment
	rm -rf $(VENV)
