# $Id: configure.ac,v 1.18 2017/08/13 14:32:42 manu Exp $ 

AC_PREREQ([2.63])
AC_INIT([crudeoidc], [1.9], [manu@netbsd.org])
AC_CONFIG_SRCDIR([oidc.c])
AC_CONFIG_MACRO_DIR([m4])
AC_CONFIG_HEADERS([config.h])

AM_INIT_AUTOMAKE([foreign])

# Checks for programs.
AC_PROG_CC
AC_PROG_INSTALL
AC_PROG_LIBTOOL

AC_ARG_WITH(pkg-config, [  --with-pkg-config=PATH set pkg-config metadata search path.],
            PKG_CONFIG_PATH="${withval}", PKG_CONFIG_PATH="")
if test "z$PKG_CONFIG_PATH" != "z"; then
    export PKG_CONFIG_PATH
fi

PKG_CHECK_MODULES(CRUDEOIDC, glib-2.0 >= 2.4.0 gobject-2.0 >= 2.4.0 
		  libxml-2.0 xmlsec1 >= 1.2.6 xmlsec1-openssl >= 1.2.6)
CFLAGS="$CFLAGS $CRUDEOIDC_CFLAGS"
LIBS="$LIBS $CRUDEOIDC_LIBS"

AC_ARG_WITH(sasl2, [  --with-sasl2=prefix           Base installation of Cyrus SASL],
		   [CFLAGS="$CFLAGS -I${with_sasl2}/include -I${with_sasl2}/include/sasl -DWITH_SASL2"; 
		    LDFLAGS="$LDFLAGS -L${with_sasl2}/lib";
		    cyrus_sasl2_prefix="${with_sasl2}"])
AC_ARG_WITH(pam, [  --with-pam=prefix             Base installation of PAM],
		 [CFLAGS="$CFLAGS -I${with_pam}/include -DWITH_PAM"; 
		  LDFLAGS="$LDFLAGS -L${with_pam}/lib";
		  pam_prefix="${with_pam}"])
AC_ARG_WITH(lasso, [  --with-lasso[=prefix]         Base installation of Lasso],
		   [CFLAGS="$CFLAGS -I${with_lasso}/include"; 
		    LDFLAGS="$LDFLAGS -L${with_lasso}/lib -llasso"])
AC_ARG_WITH(rhonabwy, [  --with-rhonabwy[=prefix]         Base installation of rhonabwy],
		   [CFLAGS="$CFLAGS -I${with_rhonabwy}/include"; 
		    LDFLAGS="$LDFLAGS -L${with_rhonabwy}/lib -lrhonabwy"])

# Checks for libraries.
AC_CHECK_LIB([lasso], [lasso_node_new_from_xmlNode])
AC_CHECK_LIB([xml2], [xmlParseDoc])
AC_CHECK_LIB([xmlsec1], [xmlSecInit])
AC_CHECK_LIB([pam], [pam_authenticate])
AC_CHECK_LIB([sasl], [sasl_client_init])
AC_CHECK_LIB([crypto], [BIO_f_base64])
AC_CHECK_LIB([rhonabwy], [r_jwt_get_full_claims_str])

# Checks for header files.
AC_CHECK_HEADERS([string.h])

# Checks for typedefs, structures, and compiler characteristics.

# Checks for library functions.
AC_FUNC_MALLOC

AC_SUBST([cyrus_sasl2_prefix])
AC_SUBST([pam_prefix])
AC_CONFIG_FILES([Makefile])
AC_OUTPUT
