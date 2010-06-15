# Macros
%define         V_package turba
%define         V_version 2.3.3
%define         V_release 20100228

# Package Information
Name:		%{V_package}
Summary:	Turba Contact Manager
URL:		http://www.horde.org/
Packager:	Gunnar Wrobel <wrobel@pardus.de> (p@rdus)
Version:	%{V_version}
Release:	%{V_release}
License:	GPL
Group:		MAIL
Distribution:	OpenPKG

# List of Sources
Source0:	http://ftp.horde.org/pub/%{V_package}/%{V_package}-h3-%{V_version}.tar.gz
Source1:        webclient-turba_attributes.php.template
Source2:        webclient-turba_conf.php.template
Source3:        webclient-turba_hooks.php.template
Source4:        webclient-turba_menu.php.template
Source5:        webclient-turba_mime_drivers.php.template
Source6:        webclient-turba_prefs.php.template
Source7:        webclient-turba_sources.php.template
Source8:        10-kolab_conf_base.php
Source9:        10-kolab_conf_base.php
Source10:       conf.php

# List of Patches
Patch0:         package.patch

# Build Info
Prefix:		%{l_prefix}
BuildRoot:	%{l_buildroot}

#Pre requisites
BuildPreReq:  OpenPKG, openpkg >= 20070603
BuildPreReq:  php, php::with_pear = yes
PreReq:       horde >= 3.3.6
PreReq:       PEAR-Net_LDAP

AutoReq:      no
AutoReqProv:  no

%description 
Turba is the Horde contact management application. It is a production
level address book, and makes heavy use of the Horde framework to
provide integration with IMP and other Horde applications.

Turba is a complete basic contact management application. SQL, LDAP,
IMSP, Kolab, and Horde Preferences backends are available and are well
tested. You can define the fields in your address books in a very
flexible way, just by changing the config files. You can import/export
from/to Pine, Mulberry, CSV, TSV, and vCard contacts. You can create
distribution lists from your addressbooks, which are handled
transparently by IMP and other Horde applications. You can share
address books with other users. And there are Horde API functions to
add and search for contacts.

%prep
	%setup -q -c %{V_package}-h3-%{V_version}

	cd %{V_package}-h3-%{V_version}
	%patch -p1 -P 0
	cd ..

%build

%install

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/turba
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

	cp -r * $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/turba

	cd ..

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/turba/config/attributes.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/turba/config/conf.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/turba/config/hooks.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/turba/config/menu.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/turba/config/mime_drivers.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/turba/config/prefs.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/turba/config/sources.d

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:1} %{S:2} %{S:3} %{S:4} %{S:5} %{S:6} %{S:7} \
	  $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:8} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/turba/config/conf.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:9} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/turba/config/sources.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:10} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/turba/config/

	sed -i -e 's#@@@horde_confdir@@@#%{l_prefix}/var/kolab/www/client/turba/config#' $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates/*.php.template

	%{l_rpmtool} files -v -ofiles -r$RPM_BUILD_ROOT %{l_files_std} \
            '%config %{l_prefix}/etc/kolab/templates/webclient-turba_attributes.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-turba_conf.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-turba_hooks.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-turba_menu.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-turba_mime_drivers.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-turba_prefs.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-turba_sources.php.template' \
	    '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/www/client/turba/config/conf.php

%clean
	rm -rf $RPM_BUILD_ROOT

%files -f files
