AC_PREREQ([2.63])
AC_INIT([crudeoauth], [1.0.0], [packages@univention.de])
AC_CONFIG_SRCDIR([oauthbearer.c])
AC_CONFIG_MACRO_DIR([m4])
AC_CONFIG_HEADERS([config.h])

AM_INIT_AUTOMAKE([foreign])

# Checks for programs.
AC_PROG_CC
AC_PROG_INSTALL
AC_PROG_LIBTOOL

AC_ARG_WITH(pkg-config, AS_HELP_STRING([--with-pkg-config=PATH], [set pkg-config metadata search path.]),
            PKG_CONFIG_PATH="${withval}", PKG_CONFIG_PATH="")
if test "z$PKG_CONFIG_PATH" != "z"; then
    export PKG_CONFIG_PATH
fi

PKG_CHECK_MODULES([SASL2], [libsasl2 >= 2.1])
# PKG_CHECK_MODULES([RHONABWY], [rhonabwy >= 1.1.2])
CFLAGS="$CFLAGS $SASL2_CFLAGS"
LIBS="$LIBS $GLIB_LIBS $GOBJECT_LIBS $SASL2_LIBS"

AC_ARG_WITH([pam],
			AS_HELP_STRING([--with-pam=DIR], [Base installation of PAM]),
		 [CFLAGS="$CFLAGS -I${with_pam}/include -DWITH_PAM";
		  LDFLAGS="$LDFLAGS -L${with_pam}/lib"])
AC_ARG_WITH([pamlibdir],
			AS_HELP_STRING([--with-pamlibdir=DIR], [directory for PAM modules]),
			[],
			[with_pamlibdir=/lib/security])
AC_ARG_WITH(rhonabwy, [  --with-rhonabwy[=prefix]         Base installation of rhonabwy],
		   [CFLAGS="$CFLAGS -I${with_rhonabwy}/include";
		    LDFLAGS="$LDFLAGS -L${with_rhonabwy}/lib -lrhonabwy"])
AC_ARG_WITH([sasllibdir],
			AS_HELP_STRING([--with-sasllibdir=DIR], [directory for SASL modules]),
			[],
			[with_sasllibdir=${libdir}/sasl2])

# Checks for libraries.
AC_CHECK_LIB([pam], [pam_authenticate])
AC_CHECK_LIB([rhonabwy], [r_jwt_get_full_claims_str])

# Checks for header files.
AC_CHECK_HEADERS([string.h])

# Checks for typedefs, structures, and compiler characteristics.

# Checks for library functions.
AC_FUNC_MALLOC

AC_SUBST([pamlibdir], [$with_pamlibdir])
AC_SUBST([sasllibdir], [$with_sasllibdir])
AC_CONFIG_FILES([Makefile])
AC_OUTPUT
