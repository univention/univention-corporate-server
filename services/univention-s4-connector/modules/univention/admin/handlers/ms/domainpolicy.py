# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  UDM module for Domain Policies
#
# Copyright 2019-2022 Univention GmbH
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

from univention.admin.layout import Tab, Group

import univention.admin.syntax
import univention.admin.handlers
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.ms')
_ = translation.translate

module = 'ms/domainpolicy'
operations = ['add', 'edit', 'remove', 'search', 'move', 'subtree_move']
childs = True
short_description = _('MS Domain Policy')
long_description = ''
options = {
	'default': univention.admin.option(
		short_description='',
		default=True,
		objectClasses=['domainPolicy', 'leaf', 'top']
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		required=True,
		identifies=True,
	),
	'qualityOfService': univention.admin.property(
		short_description=_('Qualityofservice'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'pwdProperties': univention.admin.property(
		short_description=_('Pwdproperties'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'pwdHistoryLength': univention.admin.property(
		short_description=_('Pwdhistorylength'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'publicKeyPolicy': univention.admin.property(
		short_description=_('Publickeypolicy'),
		long_description='',
		syntax=univention.admin.syntax.TextArea,
	),
	'proxyLifetime': univention.admin.property(
		short_description=_('Proxylifetime'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'minTicketAge': univention.admin.property(
		short_description=_('Minticketage'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'minPwdLength': univention.admin.property(
		short_description=_('Minpwdlength'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'minPwdAge': univention.admin.property(
		short_description=_('Minpwdage'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'maxTicketAge': univention.admin.property(
		short_description=_('Maxticketage'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'maxRenewAge': univention.admin.property(
		short_description=_('Maxrenewage'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'maxPwdAge': univention.admin.property(
		short_description=_('Maxpwdage'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'managedBy': univention.admin.property(
		short_description=_('Managedby'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'lockoutThreshold': univention.admin.property(
		short_description=_('Lockoutthreshold'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'lockoutDuration': univention.admin.property(
		short_description=_('Lockoutduration'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'lockOutObservationWindow': univention.admin.property(
		short_description=_('Lockoutobservationwindow'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'ipsecPolicyReference': univention.admin.property(
		short_description=_('Ipsecpolicyreference'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'forceLogoff': univention.admin.property(
		short_description=_('Forcelogoff'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'eFSPolicy': univention.admin.property(
		short_description=_('Efspolicy'),
		long_description='',
		syntax=univention.admin.syntax.TextArea,
		multivalue=True,
	),
	'domainWidePolicy': univention.admin.property(
		short_description=_('Domainwidepolicy'),
		long_description='',
		syntax=univention.admin.syntax.TextArea,
		multivalue=True,
	),
	'domainPolicyReference': univention.admin.property(
		short_description=_('Domainpolicyreference'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'domainCAs': univention.admin.property(
		short_description=_('Domaincas'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
	),
	'defaultLocalPolicyObject': univention.admin.property(
		short_description=_('Defaultlocalpolicyobject'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'authenticationOptions': univention.admin.property(
		short_description=_('Authenticationoptions'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General'), layout=[
			'name',
			'qualityOfService',
			'pwdProperties',
			'pwdHistoryLength',
			'publicKeyPolicy',
			'proxyLifetime',
			'minTicketAge',
			'minPwdLength',
			'minPwdAge',
			'maxTicketAge',
			'maxRenewAge',
			'maxPwdAge',
			'managedBy',
			'lockoutThreshold',
			'lockoutDuration',
			'lockOutObservationWindow',
			'ipsecPolicyReference',
			'forceLogoff',
			'eFSPolicy',
			'domainWidePolicy',
			'domainPolicyReference',
			'domainCAs',
			'defaultLocalPolicyObject',
			'authenticationOptions'
		]),
	]),
]


def multivalueMapBase64(data):
	if data:
		return [univention.admin.mapping.mapBase64(d) for d in data]
	return []


def multivalueUnmapBase64(data):
	if data:
		return [univention.admin.mapping.unmapBase64(data)]  # stupid broken function in UDM
	return []


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('qualityOfService', 'qualityOfService', None, univention.admin.mapping.ListToString)
mapping.register('pwdProperties', 'pwdProperties', None, univention.admin.mapping.ListToString)
mapping.register('pwdHistoryLength', 'pwdHistoryLength', None, univention.admin.mapping.ListToString)
mapping.register('publicKeyPolicy', 'publicKeyPolicy', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('proxyLifetime', 'proxyLifetime', None, univention.admin.mapping.ListToString)
mapping.register('minTicketAge', 'minTicketAge', None, univention.admin.mapping.ListToString)
mapping.register('minPwdLength', 'minPwdLength', None, univention.admin.mapping.ListToString)
mapping.register('minPwdAge', 'minPwdAge', None, univention.admin.mapping.ListToString)
mapping.register('maxTicketAge', 'maxTicketAge', None, univention.admin.mapping.ListToString)
mapping.register('maxRenewAge', 'maxRenewAge', None, univention.admin.mapping.ListToString)
mapping.register('maxPwdAge', 'maxPwdAge', None, univention.admin.mapping.ListToString)
mapping.register('managedBy', 'managedBy', None, univention.admin.mapping.ListToString)
mapping.register('lockoutThreshold', 'lockoutThreshold', None, univention.admin.mapping.ListToString)
mapping.register('lockoutDuration', 'lockoutDuration', None, univention.admin.mapping.ListToString)
mapping.register('lockOutObservationWindow', 'lockOutObservationWindow', None, univention.admin.mapping.ListToString)
mapping.register('ipsecPolicyReference', 'ipsecPolicyReference', None, univention.admin.mapping.ListToString)
mapping.register('forceLogoff', 'forceLogoff', None, univention.admin.mapping.ListToString)
mapping.register('eFSPolicy', 'eFSPolicy', multivalueMapBase64, multivalueUnmapBase64)
mapping.register('domainWidePolicy', 'domainWidePolicy', multivalueMapBase64, multivalueUnmapBase64)
mapping.register('domainPolicyReference', 'domainPolicyReference', None, univention.admin.mapping.ListToString)
mapping.register('domainCAs', 'domainCAs')
mapping.register('defaultLocalPolicyObject', 'defaultLocalPolicyObject', None, univention.admin.mapping.ListToString)
mapping.register('authenticationOptions', 'authenticationOptions', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_pre_modify(self):
		if self.hasChanged('name'):
			self.move(self._ldap_dn())


identify = object.identify
lookup = object.lookup
