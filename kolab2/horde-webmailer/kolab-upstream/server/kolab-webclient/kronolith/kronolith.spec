# Macros
%define         V_package kronolith
%define         V_version 2.3.3
%define         V_release 20100228

# Package Information
Name:		%{V_package}
Summary:	Kronolith Calendar Application
URL:		http://www.horde.org/
Packager:	Gunnar Wrobel <wrobel@pardus.de> (p@rdus)
Version:	%{V_version}
Release:	%{V_release}
License:	GPL
Group:		MAIL
Distribution:	OpenPKG

# List of Sources
Source0:	http://ftp.horde.org/pub/%{V_package}/%{V_package}-h3-%{V_version}.tar.gz
Source1:        webclient-kronolith-kolab-conf.template
Source2:        webclient-kronolith_keywords.php.template
Source3:        webclient-kronolith_menu.php.template
Source4:        webclient-kronolith_prefs.php.template
Source5:        10-kolab_conf_base.php
Source6:        conf.php

# List of Patches
Patch0:         package.patch

# Build Info
Prefix:		%{l_prefix}
BuildRoot:	%{l_buildroot}

#Pre requisites
BuildPreReq:  OpenPKG, openpkg >= 20070603
BuildPreReq:  php, php::with_pear = yes
PreReq:       horde >= 3.3.6
PreReq:       PEAR-Date_Holidays_Austria >= 0.1.3
PreReq:       PEAR-Date_Holidays_Brazil >= 0.1.2
PreReq:       PEAR-Date_Holidays_Denmark >= 0.1.3
PreReq:       PEAR-Date_Holidays_Discordian >= 0.1.1
PreReq:       PEAR-Date_Holidays_EnglandWales >= 0.1.2
PreReq:       PEAR-Date_Holidays_Germany >= 0.1.2
PreReq:       PEAR-Date_Holidays_Iceland >= 0.1.2
PreReq:       PEAR-Date_Holidays_Ireland >= 0.1.2
PreReq:       PEAR-Date_Holidays_Italy >= 0.1.1
PreReq:       PEAR-Date_Holidays_Japan >= 0.1.1
PreReq:       PEAR-Date_Holidays_Netherlands >= 0.1.2
PreReq:       PEAR-Date_Holidays_Norway >= 0.1.2
PreReq:       PEAR-Date_Holidays_Romania >= 0.1.2
PreReq:       PEAR-Date_Holidays_Slovenia >= 0.1.2
PreReq:       PEAR-Date_Holidays_Sweden >= 0.1.2
PreReq:       PEAR-Date_Holidays_Ukraine >= 0.1.2
PreReq:       PEAR-Date_Holidays_UNO >= 0.1.3
PreReq:       PEAR-Date_Holidays_USA >= 0.1.1

AutoReq:      no
AutoReqProv:  no

%description 
Kronolith is the Horde calendar application. It provides a stable and
featureful individual calendar system for every Horde user, with
integrated collaboration/scheduling features. It makes extensive use
of the Horde Framework to provide integration with other applications.

%prep
	%setup -q -c %{V_package}-h3-%{V_version}

	cd %{V_package}-h3-%{V_version}
	%patch -p1 -P 0
	cd ..

%build

%install

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/kronolith
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

	find . -type f | grep '\.orig$' | xargs rm -f

	cp -r * $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/kronolith

	cd ..

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/kronolith/config/conf.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/kronolith/config/keywords.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/kronolith/config/menu.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/kronolith/config/prefs.d

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:1} %{S:2} %{S:3} %{S:4} \
	  $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:5} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/kronolith/config/conf.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:6} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/kronolith/config/

	sed -i -e 's#@@@horde_confdir@@@#%{l_prefix}/var/kolab/www/client/kronolith/config#' $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates/*.php.template

	%{l_rpmtool} files -v -ofiles -r$RPM_BUILD_ROOT %{l_files_std} \
            '%config %{l_prefix}/etc/kolab/templates/webclient-kronolith-kolab-conf.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-kronolith_keywords.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-kronolith_menu.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-kronolith_prefs.php.template' \
	    '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/www/client/kronolith/config/conf.php

%clean
	rm -rf $RPM_BUILD_ROOT

%files -f files

%post
        PATH="%{l_prefix}/bin" %{l_prefix}/bin/php -d safe_mode=0 -f %{l_prefix}/var/kolab/www/client/po/translation.php make --module kronolith --no-compendium
