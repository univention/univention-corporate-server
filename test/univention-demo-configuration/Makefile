#!/usr/bin/make -f
# SPDX-FileCopyrightText: 2017-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

ALL += usr/share/univention-web/js/umc/hooks/univention_demo.css
ALL += portal/background.jpg.b64

build: $(ALL)

%.css: %.styl
	stylus "$<"

%.b64: %
	base64 "$<" >"$@"

clean:
	$(RM) $(ALL)
