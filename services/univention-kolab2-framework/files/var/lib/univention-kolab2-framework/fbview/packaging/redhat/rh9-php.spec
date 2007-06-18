#
# $Horde: horde/packaging/redhat/rh9-php.spec,v 1.5 2004/01/01 15:16:43 jan Exp $
#
# Copyright 2003-2004 Brent J. Nordquist <bjn@horde.org>
#
# See the enclosed file COPYING for license information (GPL). If you
# did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
#
# Based on php-4.2.2-17.spec by Red Hat (for 9),
# and added additional modules and options (mbstring, mcrypt)
# and a PEAR suitable for Horde (1.0.1).
#

%define contentdir /var/www
%define manual_langs de en es fr it ja ko pt_BR

# For those wanting to recompile with Oracle libraries
# rpm --rebuild --define 'oracle 1' php4.2.1-x.src.rpm
#
%{!?oracle:%define oracle 0}

# More recent version of PEAR
#
%define pearversion 1.0.1

Summary: The PHP HTML-embedded scripting language. (PHP: Hypertext Preprocessor)
Name: php
Version: 4.2.2
Release: 0horde3
Epoch: 1
License: The PHP License
Group: Development/Languages
Vendor: The Horde Project
URL: http://www.horde.org/
Packager: Brent J. Nordquist <bjn@horde.org>

Source0:  http://www.php.net/distributions/php-%{version}.tar.gz
Source1:  http://www.php.net/distributions/manual/php_manual_de.tar.bz2
Source2:  http://www.php.net/distributions/manual/php_manual_en.tar.bz2
Source3:  http://www.php.net/distributions/manual/php_manual_es.tar.bz2
Source4:  http://www.php.net/distributions/manual/php_manual_fr.tar.bz2
Source5:  http://www.php.net/distributions/manual/php_manual_it.tar.bz2
Source6:  http://www.php.net/distributions/manual/php_manual_ja.tar.bz2
Source7:  http://www.php.net/distributions/manual/php_manual_ko.tar.bz2
Source8:  http://www.php.net/distributions/manual/php_manual_pt_BR.tar.bz2

Source50: php.conf

Source90: ftp://ftp.horde.org/pub/pear/pear-%{pearversion}.tar.gz

# Patch to get around a dumb assumption that size_t is always 4 bytes
Patch0: php-4.2.1-64bit-iconv.patch
Patch1: php-4.2.1-ldap-TSRM.patch
Patch2: php-4.2.1-php.ini-dist.patch
# use -DUCD_COMPATIBLE to make net-snmp backwards-compatible
Patch3: php-4.2.1-snmp.patch
# Fix for #67853
Patch4: php-4.2.2-cookies.patch
Patch5: php-4.2.2-apache2.patch
Patch6: php-4.1.2-missing-vars.patch
Patch9: php-4.2.2-lib64.patch
Patch10: php-4.2.2-inidir.patch
Patch11: php-4.2.2-openssl097.patch
Patch12: php-4.2.2-snmp.patch

# Security fixes
Patch30: php-4.2.2-mailsec.patch
Patch31: php-4.2.2-wrap.patch

# Where are we going to build the install set to?
#
BuildRoot: %{_tmppath}/%{name}-root

BuildRequires: bzip2-devel, curl-devel >= 7.9, db4-devel, expat-devel, freetype-devel
BuildRequires: gd-devel >= 1.8.4, gdbm-devel, gmp-devel, pspell-devel
BuildRequires: httpd-devel >= 2.0.40-6, libjpeg-devel, libpng-devel, pam-devel
BuildRequires: libstdc++-devel, libxml2-devel, ncurses-devel, openssl-devel
BuildRequires: zlib-devel
BuildRequires: bzip2, fileutils, perl
Obsoletes: php-dbg, mod_php, php3, phpfi
# Enforce Apache module ABI compatibility
Requires: httpd-mmn = %(cat %{_includedir}/httpd/.mmn || echo missing-httpd-devel)

%description
PHP is an HTML-embedded scripting language. PHP attempts to make it
easy for developers to write dynamically generated webpages. PHP also
offers built-in database integration for several commercial and
non-commercial database management systems, so writing a
database-enabled webpage with PHP is fairly simple. The most common
use of PHP coding is probably as a replacement for CGI scripts. The
mod_php module enables the Apache Web server to understand and process
the embedded PHP language in Web pages.  This RPM also contains PEAR
%{pearversion} (newer than the version bundled with PHP %{version}).

%package devel
Group: Development/Libraries
Summary: Files needed for building PHP extensions.

%description devel
The php-devel package contains the files needed for building PHP
extensions. If you need to compile your own PHP extensions, you will
need to install this package.

%package imap
Summary: An Apache module for PHP applications that use IMAP.
Group: Development/Languages
Requires: php = %{version}-%{release}
Obsoletes: mod_php3-imap
BuildRequires: krb5-devel, openssl-devel, imap-devel

%description imap
The php-imap package contains a dynamic shared object (DSO) for the
Apache Web server. When compiled into Apache, the php-imap module will
add IMAP (Internet Message Access Protocol) support to PHP. IMAP is a
protocol for retrieving and uploading e-mail messages on mail
servers. PHP is an HTML-embedded scripting language. If you need IMAP
support for PHP applications, you will need to install this package
and the php package.

%package ldap
Summary: A module for PHP applications that use LDAP.
Group: Development/Languages
Requires: php = %{version}-%{release}
Obsoletes: mod_php3-ldap
BuildRequires: cyrus-sasl-devel, openldap-devel, openssl-devel

%description ldap
The php-ldap package is a dynamic shared object (DSO) for the Apache
Web server that adds Lightweight Directory Access Protocol (LDAP)
support to PHP. LDAP is a set of protocols for accessing directory
services over the Internet. PHP is an HTML-embedded scripting
language. If you need LDAP support for PHP applications, you will
need to install this package in addition to the php package.

%package manual
Obsoletes: mod_php3-manual
Group: Documentation
Summary: The PHP manual, in HTML format.
Requires: php = %{version}-%{release}

%description manual
The php-manual package provides comprehensive documentation for the
PHP HTML-embedded scripting language, in HTML format. PHP is an
HTML-embedded scripting language.

%package mcrypt
Summary: A module for PHP applications that use the libmcrypt functions.
Group: Development/Languages
Prereq: php = %{version}-%{release}, perl
BuildRequires: libmcrypt-devel

%description mcrypt
The php-mcrypt package is a dynamic shared object that adds libmcrypt
function support to PHP.

%package mysql
Summary: A module for PHP applications that use MySQL databases.
Group: Development/Languages
Requires: php = %{version}-%{release}
Provides: php_database
Obsoletes: mod_php3-mysql
BuildRequires: mysql-devel

%description mysql
The php-mysql package contains a dynamic shared object that will add
MySQL database support to PHP. MySQL is an object-relational database
management system. PHP is an HTML-embeddable scripting language. If
you need MySQL support for PHP applications, you will need to install
this package and the php or mod_php package.

%package pgsql
Summary: A PostgreSQL database module for PHP.
Group: Development/Languages
Requires: php = %{version}-%{release}
Provides: php_database
Obsoletes: mod_php3-pgsql
BuildRequires: krb5-devel, openssl-devel, postgresql-devel

%description pgsql
The php-pgsql package includes a dynamic shared object (DSO) that can
be compiled in to the Apache Web server to add PostgreSQL database
support to PHP. PostgreSQL is an object-relational database management
system that supports almost all SQL constructs. PHP is an
HTML-embedded scripting language. If you need back-end support for
PostgreSQL, you should install this package in addition to the main
php package.

%package odbc
Group: Development/Languages
Requires: php = %{version}-%{release}
Summary: A module for PHP applications that use ODBC databases.
Provides: php_database
BuildRequires: unixODBC-devel

%description odbc
The php-odbc package contains a dynamic shared object that will add
database support through ODBC to PHP. ODBC is an open specification
which provides a consistent API for developers to use for accessing
data sources (which are often, but not always, databases). PHP is an
HTML-embeddable scripting language. If you need ODBC support for PHP
applications, you will need to install this package and the php
package.

%if %{oracle}
%package oci8
Group: Development/Languages
Requires: php = %{version}-%{release}
Summary: A module for PHP applications that use OCI8 databases.
Provides: php_database

%description oci8
The php-oci8 package contains a dynamic shared object that will add
support for accessing OCI8 databases to PHP.
%endif

%package snmp
Summary: A module for PHP applications that query SNMP-managed devices.
Group: Development/Languages
Requires: php = %{version}-%{release}
BuildRequires: net-snmp-devel

%description snmp
The php-snmp package contains a dynamic shared object that will add
support for querying SNMP devices to PHP.  PHP is an HTML-embeddable
scripting language. If you need SNMP support for PHP applications, you
will need to install this package and the php package.

%prep
%setup -q
%patch0 -p1
%patch1 -p1
%patch2 -p1 -b .conf
%patch3 -p1
%patch4 -p1
%patch5 -p1 -b .ap2
%patch6 -p1
%patch9 -p1 -b .lib64
%patch10 -p1 -b .inidir
%patch11 -p1 -b .ossl097
%patch12 -p1 -b .snmp

# Security fixes
%patch30 -p1 -b .mailsec
%patch31 -p1 -b .wrap

# Prevent %doc confusion over LICENSE & Zend/LICENSE
cp Zend/LICENSE Zend/ZEND_LICENSE

# Source is built twice: once for /usr/bin/php, once for the Apache DSO.
mkdir build-cgi build-apache

# Use correct libdir
perl -pi -e 's|\$\(prefix\)/lib|%{_libdir}|' pear/Makefile.in
perl -pi -e 's|%{_prefix}/lib|%{_libdir}|' php.ini-dist

%build

CFLAGS="$RPM_OPT_FLAGS -fPIC"; export CFLAGS

# Add the Kerberos library path to the default LDFLAGS so that the IMAP checks
# will be able to find the GSSAPI libraries.
LDFLAGS="-L/usr/kerberos/%{_lib}"; export LDFLAGS

# Configure may or may not catch these (mostly second-order) dependencies.
LIBS="-lttf -lfreetype -lpng -ljpeg -lz -lnsl"; export LIBS

# Install extension modules in %{_libdir}/php4.
EXTENSION_DIR=%{_libdir}/php4; export EXTENSION_DIR

# This pulls the static /usr/lib/libc-client.a into the IMAP extension module.
IMAP_SHARED_LIBADD=-lc-client ; export IMAP_SHARED_LIBADD

# pull latest ltmain.sh, AC_PROG_LIBTOOL
libtoolize --force --copy
# force aclocal run during buildconf
touch acinclude.m4

# Regenerate configure scripts (patches change config.m4's)
./buildconf

# Shell function to configure and build a PHP tree.
build() {
ln -sf ../configure
%configure \
	--cache-file=../config.cache \
	--with-config-file-path=%{_sysconfdir} \
	--with-config-file-scan-dir=%{_sysconfdir}/php.d \
	--enable-force-cgi-redirect \
	--disable-debug \
	--enable-pic \
	--disable-rpath \
	--enable-inline-optimization \
	--with-bz2 \
	--with-db3 \
	--with-curl \
	--with-dom=%{_prefix} \
	--with-exec-dir=%{_bindir} \
	--with-freetype-dir=%{_prefix} \
	--with-png-dir=%{_prefix} \
	--with-gd \
	--enable-gd-native-ttf \
	--with-ttf \
	--with-gdbm \
	--with-gettext \
	--with-ncurses \
	--with-gmp \
	--with-iconv \
	--with-jpeg-dir=%{_prefix} \
	--with-openssl \
	--with-png \
	--with-pspell \
	--with-regex=system \
	--with-xml \
	--with-expat-dir=%{_prefix} \
	--with-zlib \
	--with-layout=GNU \
	--enable-bcmath \
	--enable-exif \
	--enable-ftp \
	--enable-mbstring \
	--enable-magic-quotes \
	--enable-safe-mode \
	--enable-sockets \
	--enable-sysvsem \
	--enable-sysvshm \
	--enable-discard-path \
	--enable-track-vars \
	--enable-trans-sid \
	--enable-yp \
	--enable-wddx \
	--without-oci8 \
	--with-pear=%{_datadir}/pear \
	--with-imap=shared \
	--with-imap-ssl \
	--with-kerberos=/usr/kerberos \
	--with-ldap=shared \
	--with-mcrypt=shared \
	--with-mysql=shared,%{_prefix} \
%if %{oracle}
	--with-oci8=shared \
%endif
	--with-pgsql=shared \
	--with-snmp=shared \
	--enable-ucd-snmp-hack \
	--with-unixODBC=shared \
	--enable-memory-limit \
	--enable-bcmath \
	--enable-shmop \
	--enable-versioning \
	--enable-calendar \
	--enable-dbx \
	--enable-dio \
	$*

# Fixup the config_vars to not include the '-a' on lines which call apxs.
# FIXME: redundant with INSTALL_IT setting below?
cat config_vars.mk > config_vars.mk.old
awk '/^INSTALL_IT.*apxs.*-a -n/ {sub("-a -n ","-n ");} {print $0;}' \
	config_vars.mk.old > config_vars.mk

make %{?_smp_mflags}
}

# Build standalone /usr/bin/php
pushd build-cgi
build --enable-force-cgi-redirect
popd

# Build Apache module
pushd build-apache
build --with-apxs2=%{_sbindir}/apxs
popd

%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT

# Install from CGI tree
pushd build-cgi
make install INSTALL_ROOT=$RPM_BUILD_ROOT 
popd

### TODO: only configure shared modules for the one of the two builds
# Install the Apache tree, overwriting the shared modules from before.
# INSTALL_IT=echo prevents "apxs -a -i" from trying to modify httpd.conf
pushd build-apache
make install INSTALL_ROOT=$RPM_BUILD_ROOT INSTALL_IT="echo "
popd

# Install the default configuration file and icons
install -m 755 -d $RPM_BUILD_ROOT%{_sysconfdir}/
install -m 644    php.ini-dist $RPM_BUILD_ROOT%{_sysconfdir}/php.ini
install -m 755 -d $RPM_BUILD_ROOT%{contentdir}/icons
install -m 644    *.gif $RPM_BUILD_ROOT%{contentdir}/icons/

# install the DSO
install -m 755 -d $RPM_BUILD_ROOT%{_libdir}/httpd/modules
install -m 755 build-apache/libs/libphp4.so $RPM_BUILD_ROOT%{_libdir}/httpd/modules

# Apache config fragment
install -m 755 -d $RPM_BUILD_ROOT/etc/httpd/conf.d
install -m 644 $RPM_SOURCE_DIR/php.conf $RPM_BUILD_ROOT/etc/httpd/conf.d

# Manuals -- we'll place English (en) in the location where the only version
# of the manual was before, and langify the rest.
# Hence we don't specify %lang(en) in the files section for the manual rpm
#
for lang in %{manual_langs} ; do
	if test x${lang} = xen ; then
		target_lang=""
	else
		target_lang=${lang}
	fi
	mkdir -p $RPM_BUILD_ROOT%{contentdir}/manual/mod/mod_php4/${target_lang}
	bzip2 -dc $RPM_SOURCE_DIR/php_manual_${lang}.tar.bz2 | tar -x -C $RPM_BUILD_ROOT%{contentdir}/manual/mod/mod_php4/${target_lang} -f -
done

install -m 755 -d $RPM_BUILD_ROOT%{_sysconfdir}/php.d

%if %{oracle}
ocimod=oci8
%endif
# Generate files lists and stub .ini files for each subpackage
for mod in pgsql mysql odbc imap ldap mcrypt snmp ${ocimod}; do
    cat > $RPM_BUILD_ROOT%{_sysconfdir}/php.d/${mod}.ini <<EOF
; Enable ${mod} extension module
extension=${mod}.so
EOF
    cat > files.${mod} <<EOF
%attr(755,root,root) %{_libdir}/php4/${mod}.so
%config(noreplace) %attr(644,root,root) %{_sysconfdir}/php.d/${mod}.ini
EOF
done

# Remove unpackaged files
rm -f $RPM_BUILD_ROOT%{_libdir}/php4/*.a \
      $RPM_BUILD_ROOT%{_bindir}/{phptar,pearize}

# Overlay the PHP-bundled PEAR with a more recent version
#
gzip -dc $RPM_SOURCE_DIR/pear-%{pearversion}.tar.gz | tar -x -C $RPM_BUILD_ROOT%{_datadir} -f -
chmod -R go-w $RPM_BUILD_ROOT%{_datadir}/pear

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT
rm files.*

%files
%defattr(-,root,root)
%doc CODING_STANDARDS CREDITS EXTENSIONS INSTALL LICENSE NEWS README*
%doc Zend/ZEND_*
%config(noreplace) %{_sysconfdir}/php.ini
%{_bindir}/php
%{_bindir}/pear
%{_datadir}/pear
%dir %{_libdir}/php4
%{_libdir}/httpd/modules/libphp4.so
%config(noreplace) %{_sysconfdir}/httpd/conf.d/php.conf
%dir %{_sysconfdir}/php.d

%files devel
%defattr(-,root,root)
%{_bindir}/php-config
%{_bindir}/phpize
%{_bindir}/phpextdist
%{_includedir}/php
%{_libdir}/php

%files manual
%defattr(-,root,root)
%{contentdir}/icons/*
%dir %{contentdir}/manual/mod/mod_php4/
%{contentdir}/manual/mod/mod_php4/*.html
%lang(de) %{contentdir}/manual/mod/mod_php4/de
%lang(es) %{contentdir}/manual/mod/mod_php4/es
%lang(fr) %{contentdir}/manual/mod/mod_php4/fr
%lang(it) %{contentdir}/manual/mod/mod_php4/it
%lang(ja) %{contentdir}/manual/mod/mod_php4/ja
%lang(ko) %{contentdir}/manual/mod/mod_php4/ko
%lang(pt) %{contentdir}/manual/mod/mod_php4/pt_BR

%files pgsql -f files.pgsql

%files mysql -f files.mysql

%files odbc -f files.odbc

%if %{oracle}
%files oci8 -f files.oci8
%endif

%files imap -f files.imap

%files ldap -f files.ldap

%files mcrypt -f files.mcrypt

%files snmp -f files.snmp

%changelog
* Wed Apr 23 2003 Brent J. Nordquist <bjn@horde.org> 4.2.2-0horde3
- make PEAR 1.0.1 overlay (not replace) bundled PHP PEAR (so nothing is lost)
- add mcrypt (shared), enable mbstring
- remove redundant snmp configure line
- remove mcal until we can get it to build/work

* Mon Feb 24 2003 Joe Orton <jorton@redhat.com> 4.2.2-17
- restrict SNMP patch to minimal changes, fixing segv on startup (#84607)

* Wed Feb 12 2003 Joe Orton <jorton@redhat.com> 4.2.2-16
- prevent startup if using httpd.worker to avoid thread-safety issues.
- fix parsing private keys in OpenSSL extension (#83994)
- fixes for SNMP extension (backport from 4.3) (#74761)

* Wed Jan 29 2003 Joe Orton <jorton@redhat.com> 4.2.2-15
- add security fixes for wordwrap() and mail()

* Mon Jan 13 2003 Joe Orton <jorton@redhat.com> 4.2.2-14
- drop explicit Requires in subpackages, rely on automatic deps.
- further fixes for libdir=lib64

* Tue Dec 17 2002 Joe Orton <jorton@redhat.com> 4.2.2-13
- drop prereq for perl, grep in subpackages
- rebuild and patch for OpenSSL 0.9.7

* Tue Dec 10 2002 Joe Orton <jorton@redhat.com> 4.2.2-12
- backport "ini dir scanning" patch from CVS HEAD; /etc/php.d/*.ini
  are now loaded at startup; each subpackage places an ini file
  in that directory rather than munging /etc/php.ini in post/postun.
- default config changes: enable short_open_tag; remove settings for
  php-dbg extension

* Wed Dec  4 2002 Joe Orton <jorton@redhat.com> 4.2.2-11
- own the /usr/lib/php4 directory (#73894)
- reinstate dropped patch to unconditionally disable ZTS

* Mon Dec  2 2002 Joe Orton <jorton@redhat.com> 4.2.2-10
- remove ldconfig invocation in post/postun
- fixes for #73516 (partially), #78586, #75029, #75712, #75878

* Wed Nov  6 2002 Joe Orton <jorton@redhat.com> 4.2.2-9
- fixes for libdir=/usr/lib64, based on SuSE's patches.
- add build prereqs for zlib-devel, imap-devel, curl-devel (#74819)
- remove unpackaged files from install root
- libtoolize; use configure cache to speed up build

* Mon Sep 23 2002 Philip Copeland <bryce@redhat.com> 4.2.2-8.0.6
- PHP cannot determine which UID is being used, so safe
  mode restrictions were always applied. Fixed. (#74396)

* Tue Sep 3 2002 Philip Copeland <bryce@redhat.com> 4.2.2-8.0.4
- zts support seems to crash out httpd on a *second* sighup
  ie service httpd start;
  apachectl restart ; (ok)
  apachectl restart ; (httpd segv's and collapses)
  removed --enable-experimental-zts which this seems related to.
- Small patch added because some places need to know that they
  aren't using the ZTS API's (dumb)

* Mon Sep 2 2002 Philip Copeland <bryce@redhat.com> 4.2.2-8.0.3
- fixup /etc/httpd/conf.d/php.conf to limit largest amount
  of data accepted (#73254) Limited to 512K (which seems a
  little excessive but anyway,..)
  Note: php.conf is part of the srpm sources not part of the
  php codebase.
- ditched extrenious --enable-debugger (was for php-dbg)
- When upgrading we tend not to modify /etc/php.ini if it exists,
  instead we create php.ini.rpmnew. Modified the post scripts to
  edit php.ini.rpmnew if it exists, so that people can copy
  over the php.ini.rpmnew as php.ini knowing that it will
  be an edited version, consistant with what modules they
  installed #72033

* Sun Sep 1 2002 Joe Orton <jorton@redhat.com> 4.2.2-8.0.2
- require httpd-mmn for module ABI compatibility

* Fri Aug 30 2002 Philip Copeland <bryce@redhat.com> 4.2.2-8.0.1
- URLS would drop the last arguments #72752
        --enable-mbstring
        --enable-mbstr-enc-trans
  These were supposed to help provide multibyte language
  support, however, they cause problems. Removed. Maybe in
  a later errata when they work.
- added small patch to php_variables.c that allows
  $_GET[<var>] to initialise properly when
  --enable-mbstr-enc-trans is disabled.
- Be consistant with errata naming (8.0.x)

* Tue Aug 27 2002 Nalin Dahyabhai <nalin@redhat.com> 4.2.2-11
- rebuild

* Wed Aug 22 2002 Philip Copeland <bryce@redhat.com> 4.2.2-10
- Beat down the requirement list to something a little
  more sane

* Wed Aug 14 2002 Bill Nottingham <notting@redhat.com> 4.2.2-9
- trim manual language lists

* Mon Aug 12 2002 Gary Benson <gbenson@redhat.com> 4.2.2-8
- rebuild against httpd-2.0.40

* Sat Aug 10 2002 Elliot Lee <sopwith@redhat.com> 4.2.2-7
- rebuilt with gcc-3.2 (we hope)

* Wed Aug 7 2002 Philip Copeland <bryce@redhat.com> 4.2.2-6
- Where multiple cookies are set, only the last one
  was actually made. Fixes #67853

* Mon Aug 5 2002 Philip Copeland <bryce@redhat.com> 4.2.2-5
- Shuffled the php/php-devel package file manifest
  with respect to PEAR (PHP Extension and Application
  Repository) #70673

* Fri Aug 2 2002 Philip Copeland <bryce@redhat.com> 4.2.2-4
- #67815, search path doesn't include the pear directory
- pear not being installed correctly. Added --with-pear=
  option.

* Tue Jul 23 2002 Tim Powers <timp@redhat.com> 4.2.2-2
- build using gcc-3.2-0.1

* Mon Jul 22 2002 Philip Copeland <bryce@redhat.com> 4.2.2-1
- Yippie 8/ another security vunerability (see
  http://www.php.net/release_4_2_2.php for details)

* Wed Jul 17 2002 Philip Copeland <bryce@redhat.com> 4.2.1-9
- Reminder to self that mm was pushed out because it's
  NOT thread safe.
- Updated the manuals (much to Bills horror)

* Tue Jul 16 2002 Philip Copeland <bryce@redhat.com> 4.2.1-8
- php.ini alteration to fit in with the install/uninstall
  of various php rpm based installable modules

* Mon Jul 15 2002 Philip Copeland <bryce@redhat.com> 4.2.1-8
- php -v showing signs of deep unhappiness with the world
  added  --enable-experimental-zts to configure to make it
  happy again (yes I know experimental sounds 'dangerous'
  it's just a name for an option we need)

* Fri Jul 12 2002 Philip Copeland <bryce@redhat.com> 4.2.1-7
- #68715, Wrong name for Mysql Module in php.ini. Fixed.

* Fri Jun 28 2002 Philip Copeland <bryce@redhat.com> 4.2.1-6
- SNMP fixup

* Thu Jun 27 2002 Philip Copeland <bryce@redhat.com> 4.2.1-5
- Ah,.. seems httpd2 has been renamed to just plain
  ol' httpd. Fixed spec file to suit.
- ucd-snmp changed to net-snmp overnight...
  temporarily disabled snmp while I work out the
  impact of this change and if it is safe

* Wed Jun 26 2002 Philip Copeland <bryce@redhat.com> 4.2.1-4
- openldap 2.1.x problem solved by Nalin. Sure the ldap
  API didn't change,... <mutter>. Added TSRMLS_FETCH()
  to ldap_rebind_proc().
- Removed the php-dbg package as thats going to be provided
  elsewhere

* Fri Jun 21 2002 Tim Powers <timp@redhat.com> 4.2.1-3
- automated rebuild

* Mon Jun 10 2002 Philip Copeland <bryce@redhat.com> 4.2.1-2
- Actually mm is now a dead project. Removed permently.

* Tue May 28 2002 Gary Benson <gbenson@redhat.com> 4.2.1-2
- change paths for httpd-2.0
- add the config file
- disable mm temporarily

* Sun May 26 2002 Tim Powers <timp@redhat.com> 4.2.1-1
- automated rebuild

* Wed May 22 2002 Philip Copeland <bryce@redhat.com> 4.2.1-0
- Initial pristine build of php-4.2.1
- Minor patch to get around a 64 bitism
- Added in the dgb debugging hooks

===============================================================================
  Ditched the 4.1.1 sources for 4.2.1
===============================================================================

* Sun Apr 14 2002 Philip Copeland <bryce@redhat.com> 4.1.2-6
- %post for mysql has zlib in it?!? Bad cut/paste. Fixed.
- Added missing trigger entries to php.ini-dist
- Bumped release number.

* Sat Apr 13 2002 Philip Copeland <bryce@redhat.com> 4.1.2-6
- Oh joyous. buildconf doesn't correctly rebuild a
  configure script, consequently we get lex checking errors
  Strictly speaking this is autoconf's fault. Tweeked.

* Sun Apr 07 2002 Philip Copeland <bryce@redhat.com> 4.1.2-6
- Added in hook for the rather useful dbg addin
  http://dd.cron.ru/dbg/
  May not be able to provide a dbg rpm accomplyment
  to php for the official release but at least it'll
  make it easy to drop in at a later date.

* Mon Mar 25 2002 Philip Copeland <bryce@redhat.com> 4.1.2-5
- Accepted patches from Konstantin Riabitsev <icon@duke.edu>
  for the php.ini file which fix this damnable .dll/.so
  mess.
- Fixes for the modules. Every dll name is now prepended by php_,
  so the modules were NEVER enabled. Also, there is no longer
  php_mysql.dll or php_odbc.dll. Added workarounds for that.
- Jumped a number (-4) because of intresting after effects
  in the build system.

* Tue Mar 12 2002 Philip Copeland <bryce@redhat.com> 4.1.2-3
- Fix for crashing bug (#60855)

* Tue Mar 05 2002 Philip Copeland <bryce@redhat.com> 4.1.2-2
- Forgot the -with-png-dir=%{_prefix} config
  option (#55248)

* Mon Mar 04 2002 Philip Copeland <bryce@redhat.com> 4.1.2-2
- Minor patch for figuring out where the blasted
  mysql.sock named socket lives. (grumble)
- Added in --enable-exif. It's there for people who
  asked for it but I ain't supporting it if it
  breaks.
- Tweak the default php.ini file to turn off file upload by default
  and to tweak the default path for loadable modules

* Thu Feb 28 2002 Philip Copeland <bryce@redhat.com> 4.1.2-1
- Jumped to 4.1.2 for security...

* Wed Feb 13 2002 Philip Copeland <bryce@redhat.com> 4.1.1-4
- Added multibyte input/ouput support
  --enable-mbstring
  --enable-mbstr-enc-trans
- Added in a couple of BuildReq's
- Because db1,2,3 are ditched in the next RHAT release and only
  db4 exists, I've purposly NOT put in the db4-devel BuildReq
  as thers no way to differentiate this build for a 7.X and
  the new release.

* Fri Feb 08 2002 Philip Copeland <bryce@redhat.com> 4.1.1-3
- Added calendar, dbx, dio and mcal support into the build
  --enable-calendar
  --enable-dbx
  --enable-dio
  --enable-mcal

* Thu Feb 07 2002 Philip Copeland <bryce@redhat.com> 4.1.1-2
- Reformatted the spec file to be something more pretty to read
- Some wassak upstream changed the default php.ini file to
  winblows format (.dll) which broke the extension munching
  altered the post scripts to accomodate (#59195)
- Added in --enable-gd-native-ttf (#55199)

* Mon Jan 29 2002 Philip Copeland <bryce@redhat.com> 4.1.1-1
- Added in patch for DOM(xml)

* Mon Jan 28 2002 Philip Copeland <bryce@redhat.com> 4.1.1-0
- Rather than write a new spec file, borrowed the one from 4.0.6-13
  Initial build of 4.1.1 (note db2 is now obsoleted)
  Added --enable-memory-limit

===============================================================================
  Ditched the 4.0.x sources for 4.1.1
===============================================================================

* Wed Dec  5 2001 Philip Copeland <bryce@redhat.com> 4.0.6-13
- Minor tweak to the configure script to allow it to search fo the libxml
  installation in both */include/libxml/tree.h and
  include/libxml2/libxml/tree.h

* Tue Nov 20 2001 Nalin Dahyabhai <nalin@redhat.com> 4.0.6-12
- rebuild for Raw Hide, building snmp again

* Tue Nov 20 2001 Nalin Dahyabhai <nalin@redhat.com> 4.0.6-11
- don't build the snmp module
- don't activate the module for Apache when we install it into the buildroot

* Mon Nov 19 2001 Nalin Dahyabhai <nalin@redhat.com>
- link the IMAP module with c-client.a

* Fri Nov 16 2001 Nalin Dahyabhai <nalin@redhat.com> 4.0.6-10
- use shared expat for XML support, add buildprereq on expat-devel
- update to latest manuals from the web site
- %{_datadir}/php -> %{_datadir}/pear
- miscellaneous cleanups

* Tue Nov 13 2001 Nalin Dahyabhai <nalin@redhat.com>
- remove explicit dependency on krb5-libs

* Fri Nov  9 2001 Nalin Dahyabhai <nalin@redhat.com>
- enable transparent session id support, configure freetype and gmp extensions
  (suggestion and patch Jason Costomiris)

* Mon Sep 17 2001 Tim Powers <timp@redhat.com> 4.0.6-9
- rebuilt against newer posgresql libs

* Wed Sep 12 2001 Tim Powers <timp@redhat.com>
- rebuild with new gcc and binutils

* Mon Aug 27 2001 Nalin Dahyabhai <nalin@redhat.com>
- add patch from pzb at scyld.com to fix the ZVAL_TRUE and ZVAL_FALSE macros
  (#52501)

* Fri Aug 17 2001 Nalin Dahyabhai <nalin@redhat.com>
- enable bzip2 extension
- enable curl extension
- enable use of mm
- clean up use of libtool (#51958)

* Fri Aug 10 2001 Tim Powers <timp@redhat.com>
- only english in php-manuals, space constraints

* Thu Aug  9 2001 Nalin Dahyabhai <nalin@redhat.com>
- include %{_libdir}/%{name}/build instead of %{_libdir}/%{name}4/build (#51141)

* Mon Aug  6 2001 Nalin Dahyabhai <nalin@redhat.com>
- add build deps on pam-devel, pspell-devel, gdbm-devel (#49878)
- add some conditional logic if %%{oracle} is defined (from Antony Nguyen)

* Mon Jul  9 2001 Nalin Dahyabhai <nalin@redhat.com>
- don't obsolete subpackages we ended up not merging

* Mon Jul  2 2001 Nalin Dahyabhai <nalin@redhat.com>
- cleanups
- add manuals in multiple languages (using ko instead of kr for Korean)
- merge all of the manuals into a single -manual subpackage
- use libtool to install binary files which libtool builds
- don't strip any binaries; let the buildroot policies take care of it

* Thu Jun 28 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to 4.0.6 (preliminary)

* Mon Jun 25 2001 Nalin Dahyabhai <nalin@redhat.com>
- enable ttf in the build because the gd support needs it
- add -lfreetype to the LIBS for the same reason

* Wed Jun  6 2001 Nalin Dahyabhai <nalin@redhat.com>
- rebuild in new environment

* Wed May 16 2001 Nalin Dahyabhai <nalin@redhat.com>
- actually use two source trees to build things
- add %%post and %%postun scriptlets to run ldconfig

* Tue May 15 2001 Nalin Dahyabhai <nalin@redhat.com>
- quote part of the AC_ADD_LIBRARY macro to make newer autoconf happy

* Mon May 14 2001 Nalin Dahyabhai <nalin@redhat.com>
- fix error in %%install
- depend on the imap-devel which supplies linkage.c
- modify trigger to disable php versions less than 4.0.0 instead of 3.0.15
- enable DOM support via libxml2 (suggested by Sylvain Bergé)
- build the OpenSSL extension again

* Mon May  7 2001 Nalin Dahyabhai <nalin@redhat.com>
- enable pspell extensions
- update to 4.0.5

* Mon Apr 30 2001 Nalin Dahyabhai <nalin@redhat.com>
- build the ODBC extension

* Mon Apr 30 2001 Bill Nottingham <notting@redhat.com>
- build on ia64

* Fri Mar  2 2001 Nalin Dahyabhai <nalin@redhat.com>
- rebuild in new environment

* Fri Feb 23 2001 Nalin Dahyabhai <nalin@redhat.com>
- obsolete the old phpfi (PHP 2.x) package

* Thu Feb  8 2001 Nalin Dahyabhai <nalin@redhat.com>
- add a commented-out curl extension to the config file (part of #24933)
- fix the PEAR-installation-directory-not-being-eval'ed problem (#24938)
- find the right starting point for multipart form data (#24933)

* Tue Jan 30 2001 Nalin Dahyabhai <nalin@redhat.com>
- aaarrgh, the fix breaks something else, aaarrgh; revert it (#24933)
- terminate variable names at the right place (#24933)

* Sat Jan 20 2001 Nalin Dahyabhai <nalin@redhat.com>
- tweak the fix some more

* Thu Jan 18 2001 Nalin Dahyabhai <nalin@redhat.com>
- extract stas's fix for quoting problems from CVS for testing
- tweak the fix, ask the PHP folks about the tweak
- tweak the fix some more

* Wed Jan 17 2001 Nalin Dahyabhai <nalin@redhat.com>
- merge mod_php into the main php package (#22906)

* Fri Dec 29 2000 Nalin Dahyabhai <nalin@redhat.com>
- try to fix a quoting problem

* Wed Dec 20 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to 4.0.4 to get a raft of bug fixes
- enable sockets
- enable wddx

* Fri Nov  3 2000 Nalin Dahyabhai <nalin@redhat.com>
- rebuild in updated environment

* Thu Nov  2 2000 Nalin Dahyabhai <nalin@redhat.com>
- add more commented-out modules to the default config file (#19276)

* Wed Nov  1 2000 Nalin Dahyabhai <nalin@redhat.com>
- fix not-using-gd problem (#20137)

* Tue Oct 17 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to 4.0.3pl1 to get some bug fixes

* Sat Oct 14 2000 Nalin Dahyabhai <nalin@redhat.com>
- build for errata

* Wed Oct 11 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to 4.0.3 to get security fixes integrated
- patch around problems configuring without Oracle support
- add TSRM to include path when building individual modules

* Fri Sep  8 2000 Nalin Dahyabhai <nalin@redhat.com>
- rebuild in new environment
- enable OpenSSL support

* Wed Sep  6 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to 4.0.2, and move the peardir settings to configure (#17171)
- require %%{version}-%%{release} for subpackages
- add db2-devel and db3-devel prereqs (#17168)

* Wed Aug 23 2000 Nalin Dahyabhai <nalin@redhat.com>
- rebuild in new environment (new imap-devel)

* Wed Aug 16 2000 Nalin Dahyabhai <nalin@redhat.com>
- fix summary and descriptions to match the specspo package

* Wed Aug  9 2000 Nalin Dahyabhai <nalin@redhat.com>
- hard-code the path to apxs in build_ext() (#15799)

* Tue Aug  1 2000 Nalin Dahyabhai <nalin@redhat.com>
- add "." to the include path again, which is the default

* Wed Jul 19 2000 Nalin Dahyabhai <nalin@redhat.com>
- enable PEAR and add it to the include path
- add the beginnings of a -devel subpackage

* Wed Jul 12 2000 Prospector <bugzilla@redhat.com>
- automatic rebuild

* Fri Jul  7 2000 Nalin Dahyabhai <nalin@redhat.com>
- tweaks to post and postun from Bill Peck

* Thu Jul  6 2000 Nalin Dahyabhai <nalin@redhat.com>
- fixes from Nils for building the MySQL client
- change back to requiring %{version} instead of %{version}-%{release}

* Sat Jul  1 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to 4.0.1pl2
- enable MySQL client
- move the php.ini file to %{_sysconfdir}

* Fri Jun 30 2000 Nils Philippsen <nils@redhat.de>
- build_ext defines HAVE_PGSQL so pgsql.so in fact contains symbols
- post/un scripts tweak php.ini correctly now

* Thu Jun 28 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to 4.0.1
- refresh manual

* Tue Jun 26 2000 Nalin Dahyabhai <nalin@redhat.com>
- rebuild against new krb5 package

* Mon Jun 19 2000 Nalin Dahyabhai <nalin@redhat.com>
- rebuild against new db3 package

* Sat Jun 17 2000 Nalin Dahyabhai <nalin@redhat.com>
- Fix syntax error in post and preun scripts.
- Disable IMAP, LDAP, PgSql in the standalone version because it picks up
  the extensions.

* Fri Jun 16 2000 Nalin Dahyabhai <nalin@redhat.com>
- Unexclude the Sparc arch.
- Exclude the ia64 arch until we get a working Postgres build.
- Stop stripping extensions as aggressively.
- Start linking the IMAP module to libpam again.
- Work around extension loading problems.
- Reintroduce file-editing post and preun scripts for the mod_php extensions
  until we come up with a better way to do it.

* Mon Jun  5 2000 Nalin Dahyabhai <nalin@redhat.com>
- ExcludeArch: sparc for now

* Sun Jun  4 2000 Nalin Dahyabhai <nalin@redhat.com>
- add Obsoletes: phpfi, because their content handler names are the same
- add standalone binary, rename module packages to mod_php
- FHS fixes

* Tue May 23 2000 Nalin Dahyabhai <nalin@redhat.com>
- change license from "GPL" to "PHP"
- add URL: tag
- disable mysql support by default (license not specified)

* Mon May 22 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to PHP 4.0.0
- nuke the -mysql subpackage (php comes with a bundled mysql client lib now)

* Tue May 16 2000 Nalin Dahyabhai <nalin@redhat.com>
- link IMAP module against GSS-API and PAM to get dependencies right
- change most of the Requires to Prereqs, because the post edits config files
- move the PHP *Apache* module back to the right directory
- fix broken postun trigger that broke the post
- change most of the postuns to preuns in case php gets removed before subpkgs

* Thu May 11 2000 Trond Eivind Glomsrød <teg@redhat.com>
- rebuilt against new postgres libraries

* Tue May 09 2000 Preston Brown <pbrown@redhat.com>
- php3 .so modules moved to /usr/lib/php3 from /usr/lib/apache (was incorrect)

* Mon Apr 10 2000 Nalin Dahyabhai <nalin@redhat.com>
- make subpackages require php = %{version} (bug #10671)

* Thu Apr 06 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to 3.0.16

* Fri Mar 03 2000 Cristian Gafton <gafton@redhat.com>
- fixed the post script to work when upgrading a package
- add triggere to fix the older packages

* Tue Feb 29 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to 3.0.15
- add build-time dependency for openldap-devel
- enable db,ftp,shm,sem support to fix bug #9648

* Fri Feb 25 2000 Nalin Dahyabhai <nalin@redhat.com>
- add dependency for imap subpackage
- rebuild against Apache 1.3.12

* Thu Feb 24 2000 Preston Brown <pbrown@redhat.com>
- don't include old, outdated manual.  package one from the php distribution.

* Tue Feb 01 2000 Cristian Gafton <gafton@redhat.com>
- rebuild to fix dependency problem

* Fri Jan 14 2000 Preston Brown <pbrown@redhat.com>
- added commented out mysql module, thanks to Jason Duerstock 
  (jason@sdi.cluephone.com). Uncomment to build if you have mysql installed.

* Thu Jan 13 2000 Preston Brown <pbrown@redhat.com>
- rely on imap-devel, don't include imap in src.rpm (#5099).
- xml enabled (#5393)

* Tue Nov 02 1999 Preston Brown <pborwn@redhat.com>
- added post/postun sections to modify httpd.conf (#5259)
- removed old obsolete faq and gif (#5260)
- updated manual.tar.gz package (#5261)

* Thu Oct 07 1999 Matt Wilson <msw@redhat.com>
- rebuilt for sparc glibc brokenness

* Fri Sep 24 1999 Preston Brown <pbrown@redhat.com>
- --with-apxs --> --with-apxs=/usr/sbin/apxs (# 5094)
- ldap support (# 5097)

* Thu Sep 23 1999 Preston Brown <pbrown@redhat.com>
- fix cmdtuples for postgresql, I had it slightly wrong

* Tue Aug 31 1999 Bill Nottingham <notting@redhat.com>
- subpackages must obsolete old stuff...

* Sun Aug 29 1999 Preston Brown <pbrown@redhat.com>
- added -DHAVE_PGCMDTUPLES for postgresql module (bug # 4767)

* Fri Aug 27 1999 Preston Brown <pbrown@redhat.com>
- name change to php to follow real name of package
- fix up references to php3 to refer to php
- upgrade to 3.0.12
- fixed typo in pgsql postun script (bug # 4686)

* Mon Jun 14 1999 Preston Brown <pbrown@redhat.com>
- upgraded to 3.0.9
- fixed postgresql module and made separate package
- separated manual into separate documentation package

* Mon May 24 1999 Preston Brown <pbrown@redhat.com>
- upgraded to 3.0.8, which fixes problems with glibc 2.1.
- took some ideas grom Gomez's RPM.

* Tue May 04 1999 Preston Brown <pbrown@redhat.com>
- hacked in imap support in an ugly way until imap gets an official
  shared library implementation

* Fri Apr 16 1999 Preston Brown <pbrown@redhat.com>
- pick up php3.ini

* Wed Mar 24 1999 Preston Brown <pbrown@redhat.com>
- build against apache 1.3.6

* Sun Mar 21 1999 Cristian Gafton <gafton@redhat.com> 
- auto rebuild in the new build environment (release 2)

* Mon Mar 08 1999 Preston Brown <pbrown@redhat.com>
- upgraded to 3.0.7.

* Wed Feb 24 1999 Preston Brown <pbrown@redhat.com>
- Injected new description and group.

* Sun Feb 07 1999 Preston Brown <pbrown@redhat.com>
- upgrade to php 3.0.6, built against apache 1.3.4

* Mon Oct 12 1998 Cristian Gafton <gafton@redhat.com>
- rebuild for apache 1.3.3

* Thu Oct 08 1998 Preston Brown <pbrown@redhat.com>
- updated to 3.0.5, fixes nasty bugs in 3.0.4.

* Sun Sep 27 1998 Cristian Gafton <gafton@redhat.com>
- updated to 3.0.4 and recompiled for apache 1.3.2

* Thu Sep 03 1998 Preston Brown <pbrown@redhat.com>
- improvements; builds with apache-devel package installed.

* Tue Sep 01 1998 Preston Brown <pbrown@redhat.com>
- Made initial cut for PHP3.
