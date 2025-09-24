# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

## Process this file with automake to produce Makefile.in

AM_CPPFLAGS = -I$(top_srcdir)/include

AM_CFLAGS = -Wall -D_FILE_OFFSET_BITS=64 -Werror

lib_LTLIBRARIES = libuniventiondebug.la

libuniventiondebug_la_SOURCES = debug.h debug.c
libuniventiondebug_la_LDFLAGS = -version-info @LIB_CURRENT@:@LIB_REVISION@:@LIB_AGE@
