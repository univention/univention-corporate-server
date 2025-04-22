#!/usr/bin/make -f

# SPDX-FileCopyrightText: 2021-2025 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

DIRS := $(patsubst %/,%,$(dir $(wildcard */Makefile)))
PO_DIRS := $(patsubst %/,%,$(dir $(foreach d,$(DIRS),$(wildcard $(d)/locales))))

export SPHINXINTL_LANGUAGE ?= de
export SPHINXOPTS ?= -q -W --keep-going

dir_root := $(shell git rev-parse --show-toplevel)
dir_git := $(realpath $(shell git rev-parse --git-common-dir))
dir_doc := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

USER_ID := $(shell id -u)
DOCKER_REGISTRY := gitregistry.knut.univention.de
SPHINX_DOCKER_BASE = $(DOCKER_REGISTRY)/univention/dev/docs/sphinx-docker/base:latest
SPHINX_DOCKER_FULL = $(DOCKER_REGISTRY)/univention/dev/docs/sphinx-docker/pdf:latest

SPHINX_DOCKER = $(SPHINX_DOCKER_BASE)
DOCKER_CMD := docker run --rm -v "$(dir_root):$(dir_root)" -v "$(dir_git):$(dir_git):ro" -w "$(dir_doc)" --network=host -e SPHINXINTL_LANGUAGE -e SPHINXOPTS -e HOME=/tmp -u "$(USER_ID)"
Q ?= @
unexport CDPATH

.PHONY: update-po-all
update-po-all:
	${Q} $(MAKE) clean html
	${Q} $(MAKE) html
	${Q} $(MAKE) update-po

.PHONY: update-po stat-po
update-po stat-po:
	${Q}$(DOCKER_CMD) $(SPHINX_DOCKER) $(MAKE) $@-nodocker

.PHONY: update-po-nodocker
update-po-nodocker:
	${Q}set -e; for d in $(PO_DIRS); do ( cd "$$d" && $(MAKE) -e SPHINXOPTS=-q gettext && sphinx-intl update -p _build/gettext; ); done

.PHONY: stat-po-nodocker
stat-po-nodocker:
	${Q}set -e; for d in $(PO_DIRS); do ( cd "$$d" && echo "doc/$$d:" && sphinx-intl stat; ); done

.PHONY: latexpdf
latexpdf: SPHINX_DOCKER=$(SPHINX_DOCKER_FULL)

%:
	${Q}$(DOCKER_CMD) $(SPHINX_DOCKER) /bin/sh -c 'for d in $(DIRS); do $(MAKE) -C "$$d" "$@"; done'

# vim:set bkc=auto:
