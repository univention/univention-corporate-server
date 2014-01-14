#!/bin/bash
#
# Univention System Setup
#  setup help update script
#
# Copyright 2004-2014 Univention GmbH
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

DEST_DIR=/usr/share/univention-management-console-frontend/js/umc/modules/setup
DEST_NAME=help.html
DEFAULT_NAME=help_default.html
UCR_NAME=system/setup/boot/help
LANGUAGES=(de en)

IFS=:
vals=($(univention-config-registry get $UCR_NAME))
IFS=$'\n\t '

function default_links() {
	# set back the default help pages
	echo "Setting up fallback files..." 1>&2
	for lang in ${LANGUAGES[@]}; do
		ln -sf "$DEST_DIR/$lang/$DEFAULT_NAME" "$DEST_DIR/$lang/$DEST_NAME"
	done
}

function error() {
	echo -e "ERROR: $@" 1>&2
	default_links
	exit 1
}

if [ ${#vals[@]} -lt 2 ]; then
	if [ ${#vals[@]} -eq 0 ]; then
		echo "The UCR variable $UCR_NAME is unset" 1>&2
		default_links
		exit 0
	fi
	error "The UCR variable $UCR_NAME has an invalid format, should be '<dir>:<filename>'."
fi

dir="${vals[0]}"
file="${vals[1]}"

[ ! -d "$dir" ] && error "The directory cannot be accessed: $dir"

if [ -f "$dir/$file" ]; then
	# simple case, no i18n
	for lang in ${LANGUAGES[@]}; do
		ln -sf "$dir/$file" "$DEST_DIR/$lang/$DEST_NAME"
	done
else
	# try to find localized files
	for lang in ${LANGUAGES[@]}; do
		path="$dir/$lang/$file"
		[ ! -f "$path" ] && error "The specified path cannot be found:\n  directory: $dir\n  file: $file"
		ln -sf "$dir/$lang/$file" "$DEST_DIR/$lang/$DEST_NAME"
	done
fi

