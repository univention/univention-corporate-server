#
#  File: rh9-turba.spec
#  $Horde: turba/packaging/redhat/rh9-turba.spec,v 1.1 2003/04/29 00:28:48 bjn Exp $
#
#  This is the SPEC file for the Turba Red Hat 9 RPMs/SRPM.
#

%define apachedir /etc/httpd
%define apacheuser apache
%define apachegroup apache
%define contentdir /var/www

Summary: The Horde contact management application.
Name: turba
Version: 1.2
Release: 1
Copyright: GPL
Group: Applications/Horde
Source: ftp://ftp.horde.org/pub/turba/turba-%{version}.tar.gz
Source1: turba.conf
Vendor: The Horde Project
URL: http://www.horde.org/
Packager: Brent J. Nordquist <bjn@horde.org>
BuildArchitectures: noarch
BuildRoot: /tmp/turba-root
Requires: php >= 4.2.1
Requires: httpd >= 2.0.40
Requires: horde >= 2.0
Prereq: /usr/bin/perl

%description
Turba is the Horde contact management application, which allows access
to and storage of personal contacts (including name, email address,
phone number, and other easily customizable fields).  Turba integrates
with IMP (Horde's webmail application) as its address book.

The Horde Project writes web applications in PHP and releases them under
Open Source licenses.  For more information (including help with Turba)
please visit http://www.horde.org/.

%prep
%setup -q -n %{name}-%{version}

%build

%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{apachedir}/conf.d
cp -p $RPM_SOURCE_DIR/turba.conf $RPM_BUILD_ROOT%{apachedir}/conf.d
mkdir -p $RPM_BUILD_ROOT%{contentdir}/html/horde/turba
cp -pR * $RPM_BUILD_ROOT%{contentdir}/html/horde/turba
cd $RPM_BUILD_ROOT%{contentdir}/html/horde/turba/config
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
# post-install instructions:
cat <<_EOF_
You must manually configure Turba and create any required database tables!
See "CONFIGURING TURBA" in %{contentdir}/html/horde/turba/docs/INSTALL
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
# Apache turba.conf file
%config %{apachedir}/conf.d/turba.conf
# Include top level with %dir so not all files are sucked in
%dir %{contentdir}/html/horde/turba
# Include top-level files by hand
%{contentdir}/html/horde/turba/*.php
# Include these dirs so that all files _will_ get sucked in
%{contentdir}/html/horde/turba/graphics
%{contentdir}/html/horde/turba/lib
%{contentdir}/html/horde/turba/locale
%{contentdir}/html/horde/turba/po
%{contentdir}/html/horde/turba/scripts
%{contentdir}/html/horde/turba/templates
# Mark documentation files with %doc and %docdir
%doc %{contentdir}/html/horde/turba/COPYING
%doc %{contentdir}/html/horde/turba/README
%docdir %{contentdir}/html/horde/turba/docs
%{contentdir}/html/horde/turba/docs
# Mark configuration files with %config and use secure permissions
# (note that .dist files are considered software; don't mark %config)
%attr(750,root,%{apachegroup}) %dir %{contentdir}/html/horde/turba/config
%defattr(640,root,%{apachegroup})
%{contentdir}/html/horde/turba/config/.htaccess
%{contentdir}/html/horde/turba/config/*.dist
%config %{contentdir}/html/horde/turba/config/*.php

%changelog
* Mon Apr 28 2003 Brent J. Nordquist <bjn@horde.org> 1.2-1
- First release, 1.2-1

