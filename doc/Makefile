#!/usr/bin/make -f

# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2021-2023 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
#
# https://www.univention.com/
#
# All rights reserved.
#
# The source code of this program is made available under the terms of
# the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
# published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the AGPL-3.0-only.
#
# In the case you use this program under the terms of the AGPL-3.0-only,
# the program is provided in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/agpl-3.0.txt>.

mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir := $(dir $(mkfile_path))
DIRS := $(dir $(wildcard */Makefile))
PO_DIRS := $(dir $(wildcard */locales))
USER_ID := $(shell id -u)
LANGUAGE ?= de
SPHINXOPTS ?= "-q -W --keep-going"
DOCKER_REGISTRY := docker-registry.knut.univention.de
SPHINX_DOCKER_BASE = $(DOCKER_REGISTRY)/knut/sphinx-base:latest
SPHINX_DOCKER_FULL = $(DOCKER_REGISTRY)/sphinx:latest
DOCKER_USER_CMD := docker run --rm -v "$(mkfile_dir)..:/project" -w /project/doc --network=host -u "$(USER_ID)"
DOCKER_CMD := docker run --rm -v "$(mkfile_dir)..:/project" -w /project/doc --network=host

# Uses the default Sphinx environment in a Docker image to run the needed tools for Sphinx.
# Use this make target, when you want to update all po files in the documentation.
update-po:
	$(DOCKER_USER_CMD) $(SPHINX_DOCKER_BASE) make -e LANGUAGE="$(LANGUAGE)" update-po-nodocker

# Loop over all documents and update the PO files. Requires an environment with the Sphinx toolchain.
update-po-nodocker:
	set -e; for d in $(PO_DIRS); do d="$$d" sh -c 'cd "$$d" && make -e SPHINXOPTS="-q" gettext && sphinx-intl update -p _build/gettext -l "$(LANGUAGE)"'; done

stat-po:
	$(DOCKER_USER_CMD) $(SPHINX_DOCKER_BASE) make -e LANGUAGE="$(LANGUAGE)" stat-po-nodocker

stat-po-nodocker:
	set -e; for d in $(PO_DIRS); do d="$$d" sh -c 'cd "$$d" && echo "doc/$$d:" && sphinx-intl stat -l "$(LANGUAGE)"'; done

latexpdf:
	$(DOCKER_CMD) $(SPHINX_DOCKER_FULL) /bin/bash -c 'for d in $(DIRS);do make -C "$$d" -e SPHINXOPTS="$(SPHINXOPTS)" "$@"; done'

%:
	$(DOCKER_USER_CMD) $(SPHINX_DOCKER_BASE) /bin/bash -c 'for d in $(DIRS);do make -C "$$d" -e SPHINXOPTS="$(SPHINXOPTS)" "$@";done'

# vim:set bkc=auto:
