#!/bin/bash
#
# Copyright 2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

set -x

. utils.sh

fakepackage() { equivs-control "$1" && sed "s/^Package: .*/Package: $1/g; s/^# Version:.*/Version: ${2:-1.0}/g" -i "$1" && equivs-build "$1" && dpkg -i "$1"_*.deb; }

fake_package_install () {
	install_with_unmaintained equivs
	fakepackage python3-trml2pdf
	install_with_unmaintained \
		python3-univention \
		python3-univention-admin-diary \
		python3-univention-admin-diary-backend \
		python3-univention-app-appliance \
		python3-univention-appcenter \
		python3-univention-appcenter-dev \
		python3-univention-appcenter-docker \
		python3-univention-config-registry \
		python3-univention-connector-s4 \
		python3-univention-debug \
		python3-univention-directory-manager \
		python3-univention-directory-manager-cli \
		python3-univention-directory-manager-rest \
		python3-univention-directory-manager-uvmm \
		python3-univention-directory-reports \
		python3-univention-heimdal \
		python3-univention-ipcalc \
		python3-univention-lib \
		python3-univention-license \
		python3-univention-management-console \
		python3-univention-pkgdb \
		python3-univention-radius \
		python3-univention-updater \
		python3-univention-virtual-machine-manager
}
