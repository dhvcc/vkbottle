# Treat these arguments not as files, but as recipes
.PHONY: venv venv-no-dev githooks check fix publish autoflake_fix

# Used to execute all in one shell
.ONESHELL:

# Default recipe
DEFAULT: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Use poetry or activated venv
interpreter := $(shell poetry env info --path > /dev/null 2>&1 && echo "poetry run")
extract_ignores = $(shell awk '/.*.py/{split($$1,a,":"); print a[1]}' .flake8 | tr '\n' ',')

flake_ignores:
	@echo -n $(extract_ignores)

check-venv:
	$(if $(interpreter),, $(error No poetry environment found, either run "make venv"))

venv: ## Create virtual environment and install all dependencies
	@python3 -m pip install poetry
	@poetry install && \
	echo; echo "Poetry created virtual environment and installed all dependencies"

venv-no-dev: ## Create virtual environment and install only prod dependencies
	@python3 -m pip install poetry
	@poetry install --no-dev && \
	echo; echo "Poetry created virtual environment and installed only prod dependencies"

githooks: check-venv  ## Install git hooks
	@$(interpreter) pre-commit install -t=pre-commit -t=pre-push

check: check-venv ## Run tests and linters
	@echo "flake8"
	@echo "======"
	@$(interpreter) flake8
	@echo ; echo "black"
	@echo "====="
	@$(interpreter) black --check .
	@echo ; echo "isort"
	@echo "====="
	@$(interpreter) isort --check-only .
	@echo ; echo "mypy"
	@echo "===="
	@$(interpreter) mypy vkbottle
	@echo ; echo "pytest"
	@echo "======"
	@$(interpreter) pytest --cov vkbottle vkbottle

autoflake_fix:
	@$(interpreter) autoflake -i --remove-all-unused-imports --exclude $(extract_ignores) $(filename)

fix: check-venv ## Fix code with black and autoflake
	@echo "autoflake"
	@echo "========="
	@$(interpreter) autoflake -ri --remove-all-unused-imports --exclude $(extract_ignores) .
	@echo "black"
	@echo "====="
	@$(interpreter) black .
	@echo ; echo "isort"
	@echo "====="
	@$(interpreter) isort .

publish: ## Publish to PyPi using PYPI_TOKEN
	poetry build
	@poetry config pypi-token.pypi ${PYPI_TOKEN}
	@# "; true" is used to ignore command exit code so that rm -rf can execute anyway
	poetry publish; true
	rm -rf dist/
	extract_ignores=$(shell echo "$$(grep ':F401' .flake8 | sed -n 's/\s*\(\S*\):F401/\1,/p' | tr '\n' '\0')")
