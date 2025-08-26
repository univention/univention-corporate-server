#!/usr/bin/make -f
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

build: umc/js/appcenter.css

%.css: %.styl
	stylus "$<"

clean:
	rm -f umc/js/appcenter.css

