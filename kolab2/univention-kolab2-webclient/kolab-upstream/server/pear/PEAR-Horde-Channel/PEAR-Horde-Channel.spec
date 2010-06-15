%define pear_xmldir  %{l_prefix}/var/pear

Name:           PEAR-Horde-Channel
Version:        1.0
Release:        20090119
Summary:        Adds pear.horde.org channel to PEAR

Group:          Development/Languages
License:        N/A
URL:            http://pear.horde.org/
Source0:        pear.horde.org.xml

# Build Info
Prefix:		%{l_prefix}
BuildRoot:	%{l_buildroot}

BuildPreReq:    php, php::with_pear = yes
Requires:       php, php::with_pear = yes

Obsoletes:      php-channel-horde

%description
This package adds the pear.horde.org channel which allows PEAR packages
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
  %{l_prefix}/bin/pear -d php_dir=%{l_prefix}/lib/php channel-add    %{pear_xmldir}/pear.horde.org.xml || \
  echo "Channel already exists!" && sleep 1
env PHP_PEAR_PHP_BIN="%{l_prefix}/bin/php -d safe_mode=off"                                               \
  %{l_prefix}/bin/pear -d php_dir=%{l_prefix}/lib/php channel-update %{pear_xmldir}/pear.horde.org.xml || \
  echo "Could not update channel pear.horde.org!" && sleep 1
env PHP_PEAR_PHP_BIN="%{l_prefix}/bin/php -d safe_mode=off"                                               \
  %{l_prefix}/bin/pear -d php_dir=%{l_prefix}/lib/php-h4 channel-add    %{pear_xmldir}/pear.horde.org.xml || \
  echo "Channel already exists!" && sleep 1
env PHP_PEAR_PHP_BIN="%{l_prefix}/bin/php -d safe_mode=off"                                               \
  %{l_prefix}/bin/pear -d php_dir=%{l_prefix}/lib/php-h4 channel-update %{pear_xmldir}/pear.horde.org.xml || \
  echo "Could not update channel pear.horde.org!" && sleep 1
  rm -rf %{l_prefix}/RPM/TMP/pear

%postun
env PHP_PEAR_PHP_BIN="%{l_prefix}/bin/php -d safe_mode=off"                                               \
  %{l_prefix}/bin/pear -d php_dir=%{l_prefix}/lib/php channel-delete pear.horde.org ||                    \
  echo "Could not delete channel pear.horde.org!" && sleep 1
env PHP_PEAR_PHP_BIN="%{l_prefix}/bin/php -d safe_mode=off"                                               \
  %{l_prefix}/bin/pear -d php_dir=%{l_prefix}/lib/php-h4 channel-delete pear.horde.org ||                    \
  echo "Could not delete channel pear.horde.org!" && sleep 1
  rm -rf %{l_prefix}/RPM/TMP/pear

%files -f files

