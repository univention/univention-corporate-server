# -*- coding: utf-8 -*-
#
# Univention Diectory Manager
#  this class reads the user specific settings
#
# Copyright (C) 2004-2009 Univention GmbH
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

import univention.admin.uexceptions
import string

# This class holds the user specific settings. The settings are not
# modified here; this module is merely used internally to receive them
# from different sources:
#
# - univentionPolicyAdminSettings policies
# - user settings objects in uid=<foo>,cn=admin-settings,cn=univention
#   if allowed by policy

class settings:

	def __init__(self, uldap, userdn):
		self.userdn=userdn
		self.reload(uldap)

	def reload(self, uldap):
		self.list_wizards = []
		self.list_dns = []
		self.list_adminModules = []
		self.list_selfAttributes = []
		self.list_selfOverrides = []
		self.list_listAttributes = []
		self.list_listNavigationAttributes = []

		self.base_dn = uldap.base
		self.may_override = False
		self.userentry = uldap.get(self.userdn)
		policies = uldap.getPolicies(self.userdn)

		try:
			self.list_wizards=policies['univentionPolicyAdminSettings']['univentionAdminListWizards']['value']
		except KeyError:
			pass

		try:
			self.list_dns=policies['univentionPolicyAdminSettings']['univentionAdminListDNs']['value']
		except KeyError:
			pass

		try:
			self.list_adminModules = policies['univentionPolicyAdminSettings']['univentionAdminListWebModules']['value']
		except KeyError:
			pass

		try:
			self.list_selfAttributes = policies['univentionPolicyAdminSettings']['univentionAdminSelfAttributes']['value']
		except KeyError:
			pass

		try:
			self.list_listAttributes = policies['univentionPolicyAdminSettings']['univentionAdminListAttributes']['value']
		except KeyError:
			pass

		try:
			self.list_listNavigationAttributes = policies['univentionPolicyAdminSettings']['univentionAdminListBrowseAttributes']['value']
		except KeyError:
			pass

		try:
			self.base_dn=policies['univentionPolicyAdminSettings']['univentionAdminBaseDN']['value'][0]
		except KeyError:
			pass

		self.default_containers={}
		for i in ['policy', 'users', 'groups', 'computers', 'networks', 'shares', 'printers']:
			try:
				self.default_containers[i]=policies['univentionPolicyAdminSettings']['univention%sObject' % i.capitalize()]['value']
			except KeyError:
				pass


		try:
			if policies['univentionPolicyAdminSettings']['univentionAdminMayOverrideSettings']['value'][0] == '1':
				self.may_override = True
				pos = 'cn=admin-settings,cn=univention,%s' % uldap.base
				attr = uldap.get('uid=%s,%s' % (self.userentry['uid'][0], pos))
				if attr:
					try:
						self.list_wizards=attr['univentionAdminListWizards']
					except KeyError:
						pass
					try:
						self.list_dns=attr['univentionAdminListDNs']
					except KeyError:
						pass
					try:
						self.list_adminModules = attr['univentionAdminListWebModules']
					except KeyError:
						pass
					try:
						self.list_selfOverrides = attr['univentionAdminSelfAttributes']
					except KeyError:
						pass
					try:
						self.list_listAttributes = attr['univentionAdminListAttributes']
					except KeyError:
						pass
					try:
						self.list_listNavigationAttributes = attr['univentionAdminListBrowseAttributes']
					except KeyError:
						pass
					try:
						self.base_dn=attr['univentionAdminBaseDN'][0]
					except KeyError:
						pass
					for i in ['policy','users', 'groups', 'computers', 'networks', 'shares', 'printers']:
						try:
							self.default_containers[i]=attr['univention%sObject' % i.capitalize()]
						except KeyError:
							pass
		except KeyError:
			pass
		except univention.admin.uexceptions.base:
			pass


	# Return whether wizard (i.e. "users/user") is to be listed in menu
	def listWizard(self, wizard):
		return not self.list_wizards or wizard in self.list_wizards

	def listAdminModule(self, module):
		return not self.list_adminModules or module in self.list_adminModules

	# Return whether object/dn is to be listed. This methods returns 1 if
	# the object is child or parent of a DN in list_dns.
	# XXX: Using "endswith" doesn't exactly do the job, however it is close
	# enough for now. Example, where it fails: "cn=bar" and "xcn=bar".
	def listDN(self, cdn, parents=1, childs=1):
		if not cdn.endswith(self.base_dn):
			return 0
		if not self.list_dns:
			return 1
		for dn in self.list_dns:
			if (parents and dn.endswith(cdn)) or (childs and cdn.endswith(dn)):
				return 1
		return 0

	def listObject(self, object, parents=1, childs=1):
		if not object.dn or not object.dn.endswith(self.base_dn):
			return 0
		if not self.list_dns:
			return 1
		for dn in self.list_dns:
			if (parents and dn.endswith(object.dn)) or (childs and object.dn.endswith(dn)):
				return 1
		return 0


	def filterDNs(self, dns, parents=1, childs=1):
		new_dns=[]
		for dn in dns:
			if self.listDN(dn, parents, childs):
				new_dns.append(dn)
		return new_dns

	def filterObjects(self, objects, parents=1, childs=1):
		new_objects=[]
		for object in objects:
			if self.listObject(object, parents, childs):
				new_objects.append(object)
		return new_objects

	def getListAttributes(self, module):
		columns=[]
		for entry in self.list_listAttributes:
			if entry.startswith('%s: ' % module):
				columns.append(entry.replace( '%s: ' % module, ''))
		return columns

	def getListNavigationAttributes(self):
		columns = []
		for attr in self.list_listNavigationAttributes:
			name = string.join(attr.split(':')[1:]).strip(' ')
			if not name in columns:
				columns.append([name, attr.split(':')[0].strip(' '), name])
		return columns
