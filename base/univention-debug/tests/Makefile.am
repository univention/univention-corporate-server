## Process this file with automake to produce Makefile.in

AM_CPPFLAGS = -I$(top_srcdir)/include

AM_CFLAGS = -Wall -D_FILE_OFFSET_BITS=64

TESTS_ENVIRONMENT = \
	top_builddir=$(top_builddir) \
	host_cpu=$(host_cpu) \
	PYTHON=$(PYTHON) \
	PYTHON_VERSION=$(PYTHON_VERSION) \
	LC_ALL=C
TESTS = test_c

check_PROGRAMS = test_debug

test_debug_SOURCES = test_debug.c
test_debug_LDADD = $(top_builddir)/lib/libuniventiondebug.la
