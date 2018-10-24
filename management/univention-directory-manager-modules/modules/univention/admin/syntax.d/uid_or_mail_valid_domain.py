# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  syntax definition
#
# Copyright 2004-2018 Univention GmbH
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

"""
Bug #40609: prevent user from using forged sender address

move the class `uidOrEmailAddressValidDomain` to syntax.py with UCS 4.4 and delete this file.
"""

from univention.admin.syntax import _, simple, emailAddressValidDomain, uid
from univention.admin.uexceptions import valueError


class uidOrEmailAddressValidDomain(simple):
	"""Allow both a username or a email address from one of the hosted domains."""
	name = 'uidOrEmailAddressValidDomain'

	@classmethod
	def parse(cls, text):
		bad_username_exc = None
		try:
			return uid.parse(text)
		except valueError as bad_username_exc:
			pass
		try:
			return emailAddressValidDomain.parse(text)
		except valueError as bad_email_exc:
			if bad_username_exc:
				raise valueError(_(
					'Value is neither a valid username (%(bad_username_exc)s) nor an email address of a hosted domain '
					'(%(bad_email_exc)s).') % {'bad_username_exc': bad_username_exc, 'bad_email_exc': bad_email_exc})
			else:
				raise
