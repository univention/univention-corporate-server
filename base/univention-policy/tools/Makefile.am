## Process this file with automake to produce Makefile.in

AUTOMAKE_OPTIONS = foreign

INCLUDES = -I$(top_srcdir)/include

bin_PROGRAMS = univention_policy_result

LDADD = ../lib/libuniventionpolicy.la -luniventiondebug -luniventionconfig -lldap

univention_policy_result_SOURCES = univention_policy_result.c ../lib/internal.h
