# Univention Samba4 Shell Library
#
# Copyright 2012-2019 Univention GmbH
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
# Wait for RID pool replication
# univention_samba4_wait_for_rid_set
#
univention_samba4_wait_for_rid_set() {
	local max_attempts=180

	echo -n "Waiting for RID Pool replication: "
	local rIDSetReferences
	local attempt
	attempt=0
	while [ -z "$rIDSetReferences" ] && [ "$attempt" -lt "$max_attempts" ]; do
		if [ "$attempt" != 0 ]; then
			sleep 1
			echo -n "."
		fi
		attempt=$(($attempt + 1))
		rIDSetReferences=$(ldbsearch -H /var/lib/samba/private/sam.ldb "(sAMAccountName=$hostname\$)" rIDSetReferences \
			| ldapsearch-wrapper | sed -n 's/^rIDSetReferences: //p')
	done

	if [ -z "$rIDSetReferences" ]; then
		echo
		echo "Error no rIDSetReferences replicated for $hostname"
		exit 1
	fi

	local rIDAllocationPool
	max_attempts=60
	attempt=0
	while [ -z "$rIDAllocationPool" ] && [ "$attempt" -lt "$max_attempts" ]; do
		if [ "$attempt" != 0 ]; then
			sleep 1
			echo -n "."
		fi
		attempt=$(($attempt + 1))
		rIDAllocationPool=$(ldbsearch -H /var/lib/samba/private/sam.ldb -b "$rIDSetReferences" rIDAllocationPool \
			| ldapsearch-wrapper | sed -n 's/^rIDAllocationPool: //p')
	done

	if [ -z "$rIDAllocationPool" ]; then
		echo
		echo "Error no rIDAllocationPool replicated for $hostname"
		exit 1
	fi
	echo "done."
}

