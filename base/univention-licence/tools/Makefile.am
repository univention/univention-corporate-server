## Process this file with automake to produce Makefile.in

AUTOMAKE_OPTIONS = foreign

INCLUDES = -I$(top_srcdir)/include

bin_PROGRAMS = univentionLicenseTest 

univentionLicenseTest_SOURCES = test.c
univentionLicenseTest_LDFLAGS = -luniventionlicense -L../lib/ -lldap -luniventionconfig
