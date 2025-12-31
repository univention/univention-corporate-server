# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

## Process this file with automake to produce Makefile.in

AUTOMAKE_OPTIONS = foreign

INCLUDES = -I$(top_srcdir)/include

bin_PROGRAMS = univentionLicenseTest
sbin_SCRIPTS = univention-license-import

univentionLicenseTest_SOURCES = test.c
univentionLicenseTest_LDADD = ../lib/libuniventionlicense.la
