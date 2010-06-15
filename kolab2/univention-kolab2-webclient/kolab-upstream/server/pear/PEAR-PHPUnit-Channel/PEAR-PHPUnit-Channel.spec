%define pear_xmldir  %{l_prefix}/var/pear

Name:           PEAR-PHPUnit-Channel
Version:        1.0
Release:        20090119
Summary:        Adds pear.phpunit.de channel to PEAR

Group:          Development/Languages
License:        N/A
URL:            http://pear.phpunit.de/
Source0:        pear.phpunit.de.xml

# Build Info
Prefix:		%{l_prefix}
BuildRoot:	%{l_buildroot}

BuildPreReq:    php, php::with_pear = yes
Requires:       php, php::with_pear = yes

%description
This package adds the pear.phpunit.de channel which allows PEAR packages
from this channel to be installed.


%prep
%setup -q -c -T

%build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{pear_xmldir}
install -m 644 %{SOURCE0} $RPM_BUILD_ROOT%{pear_xmldir}
%{l_rpmtool} files -v -ofiles -r$RPM_BUILD_ROOT %{l_files_std} 

%clean
rm -rf $RPM_BUILD_ROOT

%post

env PHP_PEAR_PHP_BIN="%{l_prefix}/bin/php -d safe_mode=off"                                               \
  %{l_prefix}/bin/pear -d php_dir=%{l_prefix}/lib/php channel-add    %{pear_xmldir}/pear.phpunit.de.xml || \
  echo "Channel already exists!" && sleep 1
env PHP_PEAR_PHP_BIN="%{l_prefix}/bin/php -d safe_mode=off"                                               \
  %{l_prefix}/bin/pear -d php_dir=%{l_prefix}/lib/php channel-update %{pear_xmldir}/pear.phpunit.de.xml || \
  echo "Could not update channel pear.phpunit.de!" && sleep 1
  rm -rf %{l_prefix}/RPM/TMP/pear

%postun
env PHP_PEAR_PHP_BIN="%{l_prefix}/bin/php -d safe_mode=off"                                               \
  %{l_prefix}/bin/pear -d php_dir=%{l_prefix}/lib/php channel-delete pear.phpunit.de ||                    \
  echo "Could not delete channel pear.phpunit.de!" && sleep 1
  rm -rf %{l_prefix}/RPM/TMP/pear

%files -f files

