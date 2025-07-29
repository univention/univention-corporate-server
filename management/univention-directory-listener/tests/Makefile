#
# Univention Directory Listener
#  Makefile for testing the listener
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
SOURCES := $(wildcard test__*.c)
ALL ?= $(patsubst  %.c,%,$(SOURCES))

.PHONY: all
all: $(ALL)

.PHONY: tests
tests: $(ALL)
	run-parts --verbose --regex='test__[^.]*$$' .

test__filter__cache_entry_ldap_filter_match: ../src/filter.o
test__utils__lower_utf8: ../src/utils.o
test__utils__same_dn: ../src/utils.o

include ../src/Makefile

CFLAGS += $(DB_CFLAGS) -I../src -fdata-sections -ffunction-sections
LDFLAGS += -Wl,--as-needed -Wl,--gc-sections
LDLIBS += -lldap -llber

.PHONY: clean
clean::
	$(RM) *.o
