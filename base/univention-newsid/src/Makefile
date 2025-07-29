#!/usr/bin/make -f
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

PROG := univention-newsid
OBJS := memory.o util_pw.o md4.o genrand.o newsid.o

BINDIR := $(DESTDIR)/usr/sbin
INSTALL ?= install

$(PROG):	$(OBJS)
	$(CC) $(CFLAGS) $(OBJS) -o $(PROG) $(LDFLAGS)

install:
	$(INSTALL) -m 0755 -d $(BINDIR)
	$(INSTALL) -m 0755 $(PROG) $(BINDIR)/$(PROG)

clean:
	$(RM) $(OBJS) $(PROG) *~
