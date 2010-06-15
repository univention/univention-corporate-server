# Macros
%define         V_package horde
%define         V_version 3.3.6
%define         V_release 20100121

# Package Information
Name:		%{V_package}
Summary:	The Horde base application.
URL:		http://www.horde.org/
Packager:	Gunnar Wrobel <wrobel@pardus.de> (p@rdus)
Version:	%{V_version}
Release:	%{V_release}
License:	GPL
Group:		MAIL
Distribution:	OpenPKG

# List of Sources
Source0:	http://ftp.horde.org/pub/%{V_package}/%{V_package}-%{V_version}.tar.gz
Source1:        webclient-kolab-conf.template
Source2:        webclient-config_hooks.php.template
Source3:        webclient-config_mime_drivers.php.template
Source4:        webclient-config_motd.php.template
Source5:        webclient-config_nls.php.template
Source6:        webclient-config_prefs.php.template
Source7:        webclient-config_registry.php.template
Source8:        10-kolab_hooks_base.php
Source9:        10-kolab_prefs_base.php
Source10:       10-kolab_conf_base.php
Source11:       conf.php

# List of Patches
Patch0:         package.patch

# Build Info
Prefix:		%{l_prefix}
BuildRoot:	%{l_buildroot}

#Pre requisites
BuildPreReq:  OpenPKG, openpkg >= 20070603
BuildPreReq:  php, php::with_pear = yes
PreReq:       kolabd
PreReq:       Horde_Alarm
PreReq:       Horde_Block
PreReq:       Horde_Compress
PreReq:       Horde_Crypt
PreReq:       Horde_Data
PreReq:       Horde_Editor
PreReq:       Horde_Feed
PreReq:       Horde_File_PDF
PreReq:       Horde_Form
PreReq:       Horde_Http_Client
PreReq:       Horde_Image
PreReq:       Horde_Loader
PreReq:       Horde_Kolab
PreReq:       Horde_Maintenance
PreReq:       Horde_Mobile
PreReq:       Horde_Net_SMS
PreReq:       Horde_RPC
PreReq:       Horde_SessionHandler
PreReq:       Horde_Share
PreReq:       Horde_SyncML
PreReq:       Horde_Template
PreReq:       Horde_Text_Filter
PreReq:       Horde_Text_Flowed
PreReq:       Horde_Tree
PreReq:       Horde_UI
PreReq:       Kolab_Format >= 1.0.1
PreReq:       Kolab_Server >= 0.5.0
PreReq:       Kolab_Storage >= 0.4.0
# Needed by horde
PreReq:       PEAR-DB
# Needed by horde (translation.php)
PreReq:       PEAR-Console_Table
PreReq:       PEAR-File_Find

AutoReq:      no
AutoReqProv:  no

%description 
The Horde Application Framework is a general-purpose web application
framework in PHP, providing classes for dealing with preferences,
compression, browser detection, connection tracking, MIME handling,
and more.

This specific package does however remove all components of the actual
Horde framework and solely installs the base Horde application that
needs to be installed as a basis for the other Horde applications. The
Horde framework is installed using PEAR based packages.


%prep
	%setup -q -c %{V_package}-%{V_version}

	cd %{V_package}-%{V_version}
	%patch -p1 -P 0
	cd ..

%build

%install

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/webclient_data/storage
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/webclient_data/log
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/webclient_data/tmp
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/webclient_data/sessions
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates	

	cd %{V_package}-%{V_version}

	cd config
	for CONFIG in *.dist;                          \
	    do                                         \
	      cp $CONFIG `basename $CONFIG .dist`;     \
	      mkdir -p `basename $CONFIG .php.dist`.d; \
	done
	cd ..

	rm test.php

	#find . -type f | grep '\.orig$' | xargs rm -f

	cp -r * $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/

	# The following section removes libraries again so that we
	# only need to patch/install them once in the system.
	#
	# kolab/issue3293 (Big code duplication and code version messup: Horde
        #                  libs in 2.2.1)
	rm -rf $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/lib/File
	rm -rf $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/lib/Horde*
	rm -rf $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/lib/Net
	rm -rf $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/lib/SyncML*
	rm -rf $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/lib/Text
	rm -rf $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/lib/VFS*
	rm -rf $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/lib/XML

	# Remove the Google search portal block. It requires applying for a search API key
	# and is not really explained. It will confuse users as does nothing without
	# admin intervention.
	rm -rf $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/lib/Block/google.php

	# Remove the weather data portal block. It is not really documented and I don't
	# think the effort is worth it. In its current state it is simply confusing.
	rm -rf $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/lib/Block/metar.php

        sqlite $RPM_BUILD_ROOT%{l_prefix}/var/kolab/webclient_data/storage/horde.db < scripts/sql/horde_alarms.sql
        sqlite $RPM_BUILD_ROOT%{l_prefix}/var/kolab/webclient_data/storage/horde.db < scripts/sql/horde_perms.sql
        sqlite $RPM_BUILD_ROOT%{l_prefix}/var/kolab/webclient_data/storage/horde.db < scripts/sql/horde_syncml.sql

	cd ..

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/config/conf.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/config/hooks.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/config/mime.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/config/motd.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/config/nls.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/config/prefs.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/config/registry.d

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:1} %{S:2} %{S:3} %{S:4} %{S:5} %{S:6} %{S:7} \
	  $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:8} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/config/hooks.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:9} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/config/prefs.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:10} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/config/conf.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:11} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/config/

	sed -i -e 's#@@@horde_confdir@@@#%{l_prefix}/var/kolab/www/client/config#' $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates/*.php.template

	%{l_rpmtool} files -v -ofiles -r$RPM_BUILD_ROOT %{l_files_std} \
	    '%config %{l_prefix}/etc/kolab/templates/webclient-kolab-conf.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-config_hooks.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-config_mime_drivers.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-config_motd.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-config_nls.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-config_prefs.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-config_registry.php.template' \
            '%config(noreplace) %{l_prefix}/var/kolab/webclient_data/storage/horde.db' \
            %dir '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/webclient_data/log \
            %dir '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/webclient_data/storage \
            %dir '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/webclient_data/storage/horde.db \
            %dir '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/webclient_data/tmp \
            %dir '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/webclient_data/sessions \
	    '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/www/client/config/conf.php

%clean
	rm -rf $RPM_BUILD_ROOT

%files -f files
