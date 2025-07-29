#!/usr/bin/make -f
#
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

.PRECIOUS: build build-dev

build:
	./frontend/process_vue_files.sh
	npm set prefix=$$HOME/.node
	npm install -g npm@8.1.3
	$$HOME/.node/bin/npm install -g yarn
	cd frontend && $$HOME/.node/bin/yarn install
	cd frontend && NODE_OPTIONS=--openssl-legacy-provider $$HOME/.node/bin/yarn build
