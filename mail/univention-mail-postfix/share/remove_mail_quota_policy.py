#!/usr/bin/python2.7 -u
#
# Univention mail server
#  remove deprecated Cyrus mail quota policy objects
#
# Copyright 2018 Univention GmbH
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
import grp
import stat
import sys
import logging
from argparse import ArgumentParser
from ldap.filter import filter_format
from univention.admin import uldap
from univention.config_registry import ConfigRegistry
import univention.admin.modules


LOGFILE = '/var/log/univention/remove_mail_quota_policy.log'
DEBUG_LOG_FORMAT = "%(asctime)s %(levelname)-5s l.%(lineno)03d  %(message)s"

ucr = ConfigRegistry()
ucr.load()


def parse_cmdline():
	defaults = dict(
		dry_run=True,
		verbose=False
	)
	parser = ArgumentParser(
		description='Remove Cyrus mail quota policy references and objects from LDAP.',
		epilog='All output (incl. debugging statements) is written to logfile {!r}.'.format(LOGFILE)
	)
	parser.add_argument(
		'-n',
		'--dry-run',
		dest='dry_run',
		action='store_true',
		help="Dry run: don't actually commit changes to LDAP [default: %(default)s].")
	parser.add_argument(
		'-v',
		'--verbose',
		action='store_true',
		help='Enable debugging output on the console [default: %(default)s].')
	parser.set_defaults(**defaults)

	return parser.parse_args()


class QuotaRemoval(object):
	_module_cache = {}

	def __init__(self, args):
		self.dry_run = args.dry_run
		self.verbose = args.verbose
		self.logger = self.setup_logging()
		self.lo, _po = uldap.getAdminConnection()
		univention.admin.modules.update()
		self.logger.debug('Starting with dry_run=%r.', self.dry_run)

	def setup_logging(self):
		open(LOGFILE, "a").close()  # touch
		os.chown(LOGFILE, 0, grp.getgrnam('adm').gr_gid)
		os.chmod(LOGFILE, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)

		logger = logging.getLogger()
		logger.setLevel(logging.DEBUG)
		handler = logging.StreamHandler(stream=sys.stdout)
		handler.setLevel(logging.DEBUG if self.verbose else logging.INFO)
		logger.addHandler(handler)
		handler = logging.FileHandler(filename=LOGFILE)
		handler.setLevel(logging.DEBUG)
		handler.setFormatter(logging.Formatter(fmt=DEBUG_LOG_FORMAT))
		logger.addHandler(handler)
		return logger

	@classmethod
	def get_udm_module(cls, module_name):
		if module_name not in cls._module_cache:
			try:
				cls._module_cache[module_name] = univention.admin.modules.get(module_name)
			except (IndexError, KeyError):
				cls._module_cache[module_name] = None
		return cls._module_cache[module_name]

	def remove_policies(self):
		mail_quota_ldap_objs = self.lo.search('objectClass=univentionMailQuota')
		if not mail_quota_ldap_objs:
			self.logger.info('No Cyrus mail quota objects found in LDAP.')
			return
		self.logger.info('Found the following Cyrus mail quota objects in LDAP:')
		for dn, attr in mail_quota_ldap_objs:
			self.logger.info('* %s\n    Quota: %s\n    DN: %r', attr['cn'][0], attr['univentionMailQuotaMB'][0], dn)
			for ref_dn in self.lo.searchDn('univentionPolicyReference={}'.format(dn)):
				self.logger.info('    Referenced by %r', ref_dn)
		if self.dry_run:
			self.logger.info('Skipping quota objects removal (dry-run).')
			return
		for dn, attr in mail_quota_ldap_objs:
			for ref_dn, ref_attr in self.lo.search('univentionPolicyReference={}'.format(dn)):
				self.logger.info('Removing policy reference from %r', ref_dn)
				self.logger.debug('    univentionObjectType=%r', ref_attr.get('univentionObjectType'))
				try:
					module_name = ref_attr['univentionObjectType'][0]
					mod = self.get_udm_module(module_name)
				except (IndexError, KeyError):
					mod = None
				if mod:
					self.logger.debug('    using UDM module %r', mod)
					obj = mod.lookup(None, self.lo, 'uid=test1', base='cn=users,dc=uni,dc=dtr')[0]
					obj.policies.remove(dn)  # TODO: does this work?
					obj.modify()
				else:
					self.logger.debug('    got no UDM module, removing policy reference directly')
					pr = list(ref_attr['univentionPolicyReference'])
					pr.remove(dn)
					self.lo.modify(ref_dn, [('univentionPolicyReference', ref_attr['univentionPolicyReference'], pr)])





	def remove_udm_module(self):
		mod = self.get_udm_module('settings/udm_module')
		quota_udm_modules = mod.lookup(None, self.lo, 'cn=policies/mailquota')
		for qum in quota_udm_modules:
			self.logger.info('Found UDM module %r, removing it.', qum['name'])
			if self.dry_run:
				self.logger.info('Skipping UDM module removal (dry-run).')
			else:
				qum.remove()


if __name__ == '__main__':
	args = parse_cmdline()
	qr = QuotaRemoval(args)
	qr.remove_policies()
	qr.remove_udm_module()
