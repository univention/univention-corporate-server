#
# Univention Directory Listener
#  Makefile for the listener
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
CC ?= gcc

DB_LDLIBS := -llmdb
DB_OBJS := cache.o cache_dn.o cache_entry.o cache_lowlevel.o base64.o filter.o

LDAP_LDLIBS := -lldap -llber

CFLAGS += -Wall -Werror -D_FILE_OFFSET_BITS=64
LDLIBS := -luniventiondebug -luniventionconfig -licuuc
LISTENER_LDLIBS := -luniventionpolicy $(LDAP_LDLIBS) -lpython3.11 $(DB_LDLIBS)
LISTENER_OBJS := main.o notifier.o transfile.o handlers.o change.o network.o signals.o select_server.o utils.o $(DB_OBJS)
DUMP_LDLIBS := $(LDAP_LDLIBS) $(DB_LDLIBS)
DUMP_OBJS := dump.o dump_signals.o utils.o $(DB_OBJS)
DEMO_OBJS := demo.o network.o utils.o
VERIFY_LDLIBS := $(LDAP_LDLIBS) $(DB_LDLIBS)
VERIFY_OBJS := verify.o dump_signals.o utils.o $(DB_OBJS)

ALL ?= listener dump verify
.PHONY: all
all: $(ALL)

listener: $(LISTENER_OBJS)
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS) $(LISTENER_LDLIBS)

dump: $(DUMP_OBJS)
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS) $(DUMP_LDLIBS)

demo: $(DEMO_OBJS)
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS) $(DEMO_LDLIBS)

verify: $(VERIFY_OBJS)
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS) $(VERIFY_LDLIBS)

.PHONY: clean
clean::
	$(RM) *.o
	$(RM) $(ALL)
