# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

CC      ?= cc
CFLAGS  ?= -O2 -g
CFLAGS  += -fPIC -Wall -Wextra -I.
LDFLAGS += -shared
LIBS    := -lldap -llber -lpthread

TARGET := ucs-ldapdb.so
SOURCE := ldapdb_dlz.c

$(TARGET): $(SOURCE) dlz_minimal.h
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(SOURCE) $(LIBS)

clean:
	rm -f $(TARGET)

.PHONY: clean
