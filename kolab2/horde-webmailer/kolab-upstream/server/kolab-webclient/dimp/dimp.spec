# Macros
%define         V_package dimp
%define         V_version 1.1.4
%define         V_release 20100122

# Package Information
Name:		%{V_package}
Summary:	DIMP is a project to create a version of IMP utilizing AJAX-like technologies to allow a more dynamic user experience (thus DIMP... Dynamic IMP).
URL:		http://www.horde.org/
Packager:	Gunnar Wrobel <wrobel@pardus.de> (p@rdus)
Version:	%{V_version}
Release:	%{V_release}
License:	GPL
Group:		MAIL
Distribution:	OpenPKG

# List of Sources
Source0:	http://ftp.horde.org/pub/%{V_package}/%{V_package}-h3-%{V_version}.tar.gz
Source1:        webclient-dimp_conf.php.template
Source2:        webclient-dimp_hooks.php.template
Source3:        webclient-dimp_menu.php.template
Source4:        webclient-dimp_portal.php.template
Source5:        webclient-dimp_prefs.php.template
Source6:        webclient-dimp_servers.php.template
Source7:        10-kolab_menu_base.php
Source8:        10-kolab_servers_base.php
Source9:        conf.php

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

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/dimp
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

	cp -r * $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/dimp

	cd ..

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/dimp/config/conf.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/dimp/config/hooks.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/dimp/config/menu.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/dimp/config/portal.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/dimp/config/prefs.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/dimp/config/servers.d

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:1} %{S:2} %{S:3} %{S:4} %{S:5} %{S:6} \
	  $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:7} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/dimp/config/menu.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:8} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/dimp/config/servers.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:9} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/dimp/config/

	sed -i -e 's#@@@horde_confdir@@@#%{l_prefix}/var/kolab/www/client/dimp/config#' $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates/*.php.template

	%{l_rpmtool} files -v -ofiles -r$RPM_BUILD_ROOT %{l_files_std} \
            '%config %{l_prefix}/etc/kolab/templates/webclient-dimp_conf.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-dimp_hooks.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-dimp_menu.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-dimp_portal.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-dimp_prefs.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-dimp_servers.php.template' \
	    '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/www/client/dimp/config/conf.php

%clean
	rm -rf $RPM_BUILD_ROOT

%files -f files

%post
        PATH="%{l_prefix}/bin" %{l_prefix}/bin/php -d safe_mode=0 -f %{l_prefix}/var/kolab/www/client/po/translation.php make --module dimp --no-compendium
