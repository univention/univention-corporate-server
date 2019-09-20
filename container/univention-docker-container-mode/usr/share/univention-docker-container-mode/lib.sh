#!/bin/bash
#
# Univention Appliance Docker Container
#  lib
#
# Copyright 2015-2019 Univention GmbH
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

ARGS=("$@")
getarg() {
	local found=0
	for arg in "${ARGS[@]}"; do
		if [ "$found" -eq 1 ]; then
			echo "$arg"
			break
		fi
		if [ "$arg" = "$1" ]; then
			found=1
		fi
	done
}

APP="$(getarg "--app")"
APP_VERSION="$(getarg "--app-version")"
APP_ARG="$APP"
if [ -n "$APP_VERSION" ]; then
	APP_ARG="$APP=$APP_VERSION"
fi
ERROR_FILE=$(getarg "--error-file")

error_msg() {
	if [ -n "$ERROR_FILE" ]; then
		echo "$@" | tee -a "$ERROR_FILE" >&2
	else
		echo "$@" >&2
	fi
}

die() {
	error_msg "$@"
	exit 1
}

