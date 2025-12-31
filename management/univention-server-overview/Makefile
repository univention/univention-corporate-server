#!/usr/bin/make -f
# SPDX-FileCopyrightText: 2017-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

build: www/style.css

%.css: %.styl
	stylus "$<"

clean:
	rm -f www/style.css
