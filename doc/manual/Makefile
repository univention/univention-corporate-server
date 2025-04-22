# SPDX-FileCopyrightText: 2021-2025 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

export SPHINXINTL_LANGUAGE ?= de
export SPHINXOPTS ?= -q -W --keep-going --color
export DOCS_PATH ?= $(pwd)

dir_root := $(shell git rev-parse --show-toplevel)
dir_git := $(realpath $(shell git rev-parse --git-common-dir))
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(notdir $(patsubst %/,%,$(dir $(mkfile_path))))

USER_ID := $(shell id -u)
DOCKER_REGISTRY := gitregistry.knut.univention.de
SPHINX_DOCKER_BASE = $(DOCKER_REGISTRY)/univention/dev/docs/sphinx-docker/base:latest
SPHINX_DOCKER_FULL = $(DOCKER_REGISTRY)/univention/dev/docs/sphinx-docker/pdf:latest
SPHINX_DOCKER = $(SPHINX_DOCKER_BASE)
DOCKER_CMD := docker run --interactive --tty --rm -v "$(dir_root):$(dir_root)" -v "$(dir_git):$(dir_git):ro" -w $(dir_root) --network=host --pull=always -e SPHINXINTL_LANGUAGE -e SPHINXOPTS -e HOME=/tmp -u "$(USER_ID)"
Q ?= @

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

livehtml:
	sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

.PHONY: docker-gettext
docker-gettext:
	${Q}$(DOCKER_CMD) $(SPHINX_DOCKER) /bin/sh -c '$(MAKE) -C "$(CURDIR)" gettext'

.PHONY: docker-html
docker-html:
	${Q}$(DOCKER_CMD) $(SPHINX_DOCKER) /bin/sh -c '$(MAKE) -C "$(CURDIR)" html'

.PHONY: docker-latexpdf
docker-latexpdf: SPHINX_DOCKER=$(SPHINX_DOCKER_FULL)
docker-latexpdf:
	${Q}$(DOCKER_CMD) $(SPHINX_DOCKER) /bin/sh -c '$(MAKE) -C "$(CURDIR)" latexpdf'

.PHONY: docker-linkcheck
docker-linkcheck:
	${Q}$(DOCKER_CMD) $(SPHINX_DOCKER) /bin/sh -c '$(MAKE) -C "$(CURDIR)" linkcheck'

.PHONY: docker-livehtml
docker-livehtml:
	${Q}$(DOCKER_CMD) $(SPHINX_DOCKER) /bin/sh -c '$(MAKE) -C "$(CURDIR)" livehtml'

.PHONY: docker-spelling
docker-spelling:
	${Q}$(DOCKER_CMD) $(SPHINX_DOCKER) /bin/sh -c '$(MAKE) -C "$(CURDIR)" spelling'

.PHONY: docker-update-po
docker-update-po:
	${Q}$(DOCKER_CMD) $(SPHINX_DOCKER) /bin/sh -c 'cd "$(CURDIR)" && sphinx-intl update -l $(SPHINXINTL_LANGUAGE)'

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
