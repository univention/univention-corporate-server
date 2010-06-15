# Macros
%define         V_package mimp
%define         V_version 1.1.3
%define         V_release 20100122

# Package Information
Name:		%{V_package}
Summary:	MIMP is a project to create a version of IMP suitable for mobile devices such as WAP phones or PDAs. 
URL:		http://www.horde.org/
Packager:	Gunnar Wrobel <wrobel@pardus.de> (p@rdus)
Version:	%{V_version}
Release:	%{V_release}
License:	GPL
Group:		MAIL
Distribution:	OpenPKG

# List of Sources
Source0:	http://ftp.horde.org/pub/%{V_package}/%{V_package}-h3-%{V_version}.tar.gz
Source1:        webclient-mimp_conf.php.template
Source2:        webclient-mimp_menu.php.template
Source3:        webclient-mimp_mime_drivers.php.template
Source4:        webclient-mimp_prefs.php.template
Source5:        conf.php

# List of Patches
Patch0:         package.patch

# Build Info
Prefix:		%{l_prefix}
BuildRoot:	%{l_buildroot}

#Pre requisites
BuildPreReq:  OpenPKG, openpkg >= 20070603
BuildPreReq:  php, php::with_pear = yes
PreReq:       imp >= 4.3.6

AutoReq:      no
AutoReqProv:  no

%description 
IMP is the Internet Messaging Program. It is written in PHP and
provides webmail access to IMAP and POP3 accounts.

%prep
	%setup -q -c %{V_package}-h3-%{V_version}

	cd %{V_package}-h3-%{V_version}
	%patch -p1 -P 0
	cd ..

%build

%install

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/mimp
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates	

	cd %{V_package}-h3-%{V_version}

	cd config
	for CONFIG in *.dist;                          \
	    do                                         \
	      cp $CONFIG `basename $CONFIG .dist`;     \
	      mkdir -p `basename $CONFIG .php.dist`.d; \
	done
	cd ..

	#find . -type f | grep '\.orig$' | xargs rm -f

	cp -r * $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/mimp

	cd ..

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/mimp/config/conf.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/mimp/config/menu.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/mimp/config/mime_drivers.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/mimp/config/prefs.d

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:1} %{S:2} %{S:3} %{S:4} \
	  $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:5} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/mimp/config/

	sed -i -e 's#@@@horde_confdir@@@#%{l_prefix}/var/kolab/www/client/mimp/config#' $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates/*.php.template

	%{l_rpmtool} files -v -ofiles -r$RPM_BUILD_ROOT %{l_files_std} \
            '%config %{l_prefix}/etc/kolab/templates/webclient-mimp_conf.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-mimp_menu.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-mimp_mime_drivers.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-mimp_prefs.php.template' \
	    '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/www/client/mimp/config/conf.php

%clean
	rm -rf $RPM_BUILD_ROOT

%files -f files
