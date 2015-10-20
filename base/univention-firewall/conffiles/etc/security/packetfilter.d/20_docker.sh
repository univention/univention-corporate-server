#!/bin/sh
@%@UCRWARNING=# @%@
#
# Copyright 2015 Univention GmbH
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

nat_core_rules() {
	iptables -t nat -A PREROUTING -m addrtype --dst-type LOCAL -j DOCKER
	iptables -t nat -A OUTPUT ! -d 127.0.0.0/8 -m addrtype --dst-type LOCAL -j DOCKER
	iptables -t nat -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
	iptables -A FORWARD -o docker0 -j DOCKER
	iptables -A FORWARD -o docker0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
	iptables -A FORWARD -i docker0 ! -o docker0 -j ACCEPT
	iptables -A FORWARD -i docker0 -o docker0 -j ACCEPT
}

nat_container_rule() {
	IP=$(docker inspect --format='{{.NetworkSettings.IPAddress}}' $1)

	docker port $1 | sed -e 's#[/tcp>: -]\+# #g' | awk -v IP=$IP \
	'{ system("iptables -t nat -A DOCKER ! -i docker0 -p tcp -m tcp --dport "$3" -j DNAT --to-destination "IP":"$1";\
	iptables -t filter -A DOCKER -d "IP"/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport "$1" -j ACCEPT;\
	iptables -t nat -A POSTROUTING -s "IP"/32 -d "IP"/32 -p tcp -m tcp --dport "$1" -j MASQUERADE") }'
}

if [ -x /usr/bin/docker ] && [ -z $(ucr get docker/container/uuid) ] && /etc/init.d/docker status > /dev/null; then
	# this is a docker host
	nat_core_rules
	
	for CONT_ID in $(docker ps -q); do
		nat_container_rule $CONT_ID
	done
fi

