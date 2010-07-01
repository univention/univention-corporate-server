# Macros
%define         V_package imp
%define         V_version 4.3.6
%define         V_release 20100414

# Package Information
Name:		%{V_package}
Summary:	IMP provides webmail access to IMAP and POP3 accounts.
URL:		http://www.horde.org/
Packager:	Gunnar Wrobel <wrobel@pardus.de> (p@rdus)
Version:	%{V_version}
Release:	%{V_release}
License:	GPL
Group:		MAIL
Distribution:	OpenPKG

# List of Sources
Source0:	http://ftp.horde.org/pub/%{V_package}/%{V_package}-h3-%{V_version}.tar.gz
Source1:        webclient-imp_conf.php.template
Source2:        webclient-imp_header.php.template
Source3:        webclient-imp_hooks.php.template
Source4:        webclient-imp_menu.php.template
Source5:        webclient-imp_mime_drivers.php.template
Source6:        webclient-imp_motd.php.template
Source7:        webclient-imp_prefs.php.template
Source8:        webclient-imp_servers.php.template
Source9:        webclient-imp_spelling.php.template
Source10:       10-kolab_conf_base.php
Source11:       10-kolab_servers_base.php
Source12:       conf.php
Source13:       11-kolab_conf_imp.php

# List of Patches
Patch0:         package.patch

# Build Info
Prefix:		%{l_prefix}
BuildRoot:	%{l_buildroot}

#Pre requisites
BuildPreReq:  OpenPKG, openpkg >= 20070603
BuildPreReq:  php, php::with_pear = yes
PreReq:       horde >= 3.3.6
PreReq:       PEAR-Auth_SASL >= 1.0.2
PreReq:       PEAR-Mail
PreReq:       Horde_IMAP

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

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/imp
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/config/conf.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/webclient_data/storage
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

	cp -r * $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/imp

        sqlite $RPM_BUILD_ROOT%{l_prefix}/var/kolab/webclient_data/storage/imp.db < scripts/sql/imp.sql

	cd ..

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/imp/config/conf.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/imp/config/header.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/imp/config/hooks.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/imp/config/menu.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/imp/config/mime_drivers.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/imp/config/motd.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/imp/config/prefs.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/imp/config/servers.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/imp/config/spelling.d

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:1} %{S:2} %{S:3} %{S:4} %{S:5} %{S:6} %{S:7} %{S:8} %{S:9} \
	  $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:10} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/imp/config/conf.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:11} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/imp/config/servers.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:12} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/imp/config/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:13} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/config/conf.d/

	sed -i -e 's#@@@horde_confdir@@@#%{l_prefix}/var/kolab/www/client/imp/config#' $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates/*.php.template

	%{l_rpmtool} files -v -ofiles -r$RPM_BUILD_ROOT %{l_files_std} \
            '%config %{l_prefix}/etc/kolab/templates/webclient-imp_conf.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-imp_header.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-imp_hooks.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-imp_menu.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-imp_mime_drivers.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-imp_motd.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-imp_prefs.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-imp_servers.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-imp_spelling.php.template' \
            '%config(noreplace) %defattr(-,%{l_nusr},%{l_ngrp}) %{l_prefix}/var/kolab/webclient_data/storage/imp.db' \
            %dir '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/webclient_data/storage \
	    '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/www/client/imp/config/conf.php

%clean
	rm -rf $RPM_BUILD_ROOT

%files -f files

%post
        PATH="%{l_prefix}/bin" %{l_prefix}/bin/php -d safe_mode=0 -f %{l_prefix}/var/kolab/www/client/po/translation.php make --module imp --no-compendium
