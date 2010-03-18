#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2004-2010 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import re, sys, string
import univention.admin.filter
import univention.admin.handlers
import univention.admin.syntax

class SynVoIP_Protocols(univention.admin.syntax.select):
	"""Diese Klasse definiert einen neue Syntax für eine Auswahlliste von VoIP-Protokollen"""
	# der Text, der in dem Web-Frontend vor die Auswahlliste geschrieben werden soll
	name=u'VoIP_Protocol'
	# die Liste der Auswahlmöglichkeiten: Jedes der Elemente enthält einen eindeutigen Schlüssel und den anzuzeigenden Text
	choices=[ ( 'sip', u'SIP'), ( 'h323', u'H.323' ), ('skype', u'Skype' ) ]

class SynVoIP_Address(univention.admin.syntax.simple):
	"""Diese Klasse dient als Syntax für VoIP Adresse. Der Aufbau ist einer E-Mail Adresse ähnlich,
	kann aber als Präfix noch ein Schema gefolgt von einem ':' enthalten. Valide Schemta sind: sip, h323 und skype"""
	name='VoIP_Address'
	min_length=4
	max_length=256
	_re = re.compile('((^(sip|h323|skype):)?([a-zA-Z])[a-zA-Z0-9._-]+)@[a-zA-Z0-9._-]+$')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		raise univention.admin.uexceptions.valueError, u'Keine gültige VoIP Adresse'

# interner Name des Moduls
module = 'test/ip-phone'
# dieses Objekt kann keine Kindsobjekte enthalten
childs = 0
# ein sprechender Name für das Web-Frontend
short_description = u'IP-Telefon'
# eine ausführliche Beschreibung
long_description = u'Ein Beispiel-Modul für den Univention Admin zur Verwaltung von IP-Telefonen'
# die LDAP Operationen, die auf diesem Objekt ausgeführt werden können
operations=['add','edit','remove','search','move']


# Um einen eigenen Wizard zu erstellen
#usewizard = 1
#wizardmenustring = "VoIP"
#wizarddescription =  "Hinzufuegen, Loeschen und Suchen von VoIP Objekten"
#wizardoperations = { 'add' : [ "Hinzufuegen", "Fuegt ein VoIP Objekt hinzu" ],
#                    'find' : [ "Suchen", "Sucht VoIP Objekte" ] }
#wizardpath="univentionUsersObject"

# Liste der Optionen für dieses Modul
options={
	# mit dieser Option können die erweiterten Einstellungen ausgeblendet werden
	'extended' : univention.admin.option(
			short_description= u'Erweiterte Einstellungen',
			default=1
		)
}
# Liste der Eigenschaften für dieses Modul
property_descriptions={
	# der eindeutige Name eines IP-Telefons
	'name': univention.admin.property(
			short_description= u'Name',
			long_description= u'Name des Telefons',
			syntax=univention.admin.syntax.hostName,	# muss der Syntax eines Rechnernamens entsprechen
			multivalue=0,
			options=[],
			required=1,									# muss angegeben werden
			may_change=0,								# darf nach Erstellung nicht verändert werden
			identifies=1
		),
	#
	'active': univention.admin.property(
			short_description= u'freigeschaltet',
			long_description= u'Ein IP-Telefon kann gesperrt werden',
			syntax=univention.admin.syntax.boolean,		# kann nur die Werte '1' oder '0' annehmen
			multivalue=0,
			options=[],
			required=0,									# muss nicht zwingend angegeben werden
			default='1',								# ist standardmäßig aktiviert
			may_change=1,								# darf modifiziert werden
			identifies=0
		),
	'protocol': univention.admin.property(
			short_description= u'Protokoll',
			long_description= u'Welches VoIP Protokoll wird von dem Telefon unterstützt',
			syntax=SynVoIP_Protocols,					# nutzt die selbst definierte Auswahlliste als Syntax
			multivalue=0,
			options=[],
			required=0,									# die Angabe ist nicht erforderlich
			default='sip',								# das Eintrag 'sip' ist vorausgewählt
			may_change=1,
			identifies=0
		),
	'ip': univention.admin.property(
			short_description = u'IP-Adresse',
			long_description = u'',
			syntax=univention.admin.syntax.ipAddress,	# muss der Syntax einer IP (Version 4) Adresse entsprechen
			multivalue=0,
			options=[],
			required=1,									# zwingend erforderlich
			may_change=1,
			identifies=0
		),
	'priuser': univention.admin.property(
			short_description = u'primärer Benutzer',
			long_description = u'Der primäre Benutzer dieses Telefons',
			syntax=SynVoIP_Address,						# muss der Syntax einer VoIP Adresse entsprechen
			multivalue=0,
			options=[],
			required=1,									# diese Angabe ist erforderlich
			may_change=1,
			identifies=0
		),
	'users': univention.admin.property(
			short_description = u'weitere Benutzer',
			long_description = u'Benutzer, die an diesem Telefon registriert sein dürfen',
			syntax=SynVoIP_Address,						# jeder Eintrag muss der Syntax einer VoIP Adresse entsprechen
			multivalue=1,								# Dies ist eine Liste von Adressen
			options=['extended'],						# Ist nur sichtbar, wenn die Option 'extended' gesetzt ist
			required=0,									# ist nicht zwingend erforderlich
			may_change=1,
			identifies=0
		)
}
# definiert das Layout für das Web-Frontend
# 'univention.admin.tab entspricht einem Reiter:
#    Der erste Parameter ist der Name des Reiters und der zweite Parameter ist eine Beschreibung der Einstellungsmöglich für diesen Reiter
#    Die folgende Liste definiert die Anordnung der einzelnen Eigenschaftsfelder.
layout=[
	univention.admin.tab( u'Allgemein', u'Grundeinstellungen',
			[ [ univention.admin.field( "name" ), univention.admin.field( "active" ) ],
			[ univention.admin.field( "ip" ), univention.admin.field( "protocol" ) ],
			[ univention.admin.field( "priuser" ) ] ] ),
	univention.admin.tab( u'Erweiterungen', u'Erweiterte Einstellungen',
			[ [ univention.admin.field( "users" ) ] ] )	]

# die folgenden beiden Hilfsfunktionen dienen zur Abbildung von bool'schen Werten '0' und '1' auf 'no' und 'yes' (siehe Mapping)
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

# das 'mapping' Objekt definiert die Abbildung der Eigenschaften des Moduls auf Attribute eines LDAP-Objektes
mapping=univention.admin.mapping.mapping()
# bildet die Eigenschaft 'name' auf den RDN ab
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
# bildet die Eigenschaft 'active' auf das LDAP-Attribut testPhoneActive ab. Dabei wird die Hilfsfunktion 'boolToString' für die Abbildung
# in das LDAP-Attribut verwendet und die Hilfsfunktion 'stringToBool' für den umgekehrten Weg.
mapping.register('active', 'testPhoneActive', boolToString, stringToBool)
# bildet die Eigenschaft 'protocol' auf das LDAP-Attribut testPhoneProtocol ab
mapping.register('protocol', 'testPhoneProtocol', None, univention.admin.mapping.ListToString)
# bildet die Eigenschaft 'ip' auf das LDAP-Attribut testPhoneIP ab
mapping.register('ip', 'testPhoneIP', None, univention.admin.mapping.ListToString)
# bildet die Eigenschaft 'priuser' auf das LDAP-Attribut testPhonePrimaryUser ab
mapping.register('priuser', 'testPhonePrimaryUser', None, univention.admin.mapping.ListToString)
# bildet die Eigenschaft 'users' auf das LDAP-Attribut testPhoneUsers ab
mapping.register('users', 'testPhoneUsers')

class object(univention.admin.handlers.simpleLdap):
	"""Dieses Objekt unterstützt den Univention Admin bei LDAP Operationen, die sich auf dieses Modul beziehen.
	Die Basisklasse univention.admin.handlers.simpleLdap implementiert die komplette Kommunikation über LDAP, so dass hier nur die Anpassungen für
	dieses spezielle LDAP-Objekt implementiert werden müssen. Dafür bietet die Basisklasse jeweils eine Funktionen um vor und nach einer LDAP
	Operation Anpassungen vorzunehmen. In dieser Beispielklasse werden die Prototypen all dieser Funktionen definiert, um einen Überblick der
	Möglichkeiten zu geben."""
	# den Modulnamen als Attribute der Klasse übernehmen
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		"""Initialisierung des Objektes. Hier müssen die globalen Variablen 'mapping' und 'property_descriptions' übernommen werden"""
		global mapping
		global property_descriptions

		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self._exists=0
		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)

	def exists(self):
		return self._exists

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)
		self.save()

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
		"""Diese Funktion muss definiert werden und gibt die 'objectClass' Definition zurück."""
		return [ ('objectClass', ['top', 'testPhone' ] ) ]


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):
	"""Diese Function sucht nach Objekten, die dem in diesem Modul verwalteten Typ und die den angegebenen Suchkriterien entsprechen.
	Der Rückgabewert dieser Funktion ist ein Liste der gefunden Objekte."""
	filter=univention.admin.filter.conjunction('&', [
				univention.admin.filter.expression('objectClass', 'testPhone'),
				])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn))
	return res


def identify(dn, attr, canonical=0):
	"""Prüft ob die verwaltete Objektklasse diese Moduls in der übergebenen Liste enthalten ist"""
	return 'testPhone' in attr.get('objectClass', [])

