#
# Univention Directory Notifier
#  Makefile
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
CFLAGS += -Wall -pedantic
LDADD := -luniventiondebug -luniventionconfig
NOTIFIER_LDADD = $(LDADD) -lldap
DUMP_LDADD = $(LDADD)


all: univention-directory-notifier

univention-directory-notifier: index.o cache.o callback.o network.o notify.o univention-directory-notifier.o
	$(CC) $(CFLAGS) -o $@ $^ $(NOTIFIER_LDADD)

univention-directory-notifier-index-dump: index.o index-dump.o
	$(CC) $(CFLAGS) -o $@ $^ $(DUMP_LDADD)

clean:
	$(RM) *.o core univention-directory-notifier univention-directory-notifier-index-dump
