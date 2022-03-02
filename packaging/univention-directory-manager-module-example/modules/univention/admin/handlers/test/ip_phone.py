#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2004-2022 Univention GmbH
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

import re

import univention.admin.handlers  # Contains 'simpleLdap', the base class for 'object' below
import univention.admin.syntax  # Returns standard syntax definitions for the UDM 'property_descriptions' below
import univention.admin.localization
from univention.admin.layout import Tab

# For the integration of translation catalogs for different languages
translation = univention.admin.localization.translation('univention.admin.handlers.test')
_ = translation.translate


# <Syntax definitions>
class SynVoIP_Protocols(univention.admin.syntax.select):

	"""This class defines a new syntax for a selection list of VoIP protocols"""

	# The text to be written in front of the selection list in the Web frontend.
	name = _('VoIP_Protocol')

	# the list of selection options: each of the elements contains a unique key and the text to be displayed
	choices = [('sip', _('SIP')), ('h323', _('H.323')), ('skype', _('Skype'))]


class SynVoIP_Address(univention.admin.syntax.simple):

	"""This class serves as syntax for a VoIP address. The structure is similar to an e-mail address,
	but may contain a scheme followed by a ":" as a prefix.
	Valid schemes are: sip, h323 and skype"""

	name = _('VoIP_Address')
	min_length = 4
	max_length = 256
	_re = re.compile('((^(sip|h323|skype):)?([a-zA-Z])[a-zA-Z0-9._-]+)@[a-zA-Z0-9._-]+$')

	def parse(self, text):
		if self._re.match(text) is not None:
			return text
		raise univention.admin.uexceptions.valueError(_('Not a valid VoIP Address'))


# </Syntax definitions>

# <UDM module API>

# internal name of the module, also used in the command line client
module = 'test/ip_phone'
# This object cannot contain any subobjects
childs = False
# a descriptive name for the web frontend
short_description = _('IP-Phone')
# a detailed description
long_description = _('An example module for the Univention Directory Manager')
# the LDAP operations that can be performed on this object
operations = ['add', 'edit', 'remove', 'search', 'move', 'copy']


# To create your own wizard, which appears in the UDM Web on the left in the navigation bar:
# usewizard = 1
# wizardmenustring = "VoIP"
# wizarddescription =  _("Add, delete and search VoIP objects"
# wizardoperations = { 'add' : [_("add"), _("Add an VoIP object")],
# 'find' : [_("Search"), _("Search VoIP objects"]) }
# wizardpath = "univentionUsersObject"

# <UDM module options>
# List of options for this module or for the object type handled
options = {
	# optional properties of an object are defined by 'options'
	# the 'default' option contains the mandatory object classes
	'default': univention.admin.option(
		short_description=short_description,
		default=True,
		objectClasses=['top', 'testPhone'],
	),
	'redirection': univention.admin.option(
		short_description=_('Call redirect option'),
		default=True,
		editable=True,
		objectClasses=['testPhoneCallRedirect'],
	),
}

# <UDM module properties>

# List of properties for this module
property_descriptions = {
	# the unique name of an IP telephone
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description=_('ID of the IP-phone'),
		syntax=univention.admin.syntax.hostName,  # Property must match the syntax of a computer name, defined in syntax.py
		required=True,  # Property must be specified
		identifies=True,  # Property must be unique
	),
	'active': univention.admin.property(
		short_description=_('active'),
		long_description=_('The IP-phone can be deactivated'),
		syntax=univention.admin.syntax.TrueFalseUp,  # Definition in syntax.py, compatible to LDAP Boolean syntax
		default='TRUE',  # Property is enabled by default
	),
	'protocol': univention.admin.property(
		short_description=_('Protocol'),
		long_description=_('Supported VoIP protocols'),
		syntax=SynVoIP_Protocols,  # uses the self-defined selection list as syntax
		default='sip',  # the entry 'sip' is preselected
	),
	'ip': univention.admin.property(
		short_description=_('IP-Address'),
		long_description=_('IP-Address of the IP-phone'),
		syntax=univention.admin.syntax.ipAddress,  # must correspond to the syntax of an IP address (version 4)
		required=True,
	),
	'priuser': univention.admin.property(
		short_description=_('Primary User'),
		long_description=_('The primary user of this IP-phone'),
		syntax=SynVoIP_Address,  # must correspond to the syntax of a VoIP address
		required=True,
	),
	'users': univention.admin.property(
		short_description=_('Additional Users'),
		long_description=_('Users, that may register with this phone'),
		syntax=SynVoIP_Address,  # each entry must match the syntax of a VoIP address
		multivalue=True,  # This is a list of addresses
	),
	'redirect_user': univention.admin.property(
		short_description=_('Redirection User'),
		long_description=_('Address for call redirection'),
		syntax=SynVoIP_Address,
		options=['redirection'],  # Property is only shown if the specified option is set
	),
}

# <UDM module layout>

# The layout defines the arrangement of the fields in the web frontend.
# Each 'Tab' corresponds to a tab in the web interface:
# * The first parameter is the name of the tab and the second parameter is a description of the setting options on this tab.
# * The following list defines the arrangement of the individual property fields.
# * 'advanced=True' moves/combines the tab to the "advanced settings" tab.
layout = [
	Tab(_('General'), _('Basic Settings'), layout=[
		["name", "active"],
		["ip", "protocol"],
		["priuser"],
	]),
	Tab(_('Advanced'), _('Advanced Settings'), layout=[
		["users"],
	], advanced=True),
	Tab(_('Redirect'), _('Redirect Option'), layout=[
		["redirect_user"],
	], advanced=True),
]

# <Mapping of UDM properties to LDAP attribute>

# The mapping object defines the mapping of the properties of the UDM module/object to attributes of an LDAP object.
mapping = univention.admin.mapping.mapping()
# Binds the 'name' property to the RDN, uses predefined mapping function from mapping.py:
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
# mapping.register of the 'active' property to the LDAP attribute 'testPhoneActive':
mapping.register('active', 'testPhoneActive', None, univention.admin.mapping.ListToString)
# Binding of the 'protocol' property to the LDAP attribute 'testPhoneProtocol':
mapping.register('protocol', 'testPhoneProtocol', None, univention.admin.mapping.ListToString)
mapping.register('ip', 'testPhoneIP', None, univention.admin.mapping.ListToString)
mapping.register('priuser', 'testPhonePrimaryUser', None, univention.admin.mapping.ListToString)
# Binds the 'users' property directly to the LDAP attribute testPhoneUsers without further translation:
mapping.register('users', 'testPhoneUsers')
mapping.register('redirect_user', 'testPhoneRedirectUser', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):

	"""This object assists the Univention Directory Manager in LDAP operations that relate to this module.
	The base class univention.admin.handlers.simpleLdap implements the complete communication via LDAP,
    so that only the adjustments for this special LDAP object have to be implemented here.
	For this purpose, the base class offers one function each to make adjustments before and after an LDAP
    operation. In this example class the prototypes of all these functions are defined to give an overview
    of the possibilities."""

	# take the module name as attributes of the class (defined above as module='test/ip-phone')
	module = module

	def open(self):
		"""Open the LDAP object"""

		super(object, self).open()
		# In this method, the properties of the object in self.info can be pre-initialized dynamically.
		# The dictionary self.info can be addressed indirectly, that is, for example, using self['active'] = 1
		# 'self' behaves like a special dictionary
		# It checks operations against the 'property_descriptions' and also returns default values. A modification of e.g. self['name'] would throw an exception univention.admin.uexceptions.valueMayNotChange.

		# The 'save' method saves the current properties of the opened object as "old state" in self.oldinfo and self.oldpolicies.
		# These will later be used for comparison with the updated properties in self.info.
		self.save()

	def _ldap_pre_create(self):
		"""Called before the LDAP object is created."""
		return super(object, self)._ldap_pre_create()

	def _ldap_post_create(self):
		"""Called after the object has been created."""
		return super(object, self)._ldap_post_create()

	def _ldap_pre_modify(self):
		"""Called before the object is modified."""
		return super(object, self)._ldap_pre_modify()

	def _ldap_post_modify(self):
		"""Called after the object has been modified."""
		return super(object, self)._ldap_post_modify()

	def _ldap_pre_remove(self):
		"""Called before the object is deleted."""
		return super(object, self)._ldap_pre_remove()

	def _ldap_post_remove(self):
		"""Called after the object has been deleted."""
		return super(object, self)._ldap_post_remove()

	def _ldap_modlist(self):
		"""This function can be defined. The inherited method with the same name from 'simpleLdap'
		creates an LDAP modlist from the difference between self.oldinfo and self.info."""

		ml = super(object, self)._ldap_modlist()
		# here further adjustments of the modlist are possible
		return ml


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
