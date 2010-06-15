# Macros
%define         V_package mnemo
%define         V_version 2.2.3
%define         V_release 20100228

# Package Information
Name:		%{V_package}
Summary:	Mnemo is the Horde notes and memos application
URL:		http://www.horde.org/
Packager:	Gunnar Wrobel <wrobel@pardus.de> (p@rdus)
Version:	%{V_version}
Release:	%{V_release}
License:	GPL
Group:		MAIL
Distribution:	OpenPKG

# List of Sources
Source0:	http://ftp.horde.org/pub/%{V_package}/%{V_package}-h3-%{V_version}.tar.gz
Source1:        webclient-mnemo_conf.php.template
Source2:        webclient-mnemo_prefs.php.template
Source3:        10-kolab_conf_base.php
Source4:        conf.php

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
Mnemo is the Horde notes and memos application. It lets users keep
free-text notes and other bits of information which doesnt fit as a
contact, a todo item, an event, etc. It is very similar in
functionality to the Palm Memo application.

%prep
	%setup -q -c %{V_package}-h3-%{V_version}

	cd %{V_package}-h3-%{V_version}
	%patch -p1 -P 0
	cd ..

%build

%install

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/mnemo
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

	cp -r * $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/mnemo

	cd ..

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/mnemo/config/conf.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/mnemo/config/prefs.d

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:1} %{S:2} \
	  $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:3} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/mnemo/config/conf.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:4} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/mnemo/config/

	sed -i -e 's#@@@horde_confdir@@@#%{l_prefix}/var/kolab/www/client/mnemo/config#' $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates/*.php.template

	%{l_rpmtool} files -v -ofiles -r$RPM_BUILD_ROOT %{l_files_std} \
            '%config %{l_prefix}/etc/kolab/templates/webclient-mnemo_conf.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-mnemo_prefs.php.template' \
	    '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/www/client/mnemo/config/conf.php

%clean
	rm -rf $RPM_BUILD_ROOT

%files -f files
