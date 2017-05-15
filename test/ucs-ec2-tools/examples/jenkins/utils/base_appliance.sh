#!/bin/bash
#
# Copyright 2015-2017 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

appliance_default_password="zRMtAmGIb3"

check_returnvalue ()
{
	rval=$1
	errormessage=$2
	if [ "${rval}" != 0 ]; then
		echo "${errormessage}"
		exit "${rval}"
	fi
}

install_vmware_packages ()
{
	univention-install -y --force-yes open-vm-tools
}

install_virtualbox_packages ()
{
	ucr set repository/online/unmaintained=yes
	univention-install -y --force-yes virtualbox-guest-x11
	ucr set repository/online/unmaintained=no
}

install_activation_packages ()
{
	univention-install -y --force-yes univention-system-activation
	ucr set --force auth/sshd/user/root=yes
}

download_packages ()
{
	mkdir -p /var/cache/univention-system-setup/packages/
	if [ ! -e /etc/apt/sources.list.d/05univention-system-setup.list ]; then
		echo "deb [trusted=yes] file:/var/cache/univention-system-setup/packages/ ./" >>/etc/apt/sources.list.d/05univention-system-setup.list
	fi

	cd /var/cache/univention-system-setup/packages/
	install_cmd="$(univention-config-registry get update/commands/install)"

	for package in "$1"; do
		LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 ${package} | 
		apt-get download -o Dir::Cache::Archives=/var/cache/univention-system-setup/packages $(LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 ${package} | sed -ne 's|^Inst \([^ ]*\) .*|\1|p')

		check_returnvalue $? "Failed to download required packages for ${package}"
		apt-ftparchive packages . >Packages
		check_returnvalue $? "Failed to create ftparchive directory"
		apt-get update
	done

	return 0
}

app_get_ini ()
{
	local app=$1
	python -c "from univention.appcenter.app_cache import Apps
app = Apps().find('$app')
print app.get_ini_file()"
}

get_app_attr_raw_line ()
{
	local app=$1
	local attr=$2
	local ini="$(app_get_ini $app)"
	grep -i "^$attr " "$ini" # assumption: ini contains $attr + <space> before the '='
}

get_app_attr_raw ()
{
	local app=$1
	local attr=$2
	local line="$(get_app_attr_raw_line $app $attr)"
	echo "$line" | sed -e "s/^.*= //"
}

get_app_attr ()
{
	local app=$1
	local attr=$2
	local value="$(get_app_attr_raw $app $attr)"
	echo "$value" | sed -e 's/, */ /g'
}

app_get_database_packages_for_docker_host ()
{
	local app=$1
	python -c "from univention.appcenter.app_cache import Apps; \
		from univention.appcenter.database import DatabaseConnector; \
		app=Apps().find('$app'); \
		d = DatabaseConnector.get_connector(app); \
		print ' '.join(d._get_software_packages())"
}

app_get_component ()
{
	local app=$1
	python -c "from univention.appcenter.app_cache import Apps; \
				app = Apps().find('$app'); \
				print app.component_id"
}

app_appliance_is_software_blacklisted ()
{
	local app="$1"
	[ -z "$app" ] && return 1
	local value="$(get_app_attr $app AppliancePagesBlackList)"
	echo "$value" | grep -qs software
	return $?
}

appliance_dump_memory ()
{
	local app="$1"
	local targetfile="$2"
	local value="$(get_app_attr $app ApplianceMemory)"
	[ -z $value ] && value="1024"
	echo "$value" > "$targetfile"
}

app_appliance_AllowPreconfiguredSetup ()
{
	local app="$1"
	local value="$(get_app_attr $app ApplianceAllowPreconfiguredSetup)"
	. /usr/share/univention-lib/ucr.sh 
	case "$(echo -n "$value" | tr '[:upper:]' '[:lower:]')" in
		1|yes|on|true|enable|enabled) return 0 ;;
		0|no|off|false|disable|disabled) return 1 ;;
		*) return 2 ;;
	esac
}

app_appliance_IsDockerApp ()
{
	local app="$1"
	[ -z "$app" ] && return 1
	python -c "
import sys
from univention.appcenter.app_cache import Apps; \
app = Apps().find('$app')
dockerimage = app.get_docker_image_name()
if dockerimage:
	sys.exit(0)
else:
	sys.exit(1)
"
}

prepare_docker_app_container ()
{
	local app="$1"
	# TODO: build functionality for non appbox docker apps
	if app_appliance_IsDockerApp "$app"; then
		php7_required=false
		if [ "$app" == "owncloud82" ]; then
			php7_required=true
		fi

		dockerimage="$(get_app_attr $app DockerImage)"
		if [ "$?" != 0 ]; then
			echo "Error: No docker image for docker app!"
			exit 1
		fi

		# generate .dockercfg as appcenter does it
		docker login -e invalid -u ucs -p readonly docker.software-univention.de

		docker pull "$dockerimage"
		container_id=$(docker create "$dockerimage")
		docker start "$container_id"
		sleep 5 # some startup time...

		docker exec "$container_id" ucr set repository/online/server="$(ucr get repository/online/server)" \
			repository/app_center/server="$(ucr get repository/app_center/server)" \
			appcenter/index/verify="$(ucr get appcenter/index/verify)" \
			update/secure_apt="$(ucr get update/secure_apt)"

		# register required components
		apps="$app $(get_app_attr $app ApplianceAdditionalApps)"

		for the_app in $apps; do
			name=$(get_app_attr $the_app Name)
			component=$(app_get_component $the_app)
			component_prefix="repository/online/component/"
			docker exec "$container_id" ucr set ${component_prefix}${component}/description="$name" \
					${component_prefix}${component}/localmirror=false \
					${component_prefix}${component}/server="$(ucr get repository/app_center/server)" \
					${component_prefix}${component}/unmaintained=disabled \
					${component_prefix}${component}/version=current \
					${component_prefix}${component}=enabled
			# this has to be done on the docker host, the license agreement will be shown in the appliance system setup
			if [ -e "/var/cache/univention-appcenter/${component}.LICENSE_AGREEMENT" ]; then
				ucr set umc/web/appliance/data_path?"/var/cache/univention-appcenter/${component}."
			fi
		done

		"$php7_required" && docker exec "$container_id" ucr set repository/online/component/php7=enabled \
			repository/online/component/php7/version=current \
			repository/online/component/php7/server=http://updates-test.software-univention.de \
			repository/online/component/php7/description="PHP 7 for UCS" \
			repository/online/unmaintained=yes

		# provide required packages inside container
		docker exec "$container_id" apt-get update
		docker exec "$container_id" /usr/share/univention-docker-container-mode/download-packages $(get_app_attr ${app} DefaultPackages) $(get_app_attr ${app} DefaultPackagesMaster)
		docker exec "$container_id" apt-get update

		# shutdown container and use it as app base
		docker stop "$container_id"
		prepared_app_container_id=$(docker commit "$container_id" "${app}-app")
		docker rm "$container_id"

		cat >/root/provide_joinpwdfile.patch <<__EOF__
--- /usr/lib/univention-system-setup/scripts/10_basis/18root_password.orig      2016-10-27 16:40:47.296000000 +0200
+++ /usr/lib/univention-system-setup/scripts/10_basis/18root_password   2016-10-27 16:41:59.744000000 +0200
@@ -54,6 +54,10 @@

 root_password=\`get_profile_var "root_password"\`

+touch /tmp/joinpwd
+chmod 0600 /tmp/joinpwd
+echo -n "\$root_password" > /tmp/joinpwd
+
 sed -i 's|^root_password=.*|#root_password="***********"|g' /var/cache/univention-system-setup/profile

 if [ -z "\$root_password" ]; then
__EOF__
		univention-install -y patch
		patch -p0 < /root/provide_joinpwdfile.patch
		rm /root/provide_joinpwdfile.patch

		# clear old app joinscript
		cat >/usr/lib/univention-system-setup/scripts/00_system_setup/20remove_app_joinscript <<__EOF__
#!/bin/bash
APP=${app}

[ -e /usr/lib/univention-install/50\${APP}.inst ] && rm /usr/lib/univention-install/50\${APP}.inst

exit 0
__EOF__
		chmod 755 /usr/lib/univention-system-setup/scripts/00_system_setup/20remove_app_joinscript

		# reinstall the app
		cat >/usr/lib/univention-install/99setup_${app}.inst <<__EOF__
#!/bin/bash
. /usr/share/univention-join/joinscripthelper.lib
. /usr/share/univention-lib/ucr.sh
VERSION="1"

APP="$app"


joinscript_init
joinscript_save_current_version

# Only install the app if joinscript is run during system-setup
if is_ucr_true system/setup/boot/start; then
	# uninstall old app
	docker rm -f \$(ucr get appcenter/apps/\${APP}/container)
	univention-app register \${APP} --undo-it

	# install app
	python -c "from univention.appcenter.app_cache import Apps
from univention.appcenter.actions import get_action
from univention.appcenter.log import log_to_logfile, log_to_stream

log_to_stream()

app=Apps().find('\$APP')
app.docker_image='${app}-app'

install = get_action('install')
install.call(app=app, noninteractive=True, skip_checks=['must_have_valid_license'],pwdfile='/tmp/joinpwd')
"
fi
[ -e /tmp/joinpwd ] && rm /tmp/joinpwd

# fix docker app image name
ucr set appcenter/apps/${app}/image='${$dockerimage}'
__EOF__
		chmod 755 /usr/lib/univention-install/99setup_${app}.inst
	fi
}

register_apps ()
{
	app=$1

	# No docker app: Add app components manually
	if ! app_appliance_IsDockerApp $app; then
		apps="$app $(get_app_attr $app ApplianceAdditionalApps)"

		for the_app in $apps; do
			name=$(get_app_attr $the_app Name)
			component=$(app_get_component $the_app)
			component_prefix="repository/online/component/"
			ucr set ${component_prefix}${component}/description="$name" \
					${component_prefix}${component}/localmirror=false \
					${component_prefix}${component}/server="$(ucr get repository/app_center/server)" \
					${component_prefix}${component}/unmaintained=disabled \
					${component_prefix}${component}/version=current \
					${component_prefix}${component}=enabled
			if [ -e "/var/cache/univention-appcenter/${component}.LICENSE_AGREEMENT" ]; then
				ucr set umc/web/appliance/data_path?"/var/cache/univention-appcenter/${component}."
			fi
		done
	fi

	ucr set repository/online/unmaintained='yes'

	ucr set umc/web/appliance/id?${app}
	univention-install -y univention-app-appliance

	ucr set repository/online/unmaintained='no'

	apt-get update
}

install_pre_packages ()
{
	app=$1

	packages="$(get_app_attr $app AppliancePreInstalledPackages)"
	if [ -n "$packages" ]; then
		DEBIAN_FRONTEND=noninteractive apt-get -y install $packages
	fi

	if app_appliance_IsDockerApp $app; then
		DEBIAN_FRONTEND=noninteractive apt-get -y install "$(app_get_database_packages_for_docker_host $app)"
	fi
}

download_packages_and_dependencies ()
{
	app=$1

	# Only for non docker apps
	if ! app_appliance_IsDockerApp $app; then
		apps="$app $(get_app_attr $app ApplianceAdditionalApps)"

		mkdir -p /var/cache/univention-system-setup/packages/
		if [ ! -e /etc/apt/sources.list.d/05univention-system-setup.list ]; then
			echo "deb [trusted=yes] file:/var/cache/univention-system-setup/packages/ ./" >>/etc/apt/sources.list.d/05univention-system-setup.list
		fi

		cd /var/cache/univention-system-setup/packages/
		install_cmd="$(univention-config-registry get update/commands/install)"

		for app in $apps; do
				packages="$(get_app_attr ${app} DefaultPackages) $(get_app_attr ${app} DefaultPackagesMaster)"
			echo "Try to download: $packages"
			for package in $packages; do
				LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 ${package} | 
				apt-get download -o Dir::Cache::Archives=/var/cache/univention-system-setup/packages $(LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 ${package} | sed -ne 's|^Inst \([^ ]*\) .*|\1|p')

				check_returnvalue $? "Failed to download required packages for ${package}"
			done
			apt-ftparchive packages . >Packages
			check_returnvalue $? "Failed to create ftparchive directory"
			apt-get update
		done
	fi

	return 0
}

download_system_setup_packages ()
{
	app="$1"

	echo "download_system_setup_packages for $app"

	mkdir -p /var/cache/univention-system-setup/packages/
	(
		if [ ! -e /etc/apt/sources.list.d/05univention-system-setup.list ]; then
			echo "deb [trusted=yes] file:/var/cache/univention-system-setup/packages/ ./" >>/etc/apt/sources.list.d/05univention-system-setup.list
		fi

		cd /var/cache/univention-system-setup/packages/
		install_cmd="$(univention-config-registry get update/commands/install)"

		# server role packages
		packages="server-master server-backup server-slave server-member basesystem"

		# ad member mode
		packages="$packages ad-connector samba"

		# welcome-screen + dependencies for all roles
		# libgif4 is removed upon uninstalling X, so put it in package cache
		packages="$packages welcome-screen"

		if ! app_appliance_is_software_blacklisted $app; then
			packages="$packages management-console-module-adtakeover printserver printquota dhcp fetchmail kde radius virtual-machine-manager-node-kvm mail-server nagios-server pkgdb samba4 s4-connector squid virtual-machine-manager-daemon self-service self-service-passwordreset-umc self-service-master"
		fi

		for package in $packages; do
			LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 univention-${package} | 
			apt-get download -o Dir::Cache::Archives=/var/cache/univention-system-setup/packages $(LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 univention-${package} | sed -ne 's|^Inst \([^ ]*\) .*|\1|p')

			check_returnvalue $? "Failed to download required packages for univention-${package}"

			apt-ftparchive packages . >Packages
			check_returnvalue $? "Failed to create ftparchive directory"
			apt-get update
		done

		for package in firefox-esr-l10n-de; do
			LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 ${package} | 
			apt-get download -o Dir::Cache::Archives=/var/cache/univention-system-setup/packages $(LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 ${package} | sed -ne 's|^Inst \([^ ]*\) .*|\1|p')

			check_returnvalue $? "Failed to download required packages for ${package}"
		done

		apt-ftparchive packages . >Packages
		check_returnvalue $? "Failed to create ftparchive directory"
	)
}

create_install_script ()
{
	main_app=$1

	apps="$main_app $(get_app_attr $main_app ApplianceAdditionalApps)"

	# Only for non docker apps
	if ! app_appliance_IsDockerApp $main_app; then
		main_app_packages="$(get_app_attr ${main_app} DefaultPackages) $(get_app_attr ${main_app} DefaultPackagesMaster)"

		additional_app_packages=""
		for app in $apps; do
			additional_app_packages="$additional_app_packages $(get_app_attr ${app} DefaultPackages) $(get_app_attr ${app} DefaultPackagesMaster)"
		done
		# Due to dovect: https://forge.univention.org/bugzilla/show_bug.cgi?id=39148
		if [ "$main_app" = "oxseforucs" ] || [ "$main_app" = "egroupware" ] || [ "$main_app" = "horde" ] || [ "$main_app" = "tine20" ] || [ "$main_app" = "fortnox" ]; then
			close_fds=TRUE
		fi
		# Ticket #2015052821000587
		if [ "$main_app" = "kolab-enterprise" ]; then
			close_fds=TRUE
		fi

		# Ticket #2016051821000139
		if [ "$main_app" = "zarafa" ]; then
			close_fds=TRUE
		fi

		# Ticket #2016051821000139
		if [ "$main_app" = "kopano-core" ]; then
			close_fds=TRUE
		fi

		# Ticket #2016062321000191
		if [ "$main_app" = "kix2016" ]; then
			close_fds=TRUE
		fi
		
		cat >/usr/lib/univention-install/99setup_${main_app}.inst <<__EOF__
#!/bin/sh
. /usr/share/univention-join/joinscripthelper.lib
VERSION="1"
joinscript_init
eval "\$(ucr shell update/commands/install)"
export DEBIAN_FRONTEND=noninteractive
apt-get update
if [ "$close_fds" = "TRUE" ]; then
	echo "Close logfile output now. Please see /var/log/dpkg.log for more information"
	exec 1> /dev/null
	exec 2> /dev/null
fi
\$update_commands_install -y --force-yes -o="APT::Get::AllowUnauthenticated=1;" $main_app_packages || die
\$update_commands_install -y --force-yes -o="APT::Get::AllowUnauthenticated=1;" $additional_app_packages || die
joinscript_save_current_version
__EOF__
	# register each app individually
	for app in $apps; do
		local version="$(get_app_attr $app Version)"	
		local ucsversion="$(app_get_ini $app | sed -e 's/.*\(4\.2\|4\.1\).*/\1/')"
		echo "univention-app register --do-it ${ucsversion}/${app}=${version}" >> /usr/lib/univention-install/99setup_${main_app}.inst
	done

		cat >>/usr/lib/univention-install/99setup_${main_app}.inst <<__EOF__
if [ \$# -gt 1 ]; then
	. /usr/share/univention-lib/ldap.sh

	ucs_parseCredentials "\$@"
	dcaccount="\$(echo "\$binddn" | sed -ne 's|uid=||;s|,.*||p')"
	dcpwd="\$(mktemp)"
	echo -n "\$bindpwd" >\$dcpwd
	univention-run-join-scripts -dcaccount "\$dcaccount" -dcpwd "\$dcpwd"

	rm \$dcpwd
	unset binddn
	unset bindpwd

else
	univention-run-join-scripts
fi
invoke-rc.d ntp restart

# Use the first template as default (Bug #38832)
if [ -e /usr/share/univention-management-console-frontend/js/umc/modules/udm/wizards/FirstPageWizard.js ]; then
	sed -i 's|templates.unshift(|templates.push(|' /usr/share/univention-management-console-frontend/js/umc/modules/udm/wizards/FirstPageWizard.js
	. /usr/share/univention-lib/umc.sh
	umc_frontend_new_hash
fi
__EOF__
		chmod 755 /usr/lib/univention-install/99setup_${main_app}.inst
	fi
}

install_app_in_prejoined_setup ()
{
	main_app="$1"
	apps="$main_app $(get_app_attr $main_app ApplianceAdditionalApps)"

	# Only for non docker apps
	if ! app_appliance_IsDockerApp $app; then
		eval "$(ucr shell update/commands/install)"
		export DEBIAN_FRONTEND=noninteractive

		for app in $apps; do
			packages=""
			packages="$(get_app_attr ${app} DefaultPackages) $(get_app_attr ${app} DefaultPackagesMaster)"
			$update_commands_install -y --force-yes -o="APT::Get::AllowUnauthenticated=1;" $packages
			univention-run-join-scripts
		done
	fi
	for app in $apps; do
		local version="$(get_app_attr $app Version)"	
		local ucsversion="$(app_get_ini $app | sed -e 's/.*\(4\.2\|4\.1\).*/\1/')"
		univention-app register --do-it ${ucsversion}/${app}=${version}
	done
}

appliance_preinstall_non_univention_packages ()
{
	packages="
adwaita-icon-theme
apache2-suexec-pristine
bc
bind9
bind9utils
dconf-gsettings-backend
dconf-service
dictionaries-common
dpt-i2o-raidutils
elinks
elinks-data
emacs24
emacs24-bin-common
emacs24-common
emacsen-common
fbcat
fbi
fping
gconf-service
gconf2-common
ghostscript
glib-networking
glib-networking-common
glib-networking-services
gsettings-desktop-schemas
gsfonts
heimdal-kdc
heimdal-servers
ifplugd
imagemagick-common
libatk-bridge2.0-0
libatspi2.0-0
libblas-common
libblas3
libcairo-gobject2
libcolord2
libcupsfilters1
libcupsimage2
libdaemon0
libdconf1
libexif12
libfftw3-double3
libfile-copy-recursive-perl
libfribidi0
libfsplib0
libgconf-2-4
libgd3
libgfortran3
libgomp1
libgpm2
libgs9
libgs9-common
libgtk-3-0
libgtk-3-bin
libgtk-3-common
libharfbuzz-icu0
libijs-0.35
libio-socket-inet6-perl
libjbig2dec0
libjson-glib-1.0-0
libjson-glib-1.0-common
libkdc2-heimdal
libkpathsea6
liblinear1
liblqr-1-0
libltdl7
liblua5.2-0
libm17n-0
libmagickcore-6.q16-2
libmagickwand-6.q16-2
libmcrypt4
libnetpbm10
libnfsidmap2
libnl-3-200
libnl-genl-3-200
libnss-extrausers
libnss-ldap
libodbc1
libopenjpeg5
libopts25
libotf0
libpam-cracklib
libpam-heimdal
libpam-ldap
libpaper-utils
libpaper1
libpcap0.8
libperl5.20
libpoppler46
libpotrace0
libpq5
libproxy1
libptexenc1
libquadmath0
librest-0.7-0
libslp1
libsnmp-session-perl
libsocket6-perl
libsoup-gnome2.4-1
libsoup2.4-1
libsynctex1
libtirpc1
libtre5
libvpx1
libwayland-cursor0
libxkbcommon0
libyaml-0-2
libzzip-0-13
locate
m17n-db
memcached
monitoring-plugins
monitoring-plugins-basic
monitoring-plugins-common
monitoring-plugins-standard
mrtg
nagios-nrpe-server
nagios-plugins-basic
netpbm
nfs-common
nfs-kernel-server
nmap
nscd
ntp
ntpdate
openbsd-inetd
pam-runasroot
php-openid
php-pear
php-xml-parser
php5-cgi
php5-curl
php5-gmp
php5-ldap
php5-mcrypt
php5-memcache
poppler-data
postgresql-client-9.4
postgresql-client-common
preview-latex-style
python-ecdsa
python-egenix-mxdatetime
python-egenix-mxtools
python-paramiko
python-pycurl
python-pygresql
python-yaml
quota
rpcbind
simplesamlphp
slapd
stunnel4
sudo
sysvinit
tex-common
texlive
texlive-base
texlive-binaries
texlive-fonts-recommended
texlive-lang-german
texlive-latex-base
texlive-latex-extra
texlive-latex-recommended
texlive-pictures
unzip
update-inetd
vim
vim-runtime
wamerican
wngerman
xdg-utils
zip"
	for p in $packages; do
		DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends "$p"
	done
}

install_haveged ()
{
    _unmaintained_setting=$(ucr get repository/online/unmaintained)
    ucr set repository/online/unmaintained="yes"
    univention-install -y haveged
    ucr set repository/online/unmaintained="$_unmaintained_setting"
}

uninstall_packages ()
{
	# if upgraded, u-basesystem will be installed by postup.sh
	state="$(dpkg --get-selections univention-basesystem 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		apt-get purge -y --force-yes univention-basesystem
		apt-get -y --force-yes autoremove
	fi

	# Old kernels
	for kernel in ""; do
		apt-get purge -y --force-yes ${kernel}
	done
}

setup_pre_joined_environment ()
{
	# $1 = appid
	# $2 = domainname / derived ldapbase
	if app_appliance_AllowPreconfiguredSetup $1; then
		[ -z "${2}" ] && set -- "$1" "ucs.example"
		local domainname="${2}"
		local ldapbase="dc=${domainname//./,dc=}" # VERY simple ldap base derivation test.domain => dc=test,dc=domain
		cat >/var/cache/univention-system-setup/profile <<__EOF__
hostname="master"
domainname="${domainname}"
server/role="domaincontroller_master"
locale="de_DE.UTF-8:UTF-8 en_US.UTF-8:UTF-8"
interfaces/eth0/type="static"
timezone="Europe/Berlin"
gateway="10.203.0.1"
ssl/organizationalunit="Univention Corporate Server"
windows/domain="UCS"
packages_install=""
interfaces/eth0/start="true"
ad/member="False"
xorg/keyboard/options/XkbLayout="de"
interfaces/primary="eth0"
interfaces/eth0/broadcast="10.203.255.255"
packages_remove=""
ssl/organization="DE"
root_password="$appliance_default_password"
ssl/email="ssl@${domainname}"
ldap/base="${ldapbase}"
locale/default="de_DE.UTF-8:UTF-8"
nameserver1="192.168.0.3"
ssl/state="DE"
interfaces/eth0/ipv6/acceptRA="false"
ssl/locality="DE"
interfaces/eth0/netmask="255.255.0.0"
interfaces/eth0/network="10.203.0.0"
update/system/after/setup="True"
components=""
interfaces/eth0/address="10.203.10.40"
__EOF__
		ucr set umc/web/appliance/fast_setup_mode=true
		/usr/lib/univention-system-setup/scripts/setup-join.sh 2>&1 | tee /var/log/univention/setup.log
		echo "root:univention" | chpasswd
	else
		ucr set umc/web/appliance/fast_setup_mode=false
		echo "No prejoined environment configured (ApplianceAllowPreconfiguredSetup)"
	fi
}

setup_appliance ()
{
	# Stop firefox. Not required to run, and resets some UCRv (e.g. system/setup/boot/start)
	killall -9 firefox-esr

	# allow X11 login as normal user
	ucr set "auth/gdm/group/Domain Users"=yes
	 
	# Disable xorg autodetection and set resolution to 800x600 for system setup
	ucr set xorg/autodetect=no \
	  xorg/resolution=800x600
	# xorg/device/driver=''

	# Use fbdev as xorg driver
	mkdir -p /etc/X11/xorg.conf.d
	cat >/etc/X11/xorg.conf.d/use-fbdev-driver.conf <<__EOF__
Section "Device"
	Identifier  "Card0"
	Driver      "fbdev"
EndSection
__EOF__

	cat >/usr/lib/univention-system-setup/appliance-hooks.d/20_remove_xorg_config <<__EOF__
#!/bin/sh
rm /etc/X11/xorg.conf.d/use-fbdev-driver.conf
ucr set xorg/autodetect=yes
exit 0
__EOF__
	chmod +x /usr/lib/univention-system-setup/appliance-hooks.d/20_remove_xorg_config
	 
	# Disable kernel mode set
	# ucr set grub/append="nomodeset $(ucr get grub/append)"
	 
	# Show bootscreen in 800x600
	ucr set grub/gfxmode=800x600@16
	 
	# generate all UMC languages
	ucr set locale/default="en_US.UTF-8:UTF-8" locale="en_US.UTF-8:UTF-8 de_DE.UTF-8:UTF-8"; locale-gen

	install_haveged

	uninstall_packages

	univention-install -y --force-yes --reinstall univention-system-setup-boot
	# univention-install -y --no-install-recommends univention-x-core

	# shrink appliance image size
	appliance_preinstall_non_univention_packages
	rm /etc/apt/sources.list.d/05univention-system-setup.list
	rm -r /var/cache/univention-system-setup/packages/

	apt-get update
	download_system_setup_packages $@

	# Cleanup apt archive
	apt-get clean
	apt-get update

	# set initial system uuid (set to new value in setup-join.sh)
	ucr set uuid/system="00000000-0000-0000-0000-000000000000"
}

appliance_cleanup ()
{
	# after system setup is finished, boot in 1024x768 (not 800x600)
	cat >/usr/lib/univention-system-setup/appliance-hooks.d/screenresolution <<__EOF__
#!/bin/sh
ucr set grub/gfxmode=1024x768@16 \
	xorg/resolution=1024x768
__EOF__
	chmod +x /usr/lib/univention-system-setup/appliance-hooks.d/screenresolution

	# deactivate kernel module; prevents bootsplash from freezing in vmware
	ucr set kernel/blacklist="$(ucr get kernel/blacklist);vmwgfx"

 # Do network stuff

	# set initial values for UCR ssl variables
	/usr/sbin/univention-certificate-check-validity

	# Set official update server, deactivate online repository until system setup script 90_postjoin/20upgrade
	ucr set repository/online=no \
		repository/online/server='https://updates.software-univention.de'
	# ucr set repository/online/server=univention-repository.knut.univention.de

	# Cleanup apt archive
	apt-get update
	apt-get clean

	# Activate DHCP
	ucr set interfaces/eth0/type=dhcp dhclient/options/timeout=12
	ucr unset gateway
	 
	# Set a default nameserver and remove all local configured nameserver
	ucr set nameserver1=208.67.222.222 dns/forwarder1=208.67.222.222
	ucr unset nameserver2 nameserver3
	ucr unset dns/forwarder2 dns/forwarder3

	# Manual cleanup
	rm -rf /tmp/*
	for dir in python-cherrypy3 libwibble-dev texlive-base texlive-lang-german texmf texlive-latex-recommended groff-base libept-dev texlive-doc; do
		[ -d "/usr/share/doc/$dir" ] && rm -rf "/usr/share/doc/$dir"
	done

	# fill up HDD with ZEROs to maximize possible compression
	dd if=/dev/zero of=/fill-it-up bs=1M; rm /fill-it-up

	# Remove persistent net rule
	rm -f /etc/udev/rules.d/70-persistent-net.rules
	 
	ucr set system/setup/boot/start=true
}



appliance_basesettings ()
{
	set -x
	app=$1
	
	/usr/sbin/univention-app-appliance $app

	app_fav_list="appcenter:appcenter,updater"
	
	for a in $(get_app_attr $app ApplianceCategoryModules); do
		app_fav_list="$app_fav_list,$a"
	done
	
	# Set UMC favourites for administrator user
	cat >/usr/lib/univention-system-setup/appliance-hooks.d/umc-favorites <<__EOF__
#!/bin/bash
eval "\$(ucr shell)"
#old_fav=\$(udm users/user list --dn "uid=Administrator,cn=users,\$ldap_base" | grep "^  umcProperty: favorites = " | awk '{print \$4}')
#test -z "\$old_fav" && old_fav="appcenter:appcenter,updater,udm:users/user"
fav="favorites \$app_fav_list"
udm users/user modify --dn "uid=Administrator,cn=users,\$ldap_base" --set umcProperty="\$fav"
__EOF__
	chmod 755 /usr/lib/univention-system-setup/appliance-hooks.d/umc-favorites

	if app_appliance_IsDockerApp $app; then
		cat >/usr/lib/univention-system-setup/appliance-hooks.d/01_update_${app}_container_settings <<__EOF__
#!/bin/bash
eval "\$(ucr shell)"
APP=$app

# update host certificate in container
cp /etc/univention/ssl/ucsCA/CAcert.pem /var/lib/docker/overlay/\$(ucr get appcenter/apps/\$APP/container)/merged/etc/univention/ssl/ucsCA

# Fix container nameserver entries
univention-app shell "\$APP" ucr set nameserver1=\${nameserver1} ldap/master=\${ldap_master} ldap/server/name=\${ldap_server_name}
__EOF__
		chmod 755 /usr/lib/univention-system-setup/appliance-hooks.d/01_update_${app}_container_settings
	fi

	if [ "$app" = "owncloud82" ]; then
		cat >/usr/lib/univention-system-setup/appliance-hooks.d/99_fix_owncloud_trusted_domains <<__EOF__
#!/bin/bash

APP=owncloud82

# Fix trusted domains value
ips="\$(python  -c "
from univention.config_registry.interfaces import Interfaces
for name, iface in Interfaces().all_interfaces: print iface.get('address')")"

HOSTS="\$(ucr get hostname).\$(ucr get domainname)"

for ip in \$ips; do
	HOSTS="\${HOSTS}\n\${ip}"
done

univention-app shell "\$APP" sh -c "printf '\${HOSTS}' > /tmp/trusted_domain_hosts"
univention-app shell "\$APP" /usr/sbin/fix_owncloud_trusted_domains

__EOF__
	chmod 755 /usr/lib/univention-system-setup/appliance-hooks.d/99_fix_owncloud_trusted_domains
	fi
}

install_appreport ()
{
	ucr set repository/online/component/appreport=yes \
		repository/online/component/appreport/version="4.0"
	cat >/usr/lib/univention-system-setup/appliance-hooks.d/install-appreport <<__EOF__
#!/bin/sh
univention-install -y --force-yes univention-appreport
__EOF__
	chmod +x /usr/lib/univention-system-setup/appliance-hooks.d/install-appreport
}

appliance_reset_servers ()
{
	ucr set repository/online/server="https://updates.software-univention.de/"
	ucr unset appcenter/index/verify
       	ucr set update/secure_apt=yes

	ucr search --brief --value "^appcenter-test.software-univention.de$" | sed -ne 's|: .*||p' | while read key; do
		ucr set "$key=appcenter.software-univention.de"
	done
}

disable_root_login_and_poweroff ()
{
	if [ "${1}" = "DISABLE_ROOTLOGIN" ]; then
		ucr set --force auth/sshd/user/root=no
		echo "root:$appliance_default_password" | chpasswd
	fi
	rm /root/*
	rm /root/.bash_history
	history -c
	halt -p
}

appliance_poweroff ()
{
	rm /root/*
	rm /root/.bash_history
	history -c
	halt -p
}
