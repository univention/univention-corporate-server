#
# $Horde: horde/packaging/redhat/horde.spec,v 1.13 2004/01/01 15:16:43 jan Exp $
#
# Copyright 2003-2004 Brent J. Nordquist <bjn@horde.org>
#
# See the enclosed file COPYING for license information (GPL). If you
# did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
#
# This is the SPEC file for the Horde Red Hat 7.x (RPM v4) RPMs/SRPM.
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
Requires: apache >= 1.3.22
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
mkdir -p $RPM_BUILD_ROOT%{apachedir}/conf
cp -p %{SOURCE1} $RPM_BUILD_ROOT%{apachedir}/conf
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
perl -pi -e 's/$/ index.php/ if (/DirectoryIndex\s.*index\.html/ && !/index\.php/);' %{apachedir}/conf/httpd.conf
grep -i 'Include.*horde.conf$' %{apachedir}/conf/httpd.conf >/dev/null 2>&1
if [ $? -eq 0 ]; then
	perl -pi -e 's/^#+// if (/Include.*horde.conf$/i);' %{apachedir}/conf/httpd.conf
else
	echo "Include %{apachedir}/conf/horde.conf" >>%{apachedir}/conf/httpd.conf
fi
# post-install instructions:
cat <<_EOF_
You must manually configure Horde and create any required database tables!
See "CONFIGURING HORDE" in %{contentdir}/html/horde/docs/INSTALL
You must also restart Apache with "service httpd restart"!
_EOF_

%postun
if [ $1 -eq 0 ]; then
	perl -pi -e 's/^/#/ if (/^Include.*horde.conf$/i);' %{apachedir}/conf/httpd.conf
	cat <<_EOF2_
You must restart Apache with "service httpd restart"!
_EOF2_
fi

%files
%defattr(-,root,root)
# Apache horde.conf file
%config %{apachedir}/conf/horde.conf
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
* Sun Apr 27 2003 Brent J. Nordquist <bjn@horde.org> 2.2.3-1
- Updated for 2.2.3

* Tue Jun 25 2002 Brent J. Nordquist <bjn@horde.org>
- 2.1 release 3

* Mon Jun 24 2002 Brent J. Nordquist <bjn@horde.org>
- 2.1 release 2 (private beta)

* Thu Jun 13 2002 Brent J. Nordquist <bjn@horde.org>
- 2.1 release 1 (private beta)

* Wed Jan 02 2002 Brent J. Nordquist <bjn@horde.org>
- 2.0 release 1

* Mon Dec 24 2001 Brent J. Nordquist <bjn@horde.org>
- 2.0-RC4 release 1

* Sat Dec 15 2001 Brent J. Nordquist <bjn@horde.org>
- rewritten for Horde 2.0

* Wed Nov 14 2001 Brent J. Nordquist <bjn@horde.org>
- 1.2.7 release 1rh7

* Sat Jul 21 2001 Brent J. Nordquist <bjn@horde.org>
- 1.2.6 release 1rh7

* Tue Feb 06 2001 Brent J. Nordquist <bjn@horde.org>
- 1.2.4 release 1rh7

