ACLOCAL_AMFLAGS=-I m4

sasllibdir = @sasllibdir@
securitylibdir = @pamlibdir@

sasllib_LTLIBRARIES = liboidc.la
liboidc_la_SOURCES = cy2_oidc.c oidc.c plugin_common.c plugin_common.h oidc.h
liboidc_la_CFLAGS = -I/usr/include/sasl
liboidc_la_LDFLAGS = -module -no-undefined -version-info 2:0:2 -export-symbols-regex '^sasl_'

securitylib_LTLIBRARIES = pam_oidc.la
pam_oidc_la_SOURCES = pam_oidc.c oidc.c oidc.h
pam_oidc_la_CFLAGS = -DNO_STATIC_MODULES
pam_oidc_la_LDFLAGS = -module -no-undefined -avoid-version -shared -export-symbols-regex '^_?pam_'

man_MANS = pam_oidc.5 cy2_oidc.5
EXTRA_DIST = $(man_MANS)

