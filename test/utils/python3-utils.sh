#!/bin/bash
#
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

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
		python3-univention-appcenter \
		python3-univention-appcenter-dev \
		python3-univention-appcenter-docker \
		python3-univention-config-registry \
		python3-univention-connector-s4 \
		python3-univention-debug \
		python3-univention-directory-manager \
		python3-univention-directory-manager-cli \
		python3-univention-directory-manager-rest \
		python3-univention-directory-reports \
		python3-univention-heimdal \
		python3-univention-ipcalc \
		python3-univention-lib \
		python3-univention-license \
		python3-univention-management-console \
		python3-univention-pkgdb \
		python3-univention-radius \
		python3-univention-updater \

}
