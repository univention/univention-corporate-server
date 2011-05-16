# Univention Common Shell Library
#
# Copyright 2011 Univention GmbH
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


#
# creates an empty file with given owner/group and permissions
# create_logfile <filename> <owner> <permissions>
# e.g. create_logfile /tmp/foo.log root:adm 0750
#
create_logfile () {
    touch "$1"
    chown "$2" "$1"
    chmod "$3" "$1"
}

#
# creates an empty file with given owner/group and permissions if file does not exist
# create_logfile_if_missing <filename> <owner> <permissions>
# e.g. create_logfile_if_missing /tmp/foo.log root:adm 0750
#
create_logfile_if_missing () {
    if [ ! -e "$1" ] ; then
		create_logfile "$@"
    fi
}

#
# calls the given joinscript
# call_joinscript <joinscript>
# e.g. call_joinscript 99my-custom-joinscript.inst
# e.g. call_joinscript 99my-custom-joinscript.inst --binddn ... --bindpwd ...
#
call_joinscript () {
	local joinscript
	joinscript="/usr/lib/univention-install/$1"
	if [ -x "$joinscript" ] ; then
		shift
		if [ "$(ucr get server/role)" = "domaincontroller_master" ] ; then
			"$joinscript" "$@"
		fi
	fi
}

#
# stops any currently running UDM CLI server
#
stop_udm_cli_server () {
    pkill -f "/usr/bin/python.* /usr/share/univention-directory-manager-tools/univention-cli-server"
}

#
# if is_domain_controller; then
#         ... do domain controller stuff ...
# fi
#
is_domain_controller () {
	[[ "$(ucr get server/role)" == domaincontroller_* ]]
}
