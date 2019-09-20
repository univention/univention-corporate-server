#!/bin/bash
#
# Copyright 2007-2019 Univention GmbH
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
#
# Generate reports to check implementation is still working
#
set -o errexit
set -o pipefail

undo="$(mktemp)"
rmac () { printf "%02x:%02x:%02x:%02x:%02x:%02x\n" $((RANDOM % 256)) $((RANDOM % 256)) $((RANDOM % 256)) $((RANDOM % 256)) $((RANDOM % 256)) $((RANDOM % 256)); }
rip () { printf "%d.%d.%d.%d\n" $((RANDOM % 256)) $((RANDOM % 256)) $((RANDOM % 256)) $((RANDOM % 256)); }
udm () { univention-directory-manager "$@"; }
udm_c () { # create object and store undo operation
	exec 3>&1
	univention-directory-manager "$@" | tee /dev/fd/3 | sed -ne "s|^Object created: \(.*\)|univention-directory-manager \"$1\" remove --dn \"\1\"|p" >>"$undo"
	exec 3>&-
}
cleanup () { # undo object creation
	set +e
	"$SHELL" "$undo"
	rm -rf "$undo"
	rm -f "$TMPDIR"/univention-directory-reports-*
}
trap cleanup EXIT

for i in $(seq 3)
do
	udm_c groups/group create --set name="group$RANDOM" --set description="desc$RANDOM"
	udm_c users/user create --set username="user$RANDOM" --set lastname="first$RANDOM" --set firstname="first$RANDOM" --set password=univention
	for module in $(udm modules | sed -e '/computers\//!d' -e '/computers\/computer/d' -e 's/ //g')
	do
		m="${module#*/}"
		udm_c "$module" create --set name="${m}$RANDOM" --set description="desc$RANDOM" --set mac="$(rmac)" --set ip="$(rip)" --set password=univention
	done
done

IFS=$'\n'
for module in users/user groups/group computers/computer
do
	for report in "Standard Report" "Standard CSV Report"
	do
		univention-directory-reports -m "$module" -r "$report" $(udm "$module" list | sed -ne 's/^DN: //p')
	done
done

echo "Success."
