#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Python VNC automate
#
# Copyright 2016 Univention GmbH
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


class Config(object):
	# All information that is relevant for an UCS-installation is stored
	# in here.
	# E.g.: IP address of the VM, DNS server, additional apps to install,
	# update after installation (bool), ...
	def __init__(
		self, ip, role='master', language='en', password="univention",
		update_ucs_after_install=True, dns_server_ip="",
		use_multiple_partitions=False, install_all_additional_components=False,
		ldap_base="dc=mydomain,dc=intranet"
	):
		self.ip = ip
		self.role = role
		# Use an ISO 639-1 language code here:
		self.language = language
		self.password = password
		self.update_ucs_after_install = update_ucs_after_install
		self.dns_server_ip = dns_server_ip
		self.use_multiple_partitions = use_multiple_partitions
		self.install_all_additional_components = install_all_additional_components
		self.ldap_base = ldap_base
