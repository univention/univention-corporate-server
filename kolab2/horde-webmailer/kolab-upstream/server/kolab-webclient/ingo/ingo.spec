# Macros
%define         V_package ingo
%define         V_version 1.2.3
%define         V_release 20100122

# Package Information
Name:		%{V_package}
Summary:	Ingo, the Email Filter Rules Manager
URL:		http://www.horde.org/
Packager:	Gunnar Wrobel <wrobel@pardus.de> (p@rdus)
Version:	%{V_version}
Release:	%{V_release}
License:	GPL
Group:		MAIL
Distribution:	OpenPKG

# List of Sources
Source0:	http://ftp.horde.org/pub/%{V_package}/%{V_package}-h3-%{V_version}.tar.gz
Source1:        webclient-ingo_backends.php.template
Source2:        webclient-ingo_conf.php.template
Source3:        webclient-ingo_fields.php.template
Source4:        webclient-ingo_hooks.php.template
Source5:        webclient-ingo_prefs.php.template
Source6:        10-kolab_backends_base.php
Source7:        10-kolab_conf_base.php
Source8:        conf.php

# List of Patches
Patch0:         package.patch

# Build Info
Prefix:		%{l_prefix}
BuildRoot:	%{l_buildroot}

#Pre requisites
BuildPreReq:  OpenPKG, openpkg >= 20070603
BuildPreReq:  php, php::with_pear = yes
PreReq:       horde >= 3.3.6
PreReq:       imp >= 4.3.6
PreReq:       PEAR-Net_Sieve

AutoReq:      no
AutoReqProv:  no

%description 
Ingo, the "Email Filter Rules Manager", started as a frontend for the
Sieve filter language, and is now a generic and complete filter rule
frontend that currently is able to create Sieve, procmail, maildrop,
and IMAP filter rules. The IMAP filter driver translates the filter
rules on demand to IMAP commands, executed via PHP's IMAP extension
and has replaced INGO's internal filtering code. It is now the default
filtering agent in INGO H3 (4.x).

%prep
	%setup -q -c %{V_package}-h3-%{V_version}

	cd %{V_package}-h3-%{V_version}
	%patch -p1 -P 0
	cd ..

%build

%install

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/ingo
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates	

	cd %{V_package}-h3-%{V_version}

	cd config
	for CONFIG in *.dist;                          \
	    do                                         \
	      cp $CONFIG `basename $CONFIG .dist`;     \
	      mkdir -p `basename $CONFIG .php.dist`.d; \
	done
	cd ..

	rm test.php

	#find . -type f | grep '\.orig$' | xargs rm -f

	cp -r * $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/ingo

	cd ..

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/ingo/config/backends.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/ingo/config/conf.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/ingo/config/fields.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/ingo/config/hooks.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/ingo/config/prefs.d

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:1} %{S:2} %{S:3} %{S:4} %{S:5} \
	  $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:6} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/ingo/config/backends.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:7} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/ingo/config/conf.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:8} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/ingo/config/

	sed -i -e 's#@@@horde_confdir@@@#%{l_prefix}/var/kolab/www/client/ingo/config#' $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates/*.php.template

	%{l_rpmtool} files -v -ofiles -r$RPM_BUILD_ROOT %{l_files_std} \
            '%config %{l_prefix}/etc/kolab/templates/webclient-ingo_backends.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-ingo_conf.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-ingo_fields.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-ingo_hooks.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-ingo_prefs.php.template' \
	    '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/www/client/ingo/config/conf.php

%clean
	rm -rf $RPM_BUILD_ROOT

%files -f files
