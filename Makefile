# Treat these arguments not as files, but as recipes
.PHONY: venv venv-no-dev githooks check fix publish

# Used to execute all in one shell
.ONESHELL:

# Default recipe
DEFAULT: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Use poetry or activated venv
interpreter := $(shell poetry env info --path > /dev/null 2>&1 && echo "poetry run")

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
	@echo -e "\nblack"
	@echo "====="
	@$(interpreter) black --check .
	@echo -e "\nisort"
	@echo "====="
	@$(interpreter) isort --check-only .
	@echo -e "\nmypy"
	@echo "===="
	@$(interpreter) mypy vkbottle
	@echo -e "\npytest"
	@echo "======"
	@$(interpreter) pytest --cov vkbottle tests

fix: check-venv ## Fix code with black and autoflake
	@echo "black"
	@echo "====="
	@$(interpreter) black .
	@echo -e "\nisort"
	@echo "====="
	@$(interpreter) isort .

publish: ## Publish to PyPi using PYPI_TOKEN
	poetry build
	@poetry config pypi-token.pypi ${PYPI_TOKEN}
	@# "; true" is used to ignore command exit code so that rm -rf can execute anyway
	poetry publish; true
	rm -rf dist/
