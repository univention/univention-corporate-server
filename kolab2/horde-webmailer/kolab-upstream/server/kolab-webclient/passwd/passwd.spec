# Macros
%define         V_package passwd
%define         V_version 3.1.2
%define         V_release 20100209

# Package Information
Name:		%{V_package}
Summary:	Passwd is the Horde password changing application.
URL:		http://www.horde.org/
Packager:	Gunnar Wrobel <wrobel@pardus.de> (p@rdus)
Version:	%{V_version}
Release:	%{V_release}
License:	GPL
Group:		MAIL
Distribution:	OpenPKG

# List of Sources
Source0:	http://ftp.horde.org/pub/%{V_package}/%{V_package}-h3-%{V_version}.tar.gz
Source1:        webclient-passwd_conf.php.template
Source2:        webclient-passwd_backends.php.template
Source3:        10-kolab_backends_base.php
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
Passwd is the Horde password changing application.  Right now, Passwd
provides fairly complete support for changing passwords via Poppassd,
LDAP, Unix expect scripts, the Unix smbpasswd command for SMB/CIFS
passwords, Kolab, ADSI, Pine, Serv-U FTP, VMailMgr, vpopmail, and SQL
passwords.

%prep
	%setup -q -c %{V_package}-h3-%{V_version}

	cd %{V_package}-h3-%{V_version}
	%patch -p1 -P 0
	cd ..

%build

%install

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/passwd
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

	cp -r * $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/passwd

	cd ..

	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/passwd/config/conf.d
	%{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/passwd/config/backends.d

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:1} %{S:2} \
	  $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates

	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:3} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/passwd/config/backends.d/
	%{l_shtool} install -c -m 644 %{l_value -s -a} %{S:4} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/passwd/config/

	sed -i -e 's#@@@horde_confdir@@@#%{l_prefix}/var/kolab/www/client/passwd/config#' $RPM_BUILD_ROOT%{l_prefix}/etc/kolab/templates/*.php.template

	%{l_rpmtool} files -v -ofiles -r$RPM_BUILD_ROOT %{l_files_std} \
            '%config %{l_prefix}/etc/kolab/templates/webclient-passwd_conf.php.template' \
            '%config %{l_prefix}/etc/kolab/templates/webclient-passwd_backends.php.template' \
	    '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab/www/client/passwd/config/conf.php

%clean
	rm -rf $RPM_BUILD_ROOT

%files -f files
