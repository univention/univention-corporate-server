## Process this file with automake to produce Makefile.in

AUTOMAKE_OPTIONS = foreign

INCLUDES = -I$(top_srcdir)/include

bin_PROGRAMS = univentionLicenseCreateSignature univentionLicenseGenerate
sbin_SCRIPTS = make_license.sh

univentionLicenseCreateSignature_SOURCES = signLicense.c
univentionLicenseCreateSignature_LDADD = ../lib/libuniventionlicense.la

univentionLicenseGenerate_SOURCES = genkey.c
univentionLicenseGenerate_LDADD = ../lib/libuniventionlicense.la
