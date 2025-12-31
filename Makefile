# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

.PHONY: help format format-all lint lint-all setup_devel_env ucr ruff isort autopep8 ruff-statistics reuse copyright
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
	{ git diff --name-only; git ls-files --others --exclude-standard; git diff --cached --name-only; } | xargs prek run --files

lint-all: ## This checks all python files in the repository
	prek run -a

ucr:  ## This formats all UCR templates correctly
	-{ git diff --name-only; git ls-files --others --exclude-standard; git diff --cached --name-only; } | xargs prek run --hook-stage manual ucr-autopep8 --files
	-{ git diff --name-only; git ls-files --others --exclude-standard; git diff --cached --name-only; } | xargs prek run --hook-stage manual ucr-ruff-fix --files

ruff:  ## This runs ruff fixes on Python files
	-{ git diff --name-only; git ls-files --others --exclude-standard; git diff --cached --name-only; } | xargs prek run --hook-stage manual ruff-fix --files

ruff-statistics:
	prek run -a --hook-stage manual ruff-statistics

isort:  ## This runs isort on Python files
	-{ git diff --name-only; git ls-files --others --exclude-standard; git diff --cached --name-only; } | xargs prek run --hook-stage manual isort-fix --files

autopep8:  ## this runs isort on Python files
	-{ git diff --name-only; git ls-files --others --exclude-standard; git diff --cached --name-only; } | xargs prek run --hook-stage manual autopep8-fix --files

reuse:
	-{ git diff --name-only; git ls-files --others --exclude-standard; git diff --cached --name-only; } | xargs prek run --hook-stage manual reuse-annotate --files

format: ucr ruff isort autopep8 reuse  ## This formats all changed python files.
	-

format-all: ## This formats all python files in the repository
	-prek run -a --hook-stage manual ucr-autopep8
	-prek run -a --hook-stage manual ucr-ruff-fix
	-prek run -a --hook-stage manual ruff-fix
	-prek run -a --hook-stage manual isort-fix
	-prek run -a --hook-stage manual autopep8-fix
	-prek run -a --hook-stage manual reuse-toml
	-prek run -a --hook-stage manual reuse-annotate

copyright:
	-prek run -a --hook-stage manual update-copyright-year
	-prek run -a --hook-stage manual reuse-toml
	-prek run -a --hook-stage manual reuse-annotate
	-prek run -a --hook-stage manual reuse-lint
