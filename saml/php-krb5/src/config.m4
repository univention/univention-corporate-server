PHP_ARG_WITH(krb5, for kerberos support,
 [  --with-krb5             Include generic kerberos5/GSSAPI support]
 )

PHP_ARG_WITH(krb5config, path to krb5config tool,
 [  --with-krb5config       Path to krb5config tool],
 no, no
 )

PHP_ARG_WITH(krb5kadm, for kerberos KADM5 support,
 [  --with-krb5kadm[=S]      Include KADM5 Kerberos Administration Support - MIT only],
 no, no
 )

if test "$PHP_KRB5" != "no" -o "$PHP_KRB5KADM" != "no"; then


	if test "$PHP_KRB5CONFIG" == "no"; then
		PHP_KRB5CONFIG=`which krb5-config`
	fi

	AC_MSG_CHECKING([whether we have krb5config])

	if test -x $PHP_KRB5CONFIG; then
		AC_MSG_RESULT($PHP_KRB5CONFIG)
	else
		AC_MSG_ERROR([no])
		exit
	fi



	if test "$PHP_KRB5KADM" != "no"; then
		KRB5_LDFLAGS=`$PHP_KRB5CONFIG --libs krb5 gssapi kadm-client`
		KRB5_CFLAGS=`$PHP_KRB5CONFIG --cflags krb5 gssapi kadm-client`
	else
		KRB5_LDFLAGS=`$PHP_KRB5CONFIG --libs krb5 gssapi`
		KRB5_CFLAGS=`$PHP_KRB5CONFIG --cflags krb5 gssapi`
	fi

	AC_MSG_CHECKING([for required linker flags])
	AC_MSG_RESULT($KRB5_LDFLAGS)

	AC_MSG_CHECKING([for required compiler flags])
	AC_MSG_RESULT($KRB5_CFLAGS)

	KRB5_VERSION=`$PHP_KRB5CONFIG --version`

	AC_MSG_CHECKING([for kerberos library version])
	AC_MSG_RESULT($KRB5_VERSION)
	AC_DEFINE_UNQUOTED(KRB5_VERSION, ["$KRB5_VERSION"], [Kerberos library version])

	SOURCE_FILES="krb5.c negotiate_auth.c gssapi.c"

	if test "$PHP_KRB5KADM" != "no"; then
		SOURCE_FILES="${SOURCE_FILES} kadm.c kadm5_principal.c kadm5_policy.c kadm5_tldata.c"
		AC_DEFINE(HAVE_KADM5, [], [Enable KADM5 support])
	fi

	CFLAGS="-Wall ${CFLAGS} ${KRB5_CFLAGS}"
	LDFLAGS="${LDFLAGS} ${KRB5_LDFLAGS}"

	AC_CHECK_FUNCS(krb5_free_string)
	AC_CHECK_FUNCS(krb5_chpw_message)
	AC_CHECK_FUNCS(krb5_principal_get_realm)

	PHP_SUBST(CFLAGS)
	PHP_SUBST(LDFLAGS)
	PHP_NEW_EXTENSION(krb5, $SOURCE_FILES, $ext_shared)
	PHP_INSTALL_HEADERS([ext/krb5], [php_krb5.h])
fi
