# Package Information
Name:		kolab-webclient
Summary:	The Kolab Groupware web client (based on horde)
URL:		http://www.kolab.org/
Packager:	Gunnar Wrobel <wrobel@pardus.de> (p@rdus)
Version:	1.2.6
Release:	20100122
License:	GPL
Group:		MAIL
Distribution:	OpenPKG

# List of Sources

# List of Patches

# Build Info
Prefix:		%{l_prefix}
BuildRoot:	%{l_buildroot}

#Pre requisites
BuildPreReq:  OpenPKG, openpkg >= 20070603
BuildPreReq:  php, php::with_pear = yes
PreReq:       dimp >= 1.1.4
PreReq:       mimp >= 1.1.3
PreReq:       passwd >= 3.1.2
PreReq:       kronolith >= 2.3.3
PreReq:       ingo >= 1.2.3
PreReq:       mnemo >= 2.2.3
PreReq:       nag >= 2.3.4
PreReq:       turba >= 2.3.3

Obsoletes:    horde-kolab, horde-kronolith-kolab, horde-imp-kolab, horde-ingo-kolab, horde-kolab-client, horde-dimp-kolab, horde-mimp-kolab, horde-mnemo-kolab, horde-nag-kolab, horde-passwd-kolab, horde-turba-kolab

AutoReq:      no
AutoReqProv:  no
#BuildArch:    noarch

%description 
The Kolab Groupware web client provides a Kolab compatible web
frontend to the Kolab server. The package is based on Horde.

%build

%install
        %{l_shtool} install -d $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client
	# Add a marker file so that this package installs something
	touch $RPM_BUILD_ROOT%{l_prefix}/var/kolab/www/client/.kolab-webclient

        %{l_rpmtool} files -v -ofiles -r$RPM_BUILD_ROOT %{l_files_std}

%clean
	rm -rf $RPM_BUILD_ROOT

%files -f files
