# SPDX-License-Identifier: Apache-2.0

.DEFAULT_GOAL := help

PYTHON := python3
SYNC_SCRIPT := scripts/sync-org-repositories.py

##@ General

.PHONY: help
help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Lint

.PHONY: lint
lint: lint-yaml lint-python ## Run all linters

.PHONY: lint-yaml
lint-yaml: ## Lint YAML files
	yamllint -c .yamllint.yml .

.PHONY: lint-python
lint-python: ## Lint Python files
	ruff check scripts/

##@ Sync

.PHONY: sync-dry-run
sync-dry-run: ## Run sync script in dry-run mode
	$(PYTHON) $(SYNC_SCRIPT) --org complytime --dry-run

##@ Test

.PHONY: test
test: ## Run tests
	$(PYTHON) -m pytest tests/ -v

##@ Clean

.PHONY: clean
clean: ## Remove generated artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
