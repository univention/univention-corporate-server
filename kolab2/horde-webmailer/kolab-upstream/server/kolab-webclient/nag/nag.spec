# Macros
%define         V_package nag
%define         V_version 2.3.4
%define         V_release 20100228

# Package Information
Name:		%{V_package}
Summary:	Nag Tasklist Application
URL:		http://www.horde.org/
Packager:	Gunnar Wrobel <wrobel@pardus.de> (p@rdus)
Version:	%{V_version}
Release:	%{V_release}
License:	GPL
Group:		MAIL
Distribution:	OpenPKG

# List of Sources
Source0:	http://ftp.horde.org/pub/%{V_package}/%{V_package}-h3-%{V_version}.tar.gz
Source1:        webclient-nag_conf.php.template
Source2:        webclient-nag_menu.php.template
Source3:        webclient-nag_prefs.php.template
Source4:        10-kolab_conf_base.php
Source5:        conf.php

# List of Patches
Patch0:         package.patch

# Build Info
Prefix:		%{l_prefix}
BuildRoot:	%{l_buildroot}

#Pre requisites
BuildPreReq:  OpenPKG, openpkg >= 20070603
BuildPreReq:  php, php::with_pear = yes
PreReq:       horde >= 3.3.6

AutoReq:      no
AutoReqProv:  no

%description 
Nag is the Horde task list application. It stores todo items, things
due later this week, etc. It is very similar in functionality to the
Palm ToDo application.

%prep
	%setup -q -c %{V_package}-h3-%{V_version}

	cd %{V_package}-h3-%{V_version}
	%patch -p1 -P 0
	cd ..

%build

%install

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/nag
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

	cp -r * $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/nag

	cd ..

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/nag/config/conf.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/nag/config/menu.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/nag/config/prefs.d

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:1} %{S:2} %{S:3} \
	  $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:4} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/nag/config/conf.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:5} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/nag/config/

	sed -i -e 's#@@@horde_confdir@@@#%{l_prefix}/var/kolab/www/client/nag/config#' $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates/*.php.template

	%{l_rpmtool} files -v -ofiles -r$RPM_BUILD_ROOT %{l_files_std} \
            '%config %{l_prefix}/etc/kolab/templates/webclient-nag_conf.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-nag_menu.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-nag_prefs.php.template' \
	    '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/www/client/nag/config/conf.php

%clean
	rm -rf $RPM_BUILD_ROOT

%files -f files
