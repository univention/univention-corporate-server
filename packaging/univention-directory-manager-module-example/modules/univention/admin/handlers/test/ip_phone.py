#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2004-2021 Univention GmbH
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
import univention.admin.handlers  # Enthält simpleLdap, die Basisklasse für 'object' unten
import univention.admin.syntax  # Liefert standard Syntax-Definitionen für die UDM 'property_descriptions' unten
import univention.admin.localization
from univention.admin.layout import Tab

# Für das Einbinden von Übersetzungskatalogen für verschiedene Sprachen
translation = univention.admin.localization.translation('univention.admin.handlers.test')
_ = translation.translate


# <Syntax definitions>
class SynVoIP_Protocols(univention.admin.syntax.select):

	"""Diese Klasse definiert einen neue Syntax für eine Auswahlliste von VoIP-Protokollen"""
	# der Text, der in dem Web-Frontend vor die Auswahlliste geschrieben werden soll
	name = _('VoIP_Protocol')

	# die Liste der Auswahlmöglichkeiten: Jedes der Elemente enthält einen eindeutigen Schlüssel
	# und den anzuzeigenden Text
	choices = [('sip', 'SIP'), ('h323', 'H.323'), ('skype', 'Skype')]


class SynVoIP_Address(univention.admin.syntax.simple):

	"""Diese Klasse dient als Syntax für VoIP Adresse. Der Aufbau ist einer E-Mail Adresse ähnlich,
	kann aber als Präfix noch ein Schema gefolgt von einem ':' enthalten.
	Valide Schemta sind: sip, h323 und skype"""

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

# interner Name des Moduls, verwendet auch im Kommandozeilen-Client
module = 'test/ip_phone'
# dieses Objekt kann keine Unterobjekte enthalten
childs = False
# ein sprechender Name für das Web-Frontend
short_description = _('IP-Phone')
# eine ausführliche Beschreibung
long_description = _('An example module for the Univention Directory Manager')
# die LDAP Operationen, die auf diesem Objekt ausgeführt werden können
operations = ['add', 'edit', 'remove', 'search', 'move']


# Um einen eigenen Wizard zu erstellen, der im UDM-Web links in der Navigationsleiste erscheint:
# usewizard = 1
# wizardmenustring = "VoIP"
# wizarddescription =  _("Add, delete and search VoIP objects"
# wizardoperations = { 'add' : [_("add"), _("Add an VoIP object")],
# 'find' : [_("Search"), _("Search VoIP objects"]) }
# wizardpath = "univentionUsersObject"

# <UDM module options>
# Liste der Optionen für dieses Modul, bzw. für den behandelten Objekttyp
options = {
	# durch 'options' werden optionale Eigenschaften eines Objekts definiert
	# die 'default' Option enthält die Pflicht-Objektklassen
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
	)
}

# <UDM module properties>

# Liste der Eigenschaften für dieses Modul
property_descriptions = {
	# der eindeutige Name eines IP-Telefons
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description=_('ID of the IP-phone'),
		syntax=univention.admin.syntax.hostName,  # Eigenschaft muss der Syntax eines Rechnernamens entsprechen, Def. in syntax.py
		required=True,  # Eigenschaft muss angegeben werden
		identifies=True,  # Eigenschaft muss eindeutig sein
	),
	'active': univention.admin.property(
		short_description=_('active'),
		long_description=_('The IP-phone can be deactivated'),
		syntax=univention.admin.syntax.TrueFalseUp,  # Definition in syntax.py, kompatibel zur LDAP Boolean Syntax
		default='TRUE',  # Eigenschaft ist standardmäßig aktiviert
	),
	'protocol': univention.admin.property(
		short_description=_('Protocol'),
		long_description=_('Supported VoIP protocols'),
		syntax=SynVoIP_Protocols,  # nutzt die selbst definierte Auswahlliste als Syntax
		default='sip',  # der Eintrag 'sip' ist vorausgewählt
	),
	'ip': univention.admin.property(
		short_description=_('IP-Address'),
		long_description=_('IP-Address of the IP-phone'),
		syntax=univention.admin.syntax.ipAddress,  # muss der Syntax einer IP (Version 4) Adresse entsprechen
		required=True,
	),
	'priuser': univention.admin.property(
		short_description=_('Primary User'),
		long_description=_('The primary user of this IP-phone'),
		syntax=SynVoIP_Address,  # muss der Syntax einer VoIP Adresse entsprechen
		required=True,
	),
	'users': univention.admin.property(
		short_description=_('Additional Users'),
		long_description=_('Users, that may register with this phone'),
		syntax=SynVoIP_Address,  # jeder Eintrag muss der Syntax einer VoIP Adresse entsprechen
		multivalue=True,  # Dies ist eine Liste von Adressen
	),
	'redirect_user': univention.admin.property(
		short_description=_('Redirection User'),
		long_description=_('Address for call redirection'),
		syntax=SynVoIP_Address,
		options=['redirection'],  # Ist nur da, wenn die Option gesetzt ist
	),
}

# <UDM module layout>

# Das 'layout' definiert die Anordung der Felder im Web-Frontend.
# Jeder 'Tab' entspricht einem Reiter:
# * Der erste Parameter ist der Name des Reiters und der zweite Parameter
# ist eine Beschreibung der Einstellungsmöglich für diesen Reiter
# * Die folgende Liste definiert die Anordnung der einzelnen Eigenschaftsfelder.
# * Per advanced=True wird der Reiter nur angezeigt, wenn das Anzeigen der
# erweiterten Einstellungen aktiviert ist.
layout = [
	Tab(_('General'), _('Basic Settings'), [
		["name", "active"],
		["ip", "protocol"],
		["priuser"],
	]),
	Tab(_('Advanced'), _('Advanced Settings'), [
		["users"],
	], advanced=True),
	Tab(_('Redirect'), _('Redirect Option'), [
		["redirect_user"],
	], advanced=True),
]

# <Mapping of UDM properties to LDAP attribute>

# Das 'mapping' Objekt definiert die Abbildung der Eigenschaften des UDM-Moduls/Objekts auf Attribute eines LDAP-Objektes
mapping = univention.admin.mapping.mapping()
# Abbindung der Eigenschaft 'name' auf den RDN, nutzt vordefinierte Mapping-Funktion aus mapping.py:
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
# mapping.register der Eigenschaft 'active' auf das LDAP-Attribut testPhoneActive:
mapping.register('active', 'testPhoneActive', None, univention.admin.mapping.ListToString)
# Abbindung der Eigenschaft 'protocol' auf das LDAP-Attribut testPhoneProtocol:
mapping.register('protocol', 'testPhoneProtocol', None, univention.admin.mapping.ListToString)
mapping.register('ip', 'testPhoneIP', None, univention.admin.mapping.ListToString)
mapping.register('priuser', 'testPhonePrimaryUser', None, univention.admin.mapping.ListToString)
# Abbindung der Eigenschaft 'users' ohne weitere Übersetzung direkt auf das LDAP-Attribut testPhoneUsers:
mapping.register('users', 'testPhoneUsers')
mapping.register('redirect_user', 'testPhoneRedirectUser', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):

	"""Dieses Objekt unterstützt den Univention Directory Manager bei LDAP-Operationen,
	die sich auf dieses Modul beziehen.
	Die Basisklasse univention.admin.handlers.simpleLdap implementiert die komplette Kommunikation über LDAP,
	so dass hier nur die Anpassungen für dieses spezielle LDAP-Objekt implementiert werden müssen.
	Dafür bietet die Basisklasse jeweils eine Funktionen um vor und nach einer LDAP Operation
	Anpassungen vorzunehmen. In dieser Beispielklasse werden die Prototypen all dieser Funktionen definiert,
	um einen Überblick der Möglichkeiten zu geben."""

	# den Modulnamen als Attribute der Klasse übernehmen (oben definiert als module='test/ip-phone')
	module = module

	def open(self):
		"""Öffnen des LDAP-Objekts."""

		super(object, self).open()
		# In dieser Methode können die Eigenschaften des Objekts in self.info dynamisch vor-initialisiert werden.
		# Das self.info Dictionary kann indirekt angesprochen werden, d.h. z.B. durch self['active'] = 1
		# Da der Basistyp von 'simpleLdap' (und damit von 'object') die Klasse 'base' ist, verhält sich
		# 'self' wie ein spezielles Dictionary. Es überprüft Operationen anhand der 'property_descriptions'
		# und liefert so auch defaults zurück. Eine Modifikation z.B. von self['name'] würde eine Exception
		# univention.admin.uexceptions.valueMayNotChange auslösen.

		# Durch die 'save' Methode werden die aktuellen Eigenschaften des geöffneten Objekts als "alter Zustand"
		# in self.oldinfo und self.oldpolicies gespeichert. Diese dienen später zum Vergleich mit dem
		# aktualisierten Eigenschaften in self.info.
		self.save()

	def _ldap_pre_create(self):
		"""Wird vor dem Anlegen des LDAP Objektes aufgerufen."""
		return super(object, self)._ldap_pre_create()

	def _ldap_post_create(self):
		"""Wird nach dem Anlegen des Objektes aufgerufen."""
		return super(object, self)._ldap_post_create()

	def _ldap_pre_modify(self):
		"""Wird vor dem Modifizieren des Objektes aufgerufen."""
		return super(object, self)._ldap_pre_modify()

	def _ldap_post_modify(self):
		"""Wird nach dem Modifizieren des Objektes aufgerufen."""
		return super(object, self)._ldap_post_modify()

	def _ldap_pre_remove(self):
		"""Wird vor dem Löschen des Objektes aufgerufen."""
		return super(object, self)._ldap_pre_remove()

	def _ldap_post_remove(self):
		"""Wird nach dem Löschen des Objektes aufgerufen."""
		return super(object, self)._ldap_post_remove()

	def _ldap_modlist(self):
		"""Diese Funktion kann definiert werden. Die gleichnamige ererbte Methode von 'simpleLdap'
		erstellt eine LDAP-modlist aus der Differenz zwischen self.oldinfo und self.info."""

		ml = super(object, self)._ldap_modlist()
		# hier sind weitere Anpassungen der modlist möglich
		return ml


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
