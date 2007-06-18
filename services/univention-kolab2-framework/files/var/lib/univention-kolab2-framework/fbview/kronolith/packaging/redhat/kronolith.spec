#
# $Horde: kronolith/packaging/redhat/kronolith.spec,v 1.8 2004/01/01 15:15:47 jan Exp $
#
# Copyright 2003-2004 Brent J. Nordquist <bjn@horde.org>
#
# See the enclosed file COPYING for license information (GPL). If you
# did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
#
# This is the SPEC file for the Kronolith Red Hat 7.x (RPM v4) RPMs/SRPM.
#

%define apachedir /etc/httpd
%define apacheuser apache
%define apachegroup apache
%define contentdir /var/www

Summary: The Horde calendar application.
Name: kronolith
Version: 1.1
Release: 1
License: GPL
Group: Applications/Horde
Source: ftp://ftp.horde.org/pub/kronolith/kronolith-%{version}.tar.gz
Source1: kronolith.conf
Vendor: The Horde Project
URL: http://www.horde.org/
Packager: Brent J. Nordquist <bjn@horde.org>
BuildArch: noarch
BuildRoot: %{_tmppath}/kronolith-root
Requires: php >= 4.2.1
Requires: apache >= 1.3.22
Requires: horde >= 2.1
Prereq: /usr/bin/perl

%description
Kronolith is the Horde calendar application.  It provides repeating
events, all-day events, custom fields, keywords, and managing multiple
users through Horde Authentication.  The calendar API that Kronolith
uses is abstracted; MCAL and SQL drivers are currently provided.

The Horde Project writes web applications in PHP and releases them under
Open Source licenses.  For more information (including help with Kronolith)
please visit http://www.horde.org/.

%prep
%setup -q -n %{name}-%{version}

%build

%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{apachedir}/conf
cp -p %{SOURCE1} $RPM_BUILD_ROOT%{apachedir}/conf
mkdir -p $RPM_BUILD_ROOT%{contentdir}/html/horde/kronolith
cp -pR * $RPM_BUILD_ROOT%{contentdir}/html/horde/kronolith
cd $RPM_BUILD_ROOT%{contentdir}/html/horde/kronolith/config
for d in *.dist; do
	d0=`basename $d .dist`
	if [ ! -f "$d0" ]; then
		cp -p $d $d0
	fi
done

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT

%pre

%post
perl -pi -e 's/$/ index.php/ if (/DirectoryIndex\s.*index\.html/ && !/index\.php/);' %{apachedir}/conf/httpd.conf
grep -i 'Include.*kronolith.conf$' %{apachedir}/conf/httpd.conf >/dev/null 2>&1
if [ $? -eq 0 ]; then
	perl -pi -e 's/^#+// if (/Include.*kronolith.conf$/i);' %{apachedir}/conf/httpd.conf
else
	echo "Include %{apachedir}/conf/kronolith.conf" >>%{apachedir}/conf/httpd.conf
fi
# post-install instructions:
cat <<_EOF_
You must manually configure Kronolith and create any required database tables!
See "CONFIGURING Kronolith" in %{contentdir}/html/horde/kronolith/docs/INSTALL
You must also restart Apache with "service httpd restart"!
_EOF_

%postun
if [ $1 -eq 0 ]; then
	perl -pi -e 's/^/#/ if (/^Include.*kronolith.conf$/i);' %{apachedir}/conf/httpd.conf
	cat <<_EOF2_
You must restart Apache with "service httpd restart"!
_EOF2_
fi

%files
%defattr(-,root,root)
# Apache kronolith.conf file
%config %{apachedir}/conf/kronolith.conf
# Include top level with %dir so not all files are sucked in
%dir %{contentdir}/html/horde/kronolith
# Include top-level files by hand
%{contentdir}/html/horde/kronolith/*.php
# Include these dirs so that all files _will_ get sucked in
%{contentdir}/html/horde/kronolith/graphics
%{contentdir}/html/horde/kronolith/lib
%{contentdir}/html/horde/kronolith/locale
%{contentdir}/html/horde/kronolith/po
%{contentdir}/html/horde/kronolith/scripts
%{contentdir}/html/horde/kronolith/templates
# Mark documentation files with %doc and %docdir
%doc %{contentdir}/html/horde/kronolith/COPYING
%doc %{contentdir}/html/horde/kronolith/README
%docdir %{contentdir}/html/horde/kronolith/docs
%{contentdir}/html/horde/kronolith/docs
# Mark configuration files with %config and use secure permissions
# (note that .dist files are considered software; don't mark %config)
%attr(750,root,%{apachegroup}) %dir %{contentdir}/html/horde/kronolith/config
%defattr(640,root,%{apachegroup})
%{contentdir}/html/horde/kronolith/config/*.dist
%config %{contentdir}/html/horde/kronolith/config/*.php

%changelog
* Sun Apr 27 2003 Brent J. Nordquist <bjn@horde.org> 1.1-1
- Updated for 1.1

* Mon Jun 24 2002 Brent J. Nordquist <bjn@horde.org>
- 1.0 release 2

* Thu Jun 13 2002 Brent J. Nordquist <bjn@horde.org>
- 1.0 release 1 (private beta)

* Sun Dec 16 2001 Brent J. Nordquist <bjn@horde.org>
- initial RPM for Kronolith 0.0.3

