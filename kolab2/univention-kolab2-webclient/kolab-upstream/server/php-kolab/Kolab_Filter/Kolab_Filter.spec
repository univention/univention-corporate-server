# Variables
%define         V_pear_pkgdir 
%define         V_pear_package Kolab_Filter
%define         V_package Kolab_Filter
%define         V_package_url http://pear.horde.org/index.php?package=
%define         V_package_origin WGET
%define         V_repo_commit 
%define         V_repo_release 
%define         V_version 0.1.8
%define         V_release 20100122
%define         V_sourceurl http://pear.horde.org/get
%define         V_php_lib_loc php
%define         V_www_loc 
%define         V_summary A package for reading/writing Kolab data formats
%define         V_license LGPL

# Package Information
Name:	   %{V_package}
Summary:   %{V_summary}
URL:       {%V_package_url}%{V_pear_package}
Packager:  Gunnar Wrobel <wrobel@pardus.de> (p@rdus)
Version:   %{V_version}
Release:   %{V_release}
License:   %{V_license}
Group:     Development/Libraries
Distribution:	OpenPKG

# List of Sources
Source:    %{V_sourceurl}/%{V_pear_package}-%{V_version}.tgz

# List of patches
Patch0:    package.patch

# Build Info
Prefix:	   %{l_prefix}
BuildRoot: %{l_buildroot}

#Pre requisites
                              
BuildPreReq:  OpenPKG, openpkg >= 20070603 
BuildPreReq:  php, php::with_pear = yes    
BuildPreReq:  PEAR-Horde-Channel           

                                   
PreReq:       OpenPKG, openpkg >= 20070603 
PreReq:       php, php::with_pear = yes    
PreReq:       PEAR-Horde-Channel           
PreReq:       Kolab_Format >= 1.0.1        
PreReq:       Kolab_Server >= 0.5.0        
PreReq:       Kolab_Storage >= 0.4.0       
PreReq:       PEAR-HTTP_Request            
PreReq:       PEAR-Net_LMTP                
PreReq:       PEAR-Net_SMTP                
PreReq:       PEAR-Mail                    
PreReq:       Horde_iCalendar              
PreReq:       Horde_Argv                   
PreReq:       Horde_Notification           
PreReq:       Horde_Prefs                  
                                           
Provides:     php-kolab = 2.2.1            
Obsoletes:    php-kolab < 2.2.1 PEAR-Net_IMAP kolab-filter 


# Package options
%option       with_chroot              no

%description 
 
This package allows to convert Kolab data objects from XML to hashes. 


%prep
	%setup -n %{V_pear_package}-%{V_version}

	cat ../package.xml | sed -e 's/md5sum="[^"]*"//' > package.xml

        if [ -n "`cat %{PATCH0}`" ]; then
	    %patch -p3 -P 0
	fi

%build

%install
        %{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab-filter/log
        %{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab-filter/locks
        %{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab-filter/tmp
        %{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/man/man1

        env PHP_PEAR_PHP_BIN="%{l_prefix}/bin/php -d safe_mode=off -d memory_limit=40M"\
            PHP_PEAR_CACHE_DIR="/tmp/pear/cache"                                       \
	    %{l_prefix}/bin/pear -d www_dir="%{l_prefix}/var/kolab/www/%{V_www_loc}"   \
	                         -d php_dir="%{l_prefix}/lib/%{V_php_lib_loc}"         \
                                 install --offline --force --nodeps -P $RPM_BUILD_ROOT \
                                 package.xml

	rm -rf $RPM_BUILD_ROOT/%{l_prefix}/lib/%{V_php_lib_loc}/{.filemap,.lock,.channels,.depdb,.depdblock}

        # With chroot
        %if "%{with_chroot}" == "yes"
                %{l_shtool} mkdir -f -p -m 755 $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/%{l_prefix}/lib
                cp -a $RPM_BUILD_ROOT/%{l_prefix}/lib/%{V_php_lib_loc} $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/%{l_prefix}/lib/
        %endif

	cp $RPM_BUILD_ROOT/%{l_prefix}/lib/php/doc/Kolab_Filter/man/man1/kolabfilter.1 $RPM_BUILD_ROOT/%{l_prefix}/man/man1
	cd $RPM_BUILD_ROOT/%{l_prefix}/man/man1 && ln -s kolabfilter.1 kolabmailboxfilter.1 && cd -

        %{l_rpmtool} files -v -ofiles -r$RPM_BUILD_ROOT %{l_files_std}                 \
            %dir '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab-filter/tmp    \
            %dir '%defattr(-,%{l_nusr},%{l_ngrp})' %{l_prefix}/var/kolab-filter/log

%clean
	rm -rf $RPM_BUILD_ROOT

%files -f files
