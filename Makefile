.PHONY: help format lint setup_devel_env
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:
	@python3 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

lint: ## This checks python files modified by you.
	{ git diff --name-only; git ls-files --others --exclude-standard; git diff --cached --name-only; } | xargs pre-commit run --files

lint-all: ## This checks all python files in the repository
	pre-commit run -a

format: ## This formats all changed python files.
	-{ git diff --name-only; git ls-files --others --exclude-standard; git diff --cached --name-only; } | xargs pre-commit run --hook-stage manual ucr-autopep8 --files
	-{ git diff --name-only; git ls-files --others --exclude-standard; git diff --cached --name-only; } | xargs pre-commit run --hook-stage manual ucr-ruff-fix --files
	-{ git diff --name-only; git ls-files --others --exclude-standard; git diff --cached --name-only; } | xargs pre-commit run --hook-stage manual ruff-fix --files
	-{ git diff --name-only; git ls-files --others --exclude-standard; git diff --cached --name-only; } | xargs pre-commit run --hook-stage manual isort-fix --files
	-{ git diff --name-only; git ls-files --others --exclude-standard; git diff --cached --name-only; } | xargs pre-commit run --hook-stage manual autopep8-fix --files

format-all: ## This formats all python files in the repository
	-pre-commit run -a --hook-stage manual ucr-autopep8
	-pre-commit run -a --hook-stage manual ucr-ruff-fix
	-pre-commit run -a --hook-stage manual ruff-fix
	-pre-commit run -a --hook-stage manual isort-fix
	-pre-commit run -a --hook-stage manual autopep8-fix
