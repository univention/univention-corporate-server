## Process this file with automake to produce Makefile.in
# SPDX-FileCopyrightText: 2014-2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

AUTOMAKE_OPTIONS = foreign

INCLUDES = -I$(top_srcdir)/include

#TESTS = clib # /usr/sbin/univention-config-registry is not available during compilation !
check_PROGRAMS = clib
check_SCRIPTS = multifile.sh

LDADD = ../lib/libuniventionconfig.la

clib_SOURCES = clib.c

EXTRA_DIST = multifile.sh
