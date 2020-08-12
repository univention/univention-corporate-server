#!/bin/bash

set -x
set -e

setup_00026 () {
	local role=${1:?missing role}
	. utils.sh && basic_setup
	. utils.sh && add_tech_key_authorized_keys
	. utils.sh && rotate_logfiles
	. utils.sh && upgrade_to_latest_patchlevel
	# install package list from 00026
	# TODO lot of unknown package, univention-grub is removed?
	#while read package; do
	#	apt-get -y install $package || true
	#done < product-tests/extsec4.3/00026/binary-packages/${role}/binpkg-${role}.txt
}

sec_updates_00026 () {
	echo -e "deb [trusted=yes] http://192.168.0.10/build2/ ucs_4.3-0-extsec4.3/all/\ndeb [trusted=yes] http://192.168.0.10/build2/ ucs_4.3-0-extsec4.3/\$(ARCH)/\n" > /etc/apt/sources.list.d/extsec43.list
	apt-get -y update
	apt-get -y update | grep extsec4.3
	. utils.sh && upgrade_to_latest_errata
}
