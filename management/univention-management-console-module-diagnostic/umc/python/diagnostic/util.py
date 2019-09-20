#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2017-2019 Univention GmbH
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

import ldap
import socket
import subprocess
import univention.uldap


def is_service_active(service, hostname=socket.gethostname()):
	lo = univention.uldap.getMachineConnection()
	raw_filter = '(&(univentionService=%s)(cn=%s))'
	filter_expr = ldap.filter.filter_format(raw_filter, (service, hostname))
	for (dn, _attr) in lo.search(filter_expr, attr=['cn']):
		if dn is not None:
			return True
	return False


def active_services(lo=None):
	if not lo:
		lo = univention.uldap.getMachineConnection()
	res = lo.search(base=lo.binddn, scope='base', attr=['univentionService'])
	if res:
		dn, attr = res[0]
		return attr.get('univentionService', [])
	return None


def run_with_output(cmd):
	output = list()
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	(stdout, stderr) = process.communicate()
	if stdout:
		output.append('\nSTDOUT:\n{}'.format(stdout))
	if stderr:
		output.append('\nSTDERR:\n{}'.format(stderr))
	return (process.returncode == 0, '\n'.join(output))
