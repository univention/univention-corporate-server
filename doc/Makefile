#!/usr/bin/make -f

# SPDX-FileCopyrightText: 2021-2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir := $(dir $(mkfile_path))
DIRS := $(dir $(wildcard */Makefile))
PO_DIRS := $(dir $(wildcard */locales))
USER_ID := $(shell id -u)
TARGET_LANG ?= de
SPHINXOPTS ?= "-q -W --keep-going"
DOCKER_REGISTRY := docker-registry.knut.univention.de
SPHINX_DOCKER_BASE = $(DOCKER_REGISTRY)/knut/sphinx-base:latest
SPHINX_DOCKER_FULL = $(DOCKER_REGISTRY)/sphinx:latest
DOCKER_USER_CMD := docker run --rm --pull always -v "$(mkfile_dir)..:/project" -w /project/doc --network=host -u "$(USER_ID)"
DOCKER_CMD := docker run --rm --pull always -v "$(mkfile_dir)..:/project" -w /project/doc --network=host

# Uses the default Sphinx environment in a Docker image to run the needed tools for Sphinx.
# Use this make target, when you want to update all po files in the documentation.
update-po:
	$(DOCKER_USER_CMD) $(SPHINX_DOCKER_BASE) make -e TARGET_L="$(TARGET_LANG)" update-po-nodocker

# Loop over all documents and update the PO files. Requires an environment with the Sphinx toolchain.
update-po-nodocker:
	set -e; for d in $(PO_DIRS); do d="$$d" sh -c 'cd "$$d" && make -e SPHINXOPTS="-q" gettext && sphinx-intl update -p _build/gettext -l "$(TARGET_L)"'; done

stat-po:
	$(DOCKER_USER_CMD) $(SPHINX_DOCKER_BASE) make -e TARGET_L="$(TARGET_LANG)" stat-po-nodocker

stat-po-nodocker:
	set -e; for d in $(PO_DIRS); do d="$$d" sh -c 'cd "$$d" && echo "doc/$$d:" && sphinx-intl stat -l "$(TARGET_L)"'; done

latexpdf:
	$(DOCKER_CMD) $(SPHINX_DOCKER_FULL) /bin/bash -c 'for d in $(DIRS);do make -C "$$d" -e SPHINXOPTS="$(SPHINXOPTS)" "$@"; done'

%:
	$(DOCKER_USER_CMD) $(SPHINX_DOCKER_BASE) /bin/bash -c 'for d in $(DIRS);do make -C "$$d" -e SPHINXOPTS="$(SPHINXOPTS)" "$@";done'

# vim:set bkc=auto:
