#!/usr/bin/python2.7
#
# Univention Management Console
#  Analyse connector rejects
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

import uuid
import sys

import univention
import univention.s4connector
import univention.s4connector.s4

import univention.config_registry

from univention.management.console.config import ucr
from univention.management.console.base import Base
from univention.management.console.modules.decorators import simple_response, sanitize
from univention.management.console.modules.sanitizers import ChoicesSanitizer, StringSanitizer

from univention.lib.i18n import Translation

sys.path = ['/etc/univention/connector/s4/'] + sys.path
import mapping

_ = Translation('univention-management-console-module-connector-rejects').translate


class Instance(Base):

	def query(self, request):
		s4 = self.new_s4()
		response = []

		for filename, dn in s4.list_rejected_ucs():
			s4_dn = univention.s4connector.s4.encode_attrib(s4.get_dn_by_ucs(dn))
			ucs_dn = univention.s4connector.s4.encode_attrib(dn)
			response.append({
				'id': str(uuid.uuid4()),
				'rejected': 'UCS',
				'ucs_dn': ucs_dn,
				's4_dn': s4_dn if s4_dn else _('not found'),
				'filename': filename
			})

		for usn, dn in s4.list_rejected():
			ucs_dn = univention.s4connector.s4.encode_attrib(s4.get_dn_by_con(dn))
			s4_dn = univention.s4connector.s4.encode_attrib(dn)
			response.append({
				'id': str(uuid.uuid4()),
				'rejected': 'S4',
				's4_dn': s4_dn,
				'ucs_dn': ucs_dn if ucs_dn else _('not found')
			})

		self.finished(request.id, response)

	@sanitize(
		rejected=ChoicesSanitizer(['UCS', 'S4'], required=True),
		ucs_dn=StringSanitizer(required=True),
		s4_dn=StringSanitizer(required=True))
	@simple_response
	def remove(self, rejected, ucs_dn, s4_dn):
		s4 = self.new_s4()
		if rejected == 'UCS':
			filename = self.get_rejected_ucs_filename(s4, ucs_dn)
			s4.remove_rejected_ucs(filename)
		elif rejected == 'S4':
			usn = self.get_rejected_s4_usn(s4, s4_dn)
			s4.remove_rejected(usn)

	def get_rejected_ucs_filename(self, s4, ucs_dn):
		for filename, dn in s4.list_rejected_ucs():
			if univention.s4connector.s4.encode_attrib(ucs_dn) == dn:
				return filename

	def get_rejected_s4_usn(self, s4, s4_dn):
		for usn, dn in s4.list_rejected():
			if univention.s4connector.s4.encode_attrib(s4_dn) == dn:
				return usn

	def new_s4(self):
		s4_ldap_bindpw = None
		if ucr.get('connector/s4/ldap/bindpw'):
			with open(ucr['connector/s4/ldap/bindpw']) as fd:
				s4_ldap_bindpw = fd.read().strip()

		s4 = univention.s4connector.s4.s4(
			"connector",
			mapping.s4_mapping,
			ucr,
			ucr['connector/s4/ldap/host'],
			ucr['connector/s4/ldap/port'],
			ucr['connector/s4/ldap/base'],
			ucr.get('connector/s4/ldap/binddn'),
			s4_ldap_bindpw,
			ucr['connector/s4/ldap/certificate'],
			ucr['connector/s4/listener/dir'],
			False
		)
		return s4
