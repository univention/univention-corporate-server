#
# $Horde: horde/packaging/redhat/rh9-horde.spec,v 1.4 2004/01/01 15:16:43 jan Exp $
#
# Copyright 2003-2004 Brent J. Nordquist <bjn@horde.org>
#
# See the enclosed file COPYING for license information (GPL). If you
# did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
#
# This is the SPEC file for the Horde Red Hat 9 RPMs/SRPM.
#

%define apachedir /etc/httpd
%define apacheuser apache
%define apachegroup apache
%define contentdir /var/www
%define phpini /etc/php.ini

Summary: The common Horde Framework for all Horde modules.
Name: horde
Version: 2.2.3
Release: 1
License: LGPL
Group: Applications/Horde
Source: ftp://ftp.horde.org/pub/horde/horde-%{version}.tar.gz
Source1: horde.conf
Vendor: The Horde Project
URL: http://www.horde.org/
Packager: Brent J. Nordquist <bjn@horde.org>
BuildArch: noarch
BuildRoot: %{_tmppath}/horde-root
Requires: php >= 4.2.1
Requires: httpd >= 2.0.40
Prereq: /usr/bin/perl

%description
The Horde Framework provides a common structure and interface for Horde
applications (such as IMP, a web-based mail program).  This RPM is
required for all other Horde module RPMs.

The Horde Project writes web applications in PHP and releases them under
Open Source licenses.  For more information (including help with Horde
and its modules) please visit http://www.horde.org/.

%prep
%setup -q -n %{name}-%{version}

%build

%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{apachedir}/conf.d
cp -p %{SOURCE1} $RPM_BUILD_ROOT%{apachedir}/conf.d
mkdir -p $RPM_BUILD_ROOT%{contentdir}/html/horde
cp -pR * $RPM_BUILD_ROOT%{contentdir}/html/horde
chmod go-rwx $RPM_BUILD_ROOT%{contentdir}/html/horde/test.php
cd $RPM_BUILD_ROOT%{contentdir}/html/horde/config
for d in *.dist; do
	d0=`basename $d .dist`
	if [ ! -f "$d0" ]; then
		cp -p $d $d0
	fi
done

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT

%post
perl -pi -e 's/=\s*Off/= On/i if (/file_uploads\s*=\s*Off/i);' %{phpini}
# post-install instructions:
cat <<_EOF_
You must manually configure Horde and create any required database tables!
See "CONFIGURING HORDE" in %{contentdir}/html/horde/docs/INSTALL
You must also restart Apache with "service httpd restart"!
_EOF_

%postun
if [ $1 -eq 0 ]; then
	cat <<_EOF2_
You must restart Apache with "service httpd restart"!
_EOF2_
fi

%files
%defattr(-,root,root)
# Apache horde.conf file
%config %{apachedir}/conf.d/horde.conf
# Include top level with %dir so not all files are sucked in
%dir %{contentdir}/html/horde
# Include top-level files by hand
%{contentdir}/html/horde/*.php
# Include these dirs so that all files _will_ get sucked in
%{contentdir}/html/horde/graphics
%{contentdir}/html/horde/lib
%{contentdir}/html/horde/locale
%{contentdir}/html/horde/po
%{contentdir}/html/horde/scripts
%{contentdir}/html/horde/templates
%{contentdir}/html/horde/util
# Mark documentation files with %doc and %docdir
%doc %{contentdir}/html/horde/COPYING
%doc %{contentdir}/html/horde/README
%docdir %{contentdir}/html/horde/docs
%{contentdir}/html/horde/docs
# Mark configuration files with %config and use secure permissions
# (note that .dist files are considered software; don't mark %config)
%attr(750,root,%{apachegroup}) %dir %{contentdir}/html/horde/config
%defattr(640,root,%{apachegroup})
%{contentdir}/html/horde/config/.htaccess
%{contentdir}/html/horde/config/*.dist
%config %{contentdir}/html/horde/config/*.php

%changelog
* Mon Apr 28 2003 Brent J. Nordquist <bjn@horde.org> 2.2.3-1
- First release, 2.2.3-1

