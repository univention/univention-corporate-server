#!/usr/bin/make -f
# SPDX-FileCopyrightText: 2019-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

build: umc/js/admindiary.css

%.css: %.styl
	stylus "$<"

clean:
	rm -f umc/js/admindiary.css

