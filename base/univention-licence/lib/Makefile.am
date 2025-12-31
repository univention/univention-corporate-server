# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

## Process this file with automake to produce Makefile.in

AUTOMAKE_OPTIONS = foreign

INCLUDES = -I$(top_srcdir)/include

lib_LTLIBRARIES = libuniventionlicense.la

libuniventionlicense_la_SOURCES = license.h license.c license_ldap.c license_key.c license_signature.c
libuniventionlicense_la_LDFLAGS = -luniventionpolicy -luniventionconfig -luniventiondebug $(LDAP_LIB) $(CRYPTO_LIB) -version-info @LIB_CURRENT@:@LIB_REVISION@:@LIB_AGE@
