ACLOCAL_AMFLAGS=-I m4

sasllibdir = @sasllibdir@
securitylibdir = @pamlibdir@

sasllib_LTLIBRARIES = liboauthbearer.la
liboauthbearer_la_SOURCES = sasl_oauthbearer.c oauthbearer.c plugin_common.c plugin_common.h oauthbearer.h
liboauthbearer_la_CFLAGS = -I/usr/include/sasl
liboauthbearer_la_LDFLAGS = -module -no-undefined -version-info 2:0:2 -export-symbols-regex '^sasl_'

securitylib_LTLIBRARIES = pam_oauthbearer.la
pam_oauthbearer_la_SOURCES = pam_oauthbearer.c oauthbearer.c oauthbearer.h
pam_oauthbearer_la_CFLAGS = -DNO_STATIC_MODULES
pam_oauthbearer_la_LDFLAGS = -module -no-undefined -avoid-version -shared -export-symbols-regex '^_?pam_'

man_MANS = pam_oauthbearer.5 sasl_oauthbearer.5
EXTRA_DIST = $(man_MANS)

