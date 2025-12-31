#!/usr/bin/make -f
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

SRC := $(wildcard usr/lib/nagios/plugins/check_univention_*_suidwrapper.c)
BIN := $(patsubst %.c,%,$(SRC))

all: $(BIN)

clean:
	$(RM) $(BIN)
