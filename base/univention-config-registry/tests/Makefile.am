## Process this file with automake to produce Makefile.in

AUTOMAKE_OPTIONS = foreign

INCLUDES = -I$(top_srcdir)/include

#TESTS = clib # /usr/sbin/univention-config-registry is not available during compilation !
check_PROGRAMS = clib
check_SCRIPTS = multifile.sh

LDADD = ../lib/libuniventionconfig.la

clib_SOURCES = clib.c

EXTRA_DIST = multifile.sh
