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

set -x
set -e

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
	python -c "
from univention.appcenter.app_cache import Apps
from univention.appcenter.database import DatabaseConnector

app=Apps().find('$app')
d = DatabaseConnector.get_connector(app)
if d:
	print ' '.join(d._get_software_packages())"
}

app_get_component ()
{
	local app=$1
	python -c "
from univention.appcenter.app_cache import Apps
app = Apps().find('$app')
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

app_has_no_repository ()
{
	local app="$1"
	[ -z "$app" ] && return 1
	local value="$(get_app_attr $app WithoutRepository)"
	echo "$value" | grep -qs True 
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
	local image="$(get_app_attr $app dockerimage)"
	test -n "$image" && return 0
	return 1
}

appliance_app_has_external_docker_image ()
{
	local app="$1"
	image="$(get_app_attr $app DockerImage)"
	echo "Docker image: $image"
	if echo "$image" | grep -qs "ucs-appbox" ; then
		return 1
	else
		return 0
	fi
}

prepare_docker_app_container ()
{
	local main_app="$1"
	local extra_packages=""

	for app in $main_app $(get_app_attr $main_app ApplianceAdditionalApps); do
		if app_appliance_IsDockerApp "$app"; then
			php7_required=false
			for i in "owncloud82" "egroupware"; do
				if [ "$i" == "$app" ]; then
					php7_required=true
				fi
			done
			if [ "$app" == "egroupware" ]; then
				extra_packages="libapache2-mod-php php-tidy php-gd php-imap php-ldap php-xsl php-mysql php-common apache2-mpm-prefork php-mbstring"
			fi
			local dockerimage="$(get_app_attr $app DockerImage)"
			if [ "$?" != 0 ]; then
				echo "Error: No docker image for docker app!"
				exit 1
			fi
			# generate .dockercfg as appcenter does it
			docker login -e invalid -u ucs -p readonly docker.software-univention.de
			docker pull "$dockerimage"
			local local_app_docker_image="$dockerimage"
			if ! appliance_app_has_external_docker_image $app; then
					container_id=$(docker create "$dockerimage")
					docker start "$container_id"
					sleep 5 # some startup time...
					docker exec "$container_id" ucr set repository/online/server="$(ucr get repository/online/server)" \
						repository/app_center/server="$(ucr get repository/app_center/server)" \
						appcenter/index/verify="$(ucr get appcenter/index/verify)" \
						update/secure_apt="$(ucr get update/secure_apt)"
					# activate app repo
					local name=$(get_app_attr $app Name)
					local component=$(app_get_component $app)
					local component_prefix="repository/online/component/"
					docker exec "$container_id" ucr set ${component_prefix}${component}/description="$name" \
						${component_prefix}${component}/localmirror=false \
						${component_prefix}${component}/server="$(ucr get repository/app_center/server)" \
						${component_prefix}${component}/unmaintained=disabled \
						${component_prefix}${component}/version=current \
						${component_prefix}${component}=enabled
					# TODO
					# this has to be done on the docker host, the license agreement will be shown in the appliance system setup
					#if [ -e "/var/cache/univention-appcenter/${component}.LICENSE_AGREEMENT" ]; then
					#	ucr set umc/web/appliance/data_path?"/var/cache/univention-appcenter/${component}."
					#fi
					# php 7 ?
					"$php7_required" && docker exec "$container_id" ucr set \
						repository/online/component/php7=enabled \
						repository/online/component/php7/version=current \
						repository/online/component/php7/server=https://updates.software-univention.de \
						repository/online/component/php7/description="PHP 7 for UCS"
					# provide required packages inside container
					docker exec "$container_id" apt-get update
					docker exec "$container_id" /usr/share/univention-docker-container-mode/download-packages $(get_app_attr ${app} DefaultPackages) $(get_app_attr ${app} DefaultPackagesMaster) $extra_packages
					docker exec "$container_id" apt-get update
					# check if packages are downloaded
					for i in $(get_app_attr ${app} DefaultPackages) $(get_app_attr ${app} DefaultPackagesMaster); do
						docker exec "$container_id" ls /var/cache/univention-system-setup/packages/ | grep $i
					done
					# shutdown container and use it as app base
					docker stop "$container_id"
					local_app_docker_image=$(docker commit "$container_id" "${app}-app-image")
					local_app_docker_image="${app}-app-image"
					docker rm "$container_id"
			fi

			# clear old app
			cat >/usr/lib/univention-system-setup/scripts/00_system_setup/20remove_docker_app_${app} <<__EOF__
#!/bin/bash

set -x

APP=${app}
DEMO_MODE=\$(echo "\$@" | grep -q "\\-\\-demo-mode" && echo 1)

if [ "\$DEMO_MODE" != 1 ]; then
	univention-app remove \${APP} --noninteractive --do-not-backup
	if [ -d "/var/lib/univention-appcenter/apps/\${APP}/" ]; then
		rm -rf "/var/lib/univention-appcenter/apps/\${APP}/"
	fi
fi

exit 0
__EOF__
			chmod 755 /usr/lib/univention-system-setup/scripts/00_system_setup/20remove_docker_app_${app}

			# reinstall the app
			cat >/usr/lib/univention-install/99setup_docker_${app}.inst <<__EOF__
#!/bin/bash
. /usr/share/univention-join/joinscripthelper.lib
. /usr/share/univention-lib/ucr.sh
VERSION="1"

APP="$app"


joinscript_init
joinscript_save_current_version

# Only install the app if joinscript is run during system-setup
if [ -n "\$(pgrep -f /usr/lib/univention-system-setup/scripts/setup-join.sh)" ]; then
	# install app, without index verification (needs internet)
	ucr set --force appcenter/index/verify=false
	python -c "from univention.appcenter.app_cache import Apps
from univention.appcenter.actions import get_action
from univention.appcenter.log import log_to_logfile, log_to_stream

log_to_stream()

app=Apps().find('\$APP')
app.docker_image='${local_app_docker_image}'

install = get_action('install')
install.call(app=app, noninteractive=True, skip_checks=['must_have_valid_license'], pwdfile='/tmp/joinpwd', pull_image=False)
"
fi

# fix docker app image name
ucr unset --force appcenter/index/verify
ucr set appcenter/apps/${app}/image="${dockerimage}"
__EOF__
			chmod 755 /usr/lib/univention-install/99setup_docker_${app}.inst

		fi
	done


	# save setup password
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
	patch -d/ -p0 < /root/provide_joinpwdfile.patch
	rm /root/provide_joinpwdfile.patch

	# delete setup password
	cat >/usr/lib/univention-system-setup/appliance-hooks.d/99_remove_password <<__EOF__
#!/bin/bash
[ -e /tmp/joinpwd ] && rm /tmp/joinpwd
invoke-rc.d ntp restart
__EOF__
	chmod 755 /usr/lib/univention-system-setup/appliance-hooks.d/99_remove_password

}

register_apps ()
{
	local main_app=$1

	# No docker app: Add app components manually
	for app in $main_app $(get_app_attr $main_app ApplianceAdditionalApps); do
		if ! app_appliance_IsDockerApp $app; then
			if app_has_no_repository $app; then
				continue
			fi
			name=$(get_app_attr $app Name)
			component=$(app_get_component $app)
			component_prefix="repository/online/component/"
			ucr set ${component_prefix}${component}/description="$name" \
					${component_prefix}${component}/localmirror=false \
					${component_prefix}${component}/server="$(ucr get repository/app_center/server)" \
					${component_prefix}${component}/unmaintained=disabled \
					${component_prefix}${component}/version=current \
					${component_prefix}${component}=enabled
			# TODO license stuff
			#if [ -e "/var/cache/univention-appcenter/${component}.LICENSE_AGREEMENT" ]; then
			#	ucr set umc/web/appliance/data_path?"/var/cache/univention-appcenter/${component}."
			#fi
		fi
	done

	ucr set repository/online/unmaintained='yes'
	ucr set umc/web/appliance/id?${main_app}
	univention-install -y univention-app-appliance
	ucr set repository/online/unmaintained='no'
	apt-get update
}

download_packages_and_dependencies ()
{
	local main_app=$1

	for app in $main_app $(get_app_attr $main_app ApplianceAdditionalApps); do

		# pre installed packages
		packages="$(get_app_attr $app AppliancePreInstalledPackages)"
		if [ -n "$packages" ]; then
			DEBIAN_FRONTEND=noninteractive apt-get -y install $packages

		fi
		# database packages for docker app
		if app_appliance_IsDockerApp $app; then
			DEBIAN_FRONTEND=noninteractive apt-get -y install "$(app_get_database_packages_for_docker_host $app)"
		fi

		# default packages for non-docker apps
		if ! app_appliance_IsDockerApp $app; then
			mkdir -p /var/cache/univention-system-setup/packages/
			if [ ! -e /etc/apt/sources.list.d/05univention-system-setup.list ]; then
				echo "deb [trusted=yes] file:/var/cache/univention-system-setup/packages/ ./" >>/etc/apt/sources.list.d/05univention-system-setup.list
			fi
			cd /var/cache/univention-system-setup/packages/
			local install_cmd="$(univention-config-registry get update/commands/install)"
			local packages="$(get_app_attr ${app} DefaultPackages) $(get_app_attr ${app} DefaultPackagesMaster)"
			echo "Try to download: $packages"
			for package in $packages; do
				LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 ${package} | 
				apt-get download -o Dir::Cache::Archives=/var/cache/univention-system-setup/packages \
					$(LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 ${package} | sed -ne 's|^Inst \([^ ]*\) .*|\1|p')
			done
			apt-ftparchive packages . >Packages
			apt-get update
		fi
	done
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
	local main_app=$1

	for app in $main_app $(get_app_attr $main_app ApplianceAdditionalApps); do
		# Only for non docker apps
		if ! app_appliance_IsDockerApp $app; then
			local packages="$(get_app_attr ${app} DefaultPackages) $(get_app_attr ${app} DefaultPackagesMaster)"
			local version="$(get_app_attr $app Version)"
			local ucsversion="$(app_get_ini $app | awk -F / '{print $(NF-1)}')"
			# Due to dovect: https://forge.univention.org/bugzilla/show_bug.cgi?id=39148
			for i in oxseforucs egroupware horde tine20 fortnox kolab-enterprise zarafa kopano-core kix2016; do
				test "$i" = "$app" && close_fds=TRUE
			done
			cat >/usr/lib/univention-install/99setup_package_${app}.inst <<__EOF__
#!/bin/bash

. /usr/share/univention-join/joinscripthelper.lib

set -x

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
\$update_commands_install -y --force-yes -o="APT::Get::AllowUnauthenticated=1;" $packages || die
joinscript_save_current_version
univention-app register --do-it ${ucsversion}/${app}=${version}

exit 0
__EOF__
			chmod 755 /usr/lib/univention-install/99setup_package_${app}.inst
		fi
	done


	# always ensure join scripts
	cat >/usr/lib/univention-install/99x_ensure_join.inst <<__EOF__
#!/bin/bash

. /usr/share/univention-join/joinscripthelper.lib

set -x

VERSION="1"
joinscript_init
joinscript_save_current_version

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

exit 0
__EOF__
	chmod 755 /usr/lib/univention-install/99x_ensure_join.inst
}

install_app_in_prejoined_setup ()
{

	local fastdemomode="unknown"
	local main_app="$1"
	local mode="$2"
	if app_appliance_AllowPreconfiguredSetup "$main_app"; then
		fastdemomode="yes"
	fi
	if [ "ignore" != "$mode" ]; then
		fastdemomode="$mode"
	fi
	if [ "yes" != "$fastdemomode" ]; then
		return 0
	fi
	for app in $main_app $(get_app_attr $main_app ApplianceAdditionalApps); do
		if ! app_appliance_IsDockerApp $app; then
			# Only for non docker apps
			eval "$(ucr shell update/commands/install)"
			export DEBIAN_FRONTEND=noninteractive
			local packages="$(get_app_attr ${app} DefaultPackages) $(get_app_attr ${app} DefaultPackagesMaster)"
			if [ -n "$packages" ]; then
				$update_commands_install -y --force-yes -o="APT::Get::AllowUnauthenticated=1;" $packages
			fi
			univention-run-join-scripts
		fi
		local version="$(get_app_attr $app Version)"	
		local ucsversion="$(app_get_ini $app | awk -F / '{print $(NF-1)}')"
		univention-app register --do-it ${ucsversion}/${app}=${version}
	done
}

appliance_preinstall_common_role ()
{
	DEBIAN_FRONTEND=noninteractive univention-install -y univention-role-common
	DEBIAN_FRONTEND=noninteractive univention-install -y univention-role-server-common
}

appliance_preinstall_non_univention_packages ()
{
	packages="
libblas-common
libblas3
libcap2-bin
libcupsfilters1
libcupsimage2
libdaemon0
libdbi1
libfftw3-double3
libfile-copy-recursive-perl
libfribidi0
libfsplib0
libgconf-2-4
libgd3
libgfortran3
libgnutls-dane0
libgomp1
libgpm2
libgs9
libgs9-common
libijs-0.35
libio-socket-inet6-perl
libirs141
libjbig2dec0
libkdc2-heimdal
liblinear3
liblqr-1-0
libltdl7
liblua5.1-0
liblua5.3-0
libm17n-0
libmagickcore-6.q16-3
libmagickwand-6.q16-3
libmcrypt4
libnet-snmp-perl
libnetpbm10
libnfsidmap2
libnl-3-200
libnl-genl-3-200
libnss-extrausers
libnss-ldap
libodbc1
libopenjp2-7
libopts25
libotf0
libpam-cap
libpam-cracklib
libpam-heimdal
libpam-ldap
libpaper-utils
libpaper1
libpcap0.8
libpq5
libquadmath0
libradcli4
libsnmp-base
libsnmp-session-perl
libsnmp30
libsocket6-perl
libtirpc1
libtre5
libunbound2
libyaml-0-2
bind9
emacs24
ifplugd
ntp
sudo
vim
zip"
	local instpackages=
	for p in $packages; do
		instpackages="$instpackages $p"
	done
	DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends $instpackages
}

install_haveged ()
{
    _unmaintained_setting=$(ucr get repository/online/unmaintained)
    ucr set repository/online/unmaintained="yes"
    univention-install -y haveged
    ucr set repository/online/unmaintained="$_unmaintained_setting"
}

backup_current_local_packagecache ()
{
	mkdir -p /var/cache/univention-system-setup/packages_backup
	cp -r /var/cache/univention-system-setup/packages/* /var/cache/univention-system-setup/packages_backup
}

restore_current_local_packagecache ()
{
	mv /var/cache/univention-system-setup/packages_backup/* /var/cache/univention-system-setup/packages
	rm -r /var/cache/univention-system-setup/packages_backup
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
	for kernel in "linux-image-4.9.0-ucs103-amd64 linux-image-4.9.0-ucs103-amd64-signed linux-image-4.9.0-ucs104-amd64 linux-image-4.9.0-ucs104-amd64-signed"; do
		DEBIAN_FRONTEND=noninteractive apt-get purge -y --force-yes ${kernel}
	done
}

setup_pre_joined_environment ()
{
	# $1 = appid
	# $2 = domainname / derived ldapbase
	fastdemomode="unknown"
	if app_appliance_AllowPreconfiguredSetup $1; then
			fastdemomode="yes"
	fi
	if [ "ignore" != "$FORCEFASTDEMOMODE" ]; then
			fastdemomode="$FORCEFASTDEMOMODE"
			ucr set --force umc/web/appliance/fast_setup_mode="$fastdemomode"
	fi
	if [ "yes" = "$fastdemomode" ]; then
		[ -z "${2}" ] && set -- "$1" "ucs.example"
		local domainname="${2}"
		local ldapbase="dc=${domainname//./,dc=}" # VERY simple ldap base derivation test.domain => dc=test,dc=domain
		cat >/var/cache/univention-system-setup/profile <<__EOF__
hostname="master"
domainname="${domainname}"
server/role="domaincontroller_master"
locale="en_US.UTF-8:UTF-8 de_DE.UTF-8:UTF-8"
interfaces/eth0/type="static"
timezone="Europe/Berlin"
gateway="10.203.0.1"
ssl/organizationalunit="Univention Corporate Server"
windows/domain="UCS"
packages_install=""
interfaces/eth0/start="true"
ad/member="False"
xorg/keyboard/options/XkbLayout="en"
interfaces/primary="eth0"
interfaces/eth0/broadcast="10.203.255.255"
packages_remove=""
ssl/organization="EN"
root_password="$appliance_default_password"
ssl/email="ssl@${domainname}"
ldap/base="${ldapbase}"
locale/default="en_US.UTF-8:UTF-8"
nameserver1="192.168.0.3"
ssl/state="EN"
interfaces/eth0/ipv6/acceptRA="false"
ssl/locality="EN"
interfaces/eth0/netmask="255.255.0.0"
interfaces/eth0/network="10.203.0.0"
update/system/after/setup="True"
components=""
interfaces/eth0/address="10.203.10.40"
__EOF__
		ucr set umc/web/appliance/fast_setup_mode=true
		# may have been set to false if u-s-s has been removed
		ucr set system/setup/boot/start=true
		/usr/lib/univention-system-setup/scripts/setup-join.sh 2>&1 | tee /var/log/univention/setup.log
		echo "root:univention" | chpasswd
		# set same address as in the profile, otherwise the ldap will not be updated
		ucr set system/setup/boot/old_ipv4=10.203.10.40
		# We still need u-s-s-boot, so reinstall it
		univention-install -y --force-yes --reinstall univention-system-setup-boot
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
	ucr set xorg/autodetect=no xorg/resolution=800x600

	# Disable kernel mode set
	# ucr set grub/append="nomodeset $(ucr get grub/append)"
	
	# Disable interface renaming	
	ucr set grub/append="$(ucr get grub/append) net.ifnames=0"

	# Show bootscreen in 800x600
	ucr set grub/gfxmode=800x600@16
	 
	# generate all UMC languages
	ucr set locale/default="en_US.UTF-8:UTF-8" locale="en_US.UTF-8:UTF-8 de_DE.UTF-8:UTF-8"; locale-gen

	install_haveged

	uninstall_packages

	univention-install -y --force-yes --reinstall univention-system-setup-boot

	# shrink appliance image size
	appliance_preinstall_non_univention_packages
	rm /etc/apt/sources.list.d/05univention-system-setup.list
	rm -r /var/cache/univention-system-setup/packages/

	apt-get update
	download_system_setup_packages $@

	# Cleanup apt archive
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

	cat >/usr/lib/univention-system-setup/appliance-hooks.d/postfix_restart <<__EOF__
#!/bin/sh
if [ -x /etc/init.d/postfix ]; then
	service postfix restart
fi
exit 0
__EOF__
	chmod +x /usr/lib/univention-system-setup/appliance-hooks.d/postfix_restart

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
	 
	# deactivate kernel module; prevents bootsplash from freezing in vmware
	ucr set kernel/blacklist="$(ucr get kernel/blacklist);vmwgfx"

	# Do network stuff

	# set initial values for UCR ssl variables
	/usr/sbin/univention-certificate-check-validity

	# Set official update server, deactivate online repository until system setup script 90_postjoin/20upgrade
	ucr set repository/online=false \
		repository/online/server='https://updates.software-univention.de'
	# ucr set repository/online/server=univention-repository.knut.univention.de

	if [ ! -e /etc/apt/sources.list.d/05univention-system-setup.list ]; then
		echo "deb [trusted=yes] file:/var/cache/univention-system-setup/packages/ ./" >>/etc/apt/sources.list.d/05univention-system-setup.list
	fi

	rm -rf /root/shared-utils/ || true

	# Cleanup apt archive
	apt-get clean
	apt-get update

	# Activate DHCP
	ucr set interfaces/eth0/type=dhcp dhclient/options/timeout=12
	ucr unset gateway
	 
	# Set a default nameserver and remove all local configured nameserver
	ucr set nameserver1=208.67.222.222
	ucr unset nameserver2 nameserver3
	ucr unset dns/forwarder2 dns/forwarder3

	ucr unset interfaces/ens3/address \
			interfaces/ens3/broadcast \
			interfaces/ens3/netmask \
			interfaces/ens3/network \
			interfaces/ens3/type

	ucr unset interfaces/primary

    ucr set update/secure_apt=yes
	# Manual cleanup
	rm -rf /tmp/*
	for dir in python-cherrypy3 libwibble-dev texlive-base texlive-lang-german texmf texlive-latex-recommended groff-base libept-dev texlive-doc; do
		[ -d "/usr/share/doc/$dir" ] && rm -rf "/usr/share/doc/$dir"
	done

	[ -e /var/lib/logrotate/status ] && :> /var/lib/logrotate/status
	test -e /var/mail/systemmail && rm /var/mail/systemmail
	rm -r /var/univention-backup/* || true

	# fill up HDD with ZEROs to maximize possible compression
	dd if=/dev/zero of=/fill-it-up bs=1M || true
	rm /fill-it-up

	# Remove persistent net rule
	rm -f /etc/udev/rules.d/70-persistent-net.rules
	 
	ucr set system/setup/boot/start=true
}



appliance_basesettings ()
{
	local main_app=$1
	
	/usr/sbin/univention-app-appliance --not-configure-portal $main_app

	# Set UMC favourites for administrator user
	local app_fav_list="appcenter:appcenter,updater"
	for a in $(get_app_attr $main_app ApplianceFavoriteModules); do
		app_fav_list="$app_fav_list,$a"
	done
	cat >/usr/lib/univention-system-setup/appliance-hooks.d/umc-favorites <<__EOF__
#!/bin/bash

. /usr/share/univention-lib/base.sh
eval "\$(ucr shell)"

set -x

fav="favorites $app_fav_list"
admin_uid=\$(custom_username Administrator)
udm users/user modify --dn "uid=\$admin_uid,cn=users,\$ldap_base" --set umcProperty="\$fav"

exit 0
__EOF__
	chmod 755 /usr/lib/univention-system-setup/appliance-hooks.d/umc-favorites

	for app in $main_app $(get_app_attr $main_app ApplianceAdditionalApps); do

		# update docker container
		if app_appliance_IsDockerApp $app; then
			cat >/usr/lib/univention-system-setup/appliance-hooks.d/01_update_${app}_container_settings <<__EOF__
#!/bin/bash
eval "\$(ucr shell)"
. /usr/share/univention-lib/ldap.sh

set -x

APP=$app
CONTAINER=\$(ucr get "appcenter/apps/\$APP/container")

# update ca certificates in container
docker cp /etc/univention/ssl/ucsCA/CAcert.pem \$CONTAINER:/etc/univention/ssl/ucsCA/
docker cp /etc/univention/ssl/ucsCA/CAcert.pem \$CONTAINER:/usr/local/share/ca-certificates/

# update host certificates in container
CONTAINER_HOSTNAME=\$(ucs_getAttrOfDN cn \$(ucr get \$(univention-app get "\$APP" ucr_hostdn_key --values-only)))
if [ -n "\$CONTAINER_HOSTNAME" ]; then
	docker cp /etc/univention/ssl/"\$CONTAINER_HOSTNAME"/cert.pem \$CONTAINER:/etc/univention/ssl/"\$CONTAINER_HOSTNAME/"
	docker cp /etc/univention/ssl/"\$CONTAINER_HOSTNAME"/cert.pem \$CONTAINER:/etc/univention/ssl/"\$CONTAINER_HOSTNAME"."\$domainname/"
fi

# Fix container nameserver entries
container_id=\$(ucr get "appcenter/apps/\$APP/container")
configfile_base="/var/lib/docker/containers/\$container_id"

docker stop "\$container_id"

for configfile in "\$configfile_base/config.json" "\$configfile_base/config.v2.json"; do
	[ -e "\$configfile" ] && python -c "import json
from univention.config_registry import ConfigRegistry
ucr = ConfigRegistry()
ucr.load()
config = {}
with open('\$configfile', 'r') as configfile:
  config=json.load(configfile)
  for i, v in enumerate(config['Config']['Env']):
    if v.startswith('nameserver1='):
       config['Config']['Env'][i] = 'nameserver1=%s' % ucr.get('nameserver1')
    if v.startswith('NAMESERVER1='):
       config['Config']['Env'][i] = 'NAMESERVER1=%s' % ucr.get('nameserver1')
    if v.startswith('nameserver2='):
       config['Config']['Env'][i] = 'nameserver2=%s' % ucr.get('nameserver2')
    if v.startswith('NAMESERVER2='):
       config['Config']['Env'][i] = 'NAMESERVER2=%s' % ucr.get('nameserver2')

with open('\$configfile', 'w') as configwriter:
  json.dump(config, configwriter)
"
done

service docker restart
docker start "\$container_id"

__EOF__
			chmod 755 /usr/lib/univention-system-setup/appliance-hooks.d/01_update_${app}_container_settings
		fi

		if [ "$app" = "mattermost" ]; then
			cat >/usr/lib/univention-system-setup/cleanup-post.d/99_reconfigure_mattermost <<__EOF__
#!/bin/bash

# During system-setup, apache2 uses temporary certificates, configured by UCR.
# These are also configured by mattermost.
# Reconfiguring the app will use the correct certs.

univention-app configure mattermost

__EOF__
			chmod 755 /usr/lib/univention-system-setup/cleanup-post.d/99_reconfigure_mattermost
		fi
	done
}


setup_ec2 ()
{
	ucr set grub/append="$(ucr get grub/append) console=tty0 console=ttyS0"

	DEV='/dev/xvda' GRUB='(hd0)'
    echo "${GRUB} ${DEV}" >/boot/grub/device.map
	debconf-communicate <<<"set grub-pc/install_devices $DEV"

	append="$(ucr get grub/append |
	    sed -re "s|/dev/sda|${DEV}|g;s|(no)?splash||g")"

	ucr set server/amazon=true \
		updater/identify="UCS (EC2)" \
		locale="en_US.UTF-8:UTF-8 de_DE.UTF-8:UTF-8" \
		grub/bootsplash=no \
		grub/quiet=no \
		grub/append="${append}" \
		grub/boot=${DEV} \
		grub/root=${DEV}1 \
		grub/grub1root=${GRUB} \
		grub/rootdelay=0 \
		grub/timeout=0 \
		grub/generate-menu-lst=no \
		grub/terminal="console serial" \
		grub/serialcommand="serial --unit=0 --speed=115200 --word=8 --parity=no --stop=1"

	rm -f /boot/grub/menu.lst # This still is evaluated by AWS-EC2 if it exists!
	update-grub

	apt-get purge -y univention-firewall univention-ifplugd univention-basesystem ifplugd libdaemon0
	univention-install -y cloud-initramfs-growroot patch gdisk
	mv /usr/share/initramfs-tools/scripts/local-bottom/growroot /usr/share/initramfs-tools/scripts/init-premount/
	###### cp growroot.patch
	cat > /root/growroot.patch <<__EOF__
--- /usr/share/initramfs-tools/scripts/init-premount/growroot.orig  2017-09-06 11:21:31.340000000 -0400
+++ /usr/share/initramfs-tools/scripts/init-premount/growroot   2017-09-06 11:21:51.044000000 -0400
@@ -1,5 +1,7 @@
 #!/bin/sh
  set -e

+udevadm settle --timeout \${ROOTDELAY:-30}
+ 
 PREREQS=""
 case \$1 in
@@ -73,10 +73,6 @@
 	*) msg "exited '\$ret'" "\${out}"; exit 1;;
 esac

-# There was something to do, unmount and resize
-umount "\${rootmnt}" ||
-	fail "failed to umount \${rootmnt}";
-
 # Wait for any of the initial udev events to finish
 # This is to avoid any other processes using the block device that the
 # root partition is on, which would cause the sfdisk 'BLKRRPART' to fail.
@@ -98,19 +94,4 @@
 # so that the root partition is available when we try and mount it.
 udevadm settle --timeout \${ROOTDELAY:-30}

-# this is taken from 'mountroot' function
-#   see /usr/share/initramfs-tools/scripts/local
-if [ -z "\${ROOTFSTYPE}" ]; then
-	FSTYPE=\$(get_fstype "\${ROOT}")
-else
-	FSTYPE=\${ROOTFSTYPE}
-fi
-roflag="-r"
-[ "\${readonly}" = "y" ] || roflag="-w"
-mount \${roflag} \${FSTYPE:+-t \${FSTYPE} }\${ROOTFLAGS} \${ROOT} \${rootmnt} ||
-	fail "failed to re-mount \${ROOT}. this is bad!"
-
-# write to /etc/grownroot-grown. most likely this wont work (readonly)
-{ date --utc > "\${rootmnt}/etc/growroot-grown" ; } >/dev/null 2>&1 || :
-
 # vi: ts=4 noexpandtab
__EOF__

	patch -p1 -d/ < growroot.patch
	rm growroot.patch
	update-initramfs -uk all

	# resize2fs
	cat > /etc/init.d/resize2fs <<__EOF__
#!/bin/bash
### BEGIN INIT INFO
# Provides:          resize2fs
# Required-Start:    \$local_fs
# Required-Stop:
# Default-Start:     2
# Default-Stop:
# Short-Description: resize filesystem upon boot
### END INIT INFO

resize2fs /dev/xvda1 &
disown
__EOF__
	chmod +x /etc/init.d/resize2fs
	update-rc.d resize2fs defaults

	univention-system-setup-boot start
	ucr set apache2/startsite="univention/initialsetup/"
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
	if ! $1; then
		ucr set --force auth/sshd/user/root=no
		echo "root:$appliance_default_password" | chpasswd
	fi
	rm -r /root/* || true
	rm /root/.bash_history || true
	history -c
	echo "halt -p" | at now || true
}

appliance_poweroff ()
{
	rm -r /root/* || true
	rm /root/.bash_history || true
	history -c
	echo "halt -p" | at now || true
}

appliance_test_appcenter () {
	if $1; then
		univention-install --yes univention-appcenter-dev
		univention-app dev-use-test-appcenter
	fi
}
