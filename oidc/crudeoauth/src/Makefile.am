ACLOCAL_AMFLAGS=-I m4

sasllibdir = @sasllibdir@
securitylibdir = @pamlibdir@

sasllib_LTLIBRARIES = liboauth.la
liboauth_la_SOURCES = cy2_oauth.c oauth.c plugin_common.c plugin_common.h oauth.h
liboauth_la_CFLAGS = -I/usr/include/sasl
liboauth_la_LDFLAGS = -module -no-undefined -version-info 2:0:2 -export-symbols-regex '^sasl_'

securitylib_LTLIBRARIES = pam_oauth.la
pam_oauth_la_SOURCES = pam_oauth.c oauth.c oauth.h
pam_oauth_la_CFLAGS = -DNO_STATIC_MODULES
pam_oauth_la_LDFLAGS = -module -no-undefined -avoid-version -shared -export-symbols-regex '^_?pam_'

man_MANS = pam_oauth.5 cy2_oauth.5
EXTRA_DIST = $(man_MANS)

