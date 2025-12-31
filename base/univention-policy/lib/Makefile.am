#
# Univention Policy
#  Makefile template for the debian package
#
# SPDX-FileCopyrightText: 2003-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

AUTOMAKE_OPTIONS = foreign

INCLUDES = -I$(top_srcdir)/include

lib_LTLIBRARIES = libuniventionpolicy.la

libuniventionpolicy_la_SOURCES = policy.c ldap.c internal.h
libuniventionpolicy_la_LDFLAGS = -luniventiondebug -luniventionconfig @LDAP_LIB@ @LBER_LIB@  -version-info @LIB_CURRENT@:@LIB_REVISION@:@LIB_AGE@
