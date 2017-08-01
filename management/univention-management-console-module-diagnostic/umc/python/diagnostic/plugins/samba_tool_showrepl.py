#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2017 Univention GmbH
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

import os
import ldap
import socket

try:
	import samba.param
	import samba.credentials
	from samba.dcerpc import drsuapi
	from samba import drs_utils
except ImportError:
	SAMBA_AVAILABLE = False
else:
	SAMBA_AVAILABLE = True

import univention.uldap
from univention.management.console.modules.diagnostic import Warning

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check Samba replication status for errors')
description = _('No errors found.'),


def is_service_active(service):
	lo = univention.uldap.getMachineConnection()
	raw_filter = '(&(univentionService=%s)(cn=%s))'
	filter_expr = ldap.filter.filter_format(raw_filter, (service, socket.gethostname()))
	for (dn, _attr) in lo.search(filter_expr, attr=['cn']):
		if dn is not None:
			return True
	return False


class DRSUAPI(object):
	def __init__(self, dc=None):
		(self.load_param, self.credentials) = self.samba_credentials()
		self.server = dc or self.netcmd_dnsname(self.load_param)
		drs_tuple = drs_utils.drsuapi_connect(self.server, self.load_param, self.credentials)
		(self.drsuapi, self.handle, _bind_supported_extensions) = drs_tuple

	@staticmethod
	def netcmd_dnsname(lp):
		'''return the full DNS name of our own host. Used as a default
		for hostname when running status queries'''
		return lp.get('netbios name').lower() + "." + lp.get('realm').lower()

	@staticmethod
	def samba_credentials():
		load_param = samba.param.LoadParm()
		load_param.set("debug level", "0")
		if os.getenv("SMB_CONF_PATH") is not None:
			load_param.load(os.getenv("SMB_CONF_PATH"))
		else:
			load_param.load_default()
		credentials = samba.credentials.Credentials()
		credentials.guess(load_param)
		if not credentials.authentication_requested():
			credentials.set_machine_account(load_param)
		return (load_param, credentials)

	def _replica_info(self, info_type):
		req1 = drsuapi.DsReplicaGetInfoRequest1()
		req1.info_type = info_type
		(info_type, info) = self.drsuapi.DsReplicaGetInfo(self.handle, 1, req1)
		return (info_type, info)

	def neighbours(self):
		(info_type, info) = self._replica_info(drsuapi.DRSUAPI_DS_REPLICA_INFO_NEIGHBORS)
		for neighbour in info.array:
			yield neighbour

		(info_type, info) = self._replica_info(drsuapi.DRSUAPI_DS_REPLICA_INFO_REPSTO)
		for neighbour in info.array:
			yield neighbour

	def replication_problems(self):
		for neighbour in self.neighbours():
			(ecode, estring) = neighbour.result_last_attempt
			if ecode != 0:
				yield ReplicationProblem(neighbour)


class ReplicationProblem(Exception):
	def __init__(self, neighbour):
		super(ReplicationProblem, self).__init__(neighbour)
		self.neighbour = neighbour

	def __str__(self):
		msg = _('In {nc!r}: error during DRS replication from {source}.')
		source = self._parse_ntds_dn(self.neighbour.source_dsa_obj_dn)
		return msg.format(nc=self.neighbour.naming_context_dn.encode(),
			source=source)

	@staticmethod
	def _parse_ntds_dn(dn):
		exploded = ldap.dn.str2dn(dn)
		if len(exploded) >= 5:
			(first, second, third, fourth, fifth) = exploded[:5]
			valid_ntds_dn = all((first[0][1] == 'NTDS Settings',
				third[0][1] == 'Servers', fifth[0][1] == 'Sites'))
			if valid_ntds_dn:
				return '{}/{}'.format(fourth[0][1], second[0][1])
		return dn


def run(_umc_instance):
	if not is_service_active('Samba 4') or not SAMBA_AVAILABLE:
		return

	drs = DRSUAPI()
	problems = list(drs.replication_problems())
	if problems:
		ed = [_('`samba-tool drs showrepl` returned a problem with the replication.')]
		ed.extend(str(error) for error in problems)
		raise Warning(description='\n'.join(ed))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
