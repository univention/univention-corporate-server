#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Copyright 2004-2011 Univention GmbH
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

import re, sys, string, copy
import univention.admin.filter		# Definiert Filterausdruck-Objekt für 'lookup' Funktion unten
import univention.admin.handlers	# Enthält simpleLdap, die Basisklasse für 'object' unten
import univention.admin.syntax		# Liefert standard Syntax-Definitionen für die UDM 'property_descriptions' unten

translation=univention.admin.localization.translation('univention.admin.handlers.test')
_=translation.translate

############################ <Syntax definitions> #############################

class SynVoIP_Protocols(univention.admin.syntax.select):
	"""Diese Klasse definiert einen neue Syntax für eine Auswahlliste von VoIP-Protokollen"""
	## der Text, der in dem Web-Frontend vor die Auswahlliste geschrieben werden soll
	name=u'VoIP_Protocol'

	## die Liste der Auswahlmöglichkeiten: Jedes der Elemente enthält einen eindeutigen Schlüssel
	## und den anzuzeigenden Text
	choices=[ ( 'sip', u'SIP'), ( 'h323', u'H.323' ), ('skype', u'Skype' ) ]

class SynVoIP_Address(univention.admin.syntax.simple):
	"""Diese Klasse dient als Syntax für VoIP Adresse. Der Aufbau ist einer E-Mail Adresse ähnlich,
	kann aber als Präfix noch ein Schema gefolgt von einem ':' enthalten.
	Valide Schemta sind: sip, h323 und skype"""

	name='VoIP_Address'
	min_length=4
	max_length=256
	_re = re.compile('((^(sip|h323|skype):)?([a-zA-Z])[a-zA-Z0-9._-]+)@[a-zA-Z0-9._-]+$')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		raise univention.admin.uexceptions.valueError, u'Not a valid VoIP Address'


############################ </Syntax definitions> ############################

############################ <UDM module API> #############################

## interner Name des Moduls, verwendet auch im Kommandozeilen-Client
module = 'test/ip_phone'
## dieses Objekt kann keine Unterobjekte enthalten
childs = 0
## ein sprechender Name für das Web-Frontend
short_description = u'IP-Phone'
## eine ausführliche Beschreibung
long_description = u'An example module for the Univention Directory Manager'
## die LDAP Operationen, die auf diesem Objekt ausgeführt werden können
operations=['add','edit','remove','search','move']


##### Um einen eigenen Wizard zu erstellen, der im UDM-Web links in der Navigationsleiste erscheint:
## usewizard = 1
## wizardmenustring = "VoIP"
## wizarddescription =  "Hinzufuegen, Loeschen und Suchen von VoIP Objekten"
## wizardoperations = { 'add' : [ "Hinzufuegen", "Fuegt ein VoIP Objekt hinzu" ],
##                    'find' : [ "Suchen", "Sucht VoIP Objekte" ] }
## wizardpath="univentionUsersObject"

############################ <UDM module options> #############################
## Liste der Optionen für dieses Modul, bzw. für den behandelten Objekttyp
options={
	# durch 'options' werden optionale Eigenschaften eines Objekts definiert
	'redirection': univention.admin.option(
			short_description=_('Call redirect option'),
			default=1,
			editable=1,
			objectClasses = ['testPhoneCallRedirect'],
		)
}

########################### <UDM module properties> ###########################

## Liste der Eigenschaften für dieses Modul
property_descriptions={
	# der eindeutige Name eines IP-Telefons
	'name': univention.admin.property(
			short_description= u'Name',
			long_description= u'ID of the IP-phone',
			syntax=univention.admin.syntax.hostName,	# Eigenschaft muss der Syntax eines Rechnernamens entsprechen, Def. in syntax.py
			multivalue=0,
			options=[],
			required=1,								# Eigenschaft muss angegeben werden
			may_change=0,								# Eigenschaft darf nach Erstellung nicht verändert werden
			identifies=1								# Eigenschaft muss eindeutig sein
		),
	#
	'active': univention.admin.property(
			short_description= u'active',
			long_description= u'The IP-phone can be deactivated',
			syntax=univention.admin.syntax.boolean,		# kann nur die Werte '1' oder '0' annehmen, Definition in syntax.py
			multivalue=0,
			options=[],
			required=0,								# Eigenschaft muss nicht zwingend angegeben werden
			default='1',								# Eigenschaft ist standardmäßig aktiviert
			may_change=1,								# Eigenschaft darf modifiziert werden
			identifies=0
		),
	'protocol': univention.admin.property(
			short_description= u'Protocol',
			long_description= u'Supported VoIP protocols',
			syntax=SynVoIP_Protocols,					# nutzt die selbst definierte Auswahlliste als Syntax
			multivalue=0,
			options=[],
			required=0,
			default='sip',							# der Eintrag 'sip' ist vorausgewählt
			may_change=1,
			identifies=0
		),
	'ip': univention.admin.property(
			short_description = u'IP-Address',
			long_description = u'IP-Address of the IP-phone',
			syntax=univention.admin.syntax.ipAddress,	# muss der Syntax einer IP (Version 4) Adresse entsprechen
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'priuser': univention.admin.property(
			short_description = u'Primary User',
			long_description = u'The primary user of this IP-phone',
			syntax=SynVoIP_Address,						# muss der Syntax einer VoIP Adresse entsprechen
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'users': univention.admin.property(
			short_description = u'Additional Users',
			long_description = u'Users, that may register with this phone',
			syntax=SynVoIP_Address,						# jeder Eintrag muss der Syntax einer VoIP Adresse entsprechen
			multivalue=1,							# Dies ist eine Liste von Adressen
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'redirect_user': univention.admin.property(
			short_description = u'Redirection User',
			long_description = u'Address for call redirection',
			syntax=SynVoIP_Address,
			multivalue=0,
			options=['redirection'],					# Ist nur da, wenn die Option gesetzt ist
			required=0,
			may_change=1,
			identifies=0
		),
}

########################### <UDM module layout> ###########################

## Das 'layout' definiert die Anordung der Felder im Web-Frontend.
## Jeder 'univention.admin.tab' entspricht einem Reiter:
##   * Der erste Parameter ist der Name des Reiters und der zweite Parameter
##     ist eine Beschreibung der Einstellungsmöglich für diesen Reiter
##   * Die folgende Liste definiert die Anordnung der einzelnen Eigenschaftsfelder.
layout=[
	univention.admin.tab( u'Gerneral', u'Basic Settings',
			[ [ univention.admin.field( "name" ), univention.admin.field( "active" ) ],
			[ univention.admin.field( "ip" ), univention.admin.field( "protocol" ) ],
			[ univention.admin.field( "priuser" ) ] ] ),
	univention.admin.tab( u'Advanced', u'Advanced Settings', [
				[ univention.admin.field( "users" ) ],
			], advanced = True ),
	univention.admin.tab( u'Redirect', u'Redirect Option', [
				[ univention.admin.field( "redirect_user" ) ],
			], advanced = True ),
	]

################ <Mapping of UDM properties to LDAP attribute> ################

## Die folgenden beiden Hilfsfunktionen dienen zur Abbildung von bool'schen Werten '0' und '1' auf 'no' und 'yes' (siehe Mapping)
def boolToString(value):
	if value == '1':
		return 'yes'
	else:
		return 'no'

def stringToBool(value):
	if value[0].lower() == 'yes':
		return '1'
	else:
		return '0'

## Das 'mapping' Objekt definiert die Abbildung der Eigenschaften des UDM-Moduls/Objekts auf Attribute eines LDAP-Objektes
mapping=univention.admin.mapping.mapping()
## Abbindung der Eigenschaft 'name' auf den RDN, nutzt vordefinierte Mapping-Funktion aus mapping.py:
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
## mapping.register der Eigenschaft 'active' auf das LDAP-Attribut testPhoneActive:
## Dabei wird die Hilfsfunktion 'boolToString' für die Umwandlung in das LDAP-Attribut verwendet
## und die Hilfsfunktion 'stringToBool' für den umgekehrten Weg:
mapping.register('active', 'testPhoneActive', boolToString, stringToBool)
## Abbindung der Eigenschaft 'protocol' auf das LDAP-Attribut testPhoneProtocol:
mapping.register('protocol', 'testPhoneProtocol', None, univention.admin.mapping.ListToString)
mapping.register('ip', 'testPhoneIP', None, univention.admin.mapping.ListToString)
mapping.register('priuser', 'testPhonePrimaryUser', None, univention.admin.mapping.ListToString)
## Abbindung der Eigenschaft 'users' ohne weitere Übersetzung direkt auf das LDAP-Attribut testPhoneUsers:
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

	## den Modulnamen als Attribute der Klasse übernehmen (oben definiert als module='test/ip-phone')
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		"""Initialisierung des Objektes. Hier müssen die oben definierten globalen Variablen 'mapping'
		und 'property_descriptions' übernommen werden"""
		global options
		global mapping
		global property_descriptions

		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self._exists=0
		self.mapping=mapping
		self.descriptions=property_descriptions

		## Initialisierungsfunktion der Basisobjektklasse simpleLdap in univention.admin.handlers
		## * liest die Objekt Attribute für den 'dn' aus dem LDAP ud stellt sie als self.oldattr bereit.
		## * stellt die per 'mapping' übersetzten LDAP-Attributnamen und Werte als
		##   UDM Objekt-Variablennamen ('property_descriptions') und -Werte bereit:
		##   - per Konvention wird in self.oldinfo der bisherige Objekt-Zustand bereitgestellt
		##   - über self.info wird der vom Benutzer (CLI oder Web) aktualisierte Objekt-Zustand
		##     bereitgestellt
		##   An diesem Punkt sind beide noch identisch. 
		## * falls Richtlinien mit diesem Objekt verknüpft sind, werden sie ebenso als self.oldpolicies
		##   und self.policies bereitgestellt:
		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)

		## Über den Vergleich von self.oldattr['objectClass'] mit den 'objectClasses' der oben definierten
		## 'options' lässt sich ermitteln, welche Optionen an dem Objekt aktiviert sind. Die so ermittelte
		## Auswahl sollte als # self.options an diesem Objekt notiert werden, damit darauf basierend
		## weitere Entscheidungen getroffen werden können.
		self.options=[]
		if self.oldattr.has_key('objectClass'):
			ocs = set(self.oldattr['objectClass'])
			for opt in ('redirection', ):
				if options[opt].matches(ocs):
					self.options.append(opt)
		else:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, '%s: reset options to default by _define_options' % module)
			self._define_options( options )

		self.old_options= copy.deepcopy( self.options )

	def exists(self):
		return self._exists

	def open(self):
		"""Öffnen des LDAP-Objekts."""

		univention.admin.handlers.simpleLdap.open(self)
		## In dieser Methode können die Eigenschaften des Objekts in self.info dynamisch Vor-initialisiert werden. 
		## Das self.info Dictionary kann indirekt angesprochen werden, d.h. z.B. durch self['active'] = 1
		## Da der Basistyp von 'simpleLdap' (und damit von 'object') die Klasse 'base' ist, verhält sich
		## 'self' wie ein spezielles Dictionary. Es überprüft Operationen anhand der 'property_descriptions'
		## und liefert so auch defaults zurück. Eine Modifikation z.B. von self['name'] würde eine Exception
		## univention.admin.uexceptions.valueMayNotChange auslösen.

		## Durch die 'save' Methode werden die aktuellen Eigenschaften des geöffneten Objekts als "alter Zustand"
		## in self.oldinfo und self.oldpolicies gespeichert. Diese dienen später zum Vergleich mit dem
		## aktualisierten Eigenschaften in self.info.
		self.save()
		self.old_options= copy.deepcopy( self.options ) # Optionen zum späteren Vergleich speichern.

	def _ldap_pre_create(self):
		"""Wird vor dem Anlegen des LDAP Objektes aufgerufen."""
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_post_create(self):
		"""Wird nach dem Anlegen des Objektes aufgerufen."""
		pass

	def _ldap_pre_modify(self):
		"""Wird vor dem Modifizieren des Objektes aufgerufen."""
		pass

	def _ldap_post_modify(self):
		"""Wird nach dem Modifizieren des Objektes aufgerufen."""
		pass

	def _ldap_pre_remove(self):
		"""Wird vor dem Löschen des Objektes aufgerufen."""
		pass

	def _ldap_post_remove(self):
		"""Wird nach dem Löschen des Objektes aufgerufen."""
		pass

	def _update_policies(self):
		pass

	def _ldap_addlist(self):
		"""Diese Funktion muss definiert werden, weil sie von 'create' verwendet wird.
		Sie sollte die nur zum Anlegen notwendigen LDAP-Attribute zurückgeben, d.h. mindestens die
		'objectClass' Definition. Nach dieser Methode ruft 'create' _ldap_modlist auf, um weitere
		Modifikationen an Eigenschaften festzustellen."""

		al = [ ('objectClass', ['top', 'testPhone' ] ) ]
		return al

	def _remove_attr(self, ml, attr):
		for m in ml:
			if m[0] == attr:
				ml.remove(m)
		if self.oldattr.get(attr, []):
			ml.insert(0, (attr, self.oldattr.get(attr, []), ''))
		return ml

	def _ldap_modlist(self):
		"""Diese Funktion kann definiert werden. Die gleichnamige ererbte Methode von 'simpleLdap'
		erstellt eine LDAP-modlist aus der Differenz zwischen self.oldinfo und self.info."""

		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)
		## hier sind weitere Anpassungen der modlist möglich, z.B. die Reaktion
		## auf Veränderungen an der Optionenauswahl:
		if self.options != self.old_options:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'options: %s' % self.options)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'old_options: %s' % self.old_options)
			if 'redirection' in self.options and not 'redirection' in self.old_options:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'added redirection option')
				ocs=self.oldattr.get('objectClass', [])
				if not 'testPhoneCallRedirect' in ocs:
					ml.insert(0, ('objectClass', '', 'testPhoneCallRedirect'))
			if not 'redirection' in self.options and 'redirection' in self.old_options:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'remove redirection option')
				ocs=self.oldattr.get('objectClass', [])
				if 'testPhoneCallRedirect' in ocs:
					ml.insert(0, ('objectClass', 'testPhoneCallRedirect', ''))

				for key in [ 'testPhoneRedirectUser', ]:
					ml=self._remove_attr(ml,key)
		return ml
 

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):
	"""Diese Function sucht nach Objekten, die dem in diesem Modul verwalteten Typ (objectClass)
	die den angegebenen Suchkriterien entsprechen. Der Rückgabewert dieser Funktion ist ein Liste
	der gefunden Objekte."""

	filter=univention.admin.filter.conjunction('&', [
				univention.admin.filter.expression('objectClass', 'testPhone'),
				])

	if filter_s:
		## Vom Benutzer übergebene Zeichenkette in ein Filterausdruck-Objekt übersetzten:
		filter_p=univention.admin.filter.parse(filter_s)
		## Übersetzung der UDM Objekt-Variablennamen ('property_descriptions') und -Werte im Filterausdruck
		## auf LDAP-Attributnamen und -Werte, wie durch 'mapping' oben definiert:
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		## Oben definierten Objektklassenfilter ergänzen um den vom Benutzer übergebenen Filterausdruck:
		filter.expressions.append(filter_p)

	res=[]
	## LDAP-Suche öber das LDAP-Connection-Objekt 'lo' unter Verwendung des unicode-Encodings,
	## das Python intern verwendet:
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		## Ergebnisliste aufbauen
		res.append(object(co, lo, None, dn))
	return res


def identify(dn, attr, canonical=0):
	"""Prüft ob die verwaltete Objektklasse diese Moduls in der übergebenen Liste enthalten ist,
	d.h. ob dieses Modul für die Handhabung des Objekts zuständig ist"""

	return 'testPhone' in attr.get('objectClass', [])

