# -*- coding: utf-8 -*-
#
# Univention App Center
#  baseconfig module: Modifies udm settings/portal_entries on UCR changes
#
# Copyright 2017-2019 Univention GmbH
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
from ldap.dn import escape_dn_chars
from ldap import SERVER_DOWN
from base64 import b64encode
from copy import copy
from urlparse import urlsplit

from univention.config_registry.interfaces import Interfaces
import univention.admin.uexceptions as udm_errors

from univention.appcenter.log import log_to_logfile, get_base_logger
from univention.appcenter.ucr import ucr_get
from univention.appcenter.udm import create_object_if_not_exists, remove_object_if_exists, get_machine_connection, modify_object, init_object


log_to_logfile()
portal_logger = get_base_logger().getChild('portalentries')


class _Link(object):
	def __init__(self, protocol=None, host=None, port=None, path=None, full=None):
		self.protocol = protocol
		self.host = host
		self.port = port
		self.path = path
		self.full = full

	def __str__(self):
		if self.full:
			return self.full
		if not self.protocol or not self.host or not self.path:
			return ''
		port = ':%s' % self.port
		if self.protocol == 'http' and (not self.port or self.port == '80'):
			port = ''
		if self.protocol == 'https' and (not self.port or self.port == '443'):
			port = ''
		return '%s://%s%s%s' % (self.protocol, self.host, port, self.path)

	def __nonzero__(self):
		return str(self) != ''


def _handler(ucr, changes):
	changed_entries = set()
	for key in changes.keys():
		match = re.match('ucs/web/overview/entries/(admin|service)/([^/]+)/.*', key)
		if match:
			changed_entries.add(match.group(2))
	changed_entries -= set(['umc', 'invalid-certificate-list', 'root-certificate', 'ldap-master'])
	portal_logger.debug('Changed: %r' % changed_entries)
	if not changed_entries:
		return
	lo, pos = get_machine_connection()
	pos.setDn('cn=portal,cn=univention,%s' % ucr.get('ldap/base'))
	hostname = '%s.%s' % (ucr.get('hostname'), ucr.get('domainname'))

	# iterate over all ipv4 and ipv6 addresses and append them to the link
	local_hosts = [hostname]
	interfaces = Interfaces(ucr)
	for idev, iconf in interfaces.all_interfaces:
		# get ipv4 address of device
		if iconf.ipv4_address():
			local_hosts.append(str(iconf.ipv4_address().ip))

		# get ipv6 addresses of device
		for iname in iconf.ipv6_names:
			local_hosts.append('[%s]' % (iconf.ipv6_address(iname).ip, ))

	portal_logger.debug('Local hosts are: %r' % local_hosts)
	attr_entries = {}
	for changed_entry in changed_entries:
		attr_entries[changed_entry] = {}
	for ucr_key in ucr.keys():
		match = re.match('ucs/web/overview/entries/([^/]+)/([^/]+)/(.*)', ucr_key)
		if not match:
			continue
		category = match.group(1)
		cn = match.group(2)
		key = match.group(3)
		value = ucr.get(ucr_key)
		if cn in attr_entries:
			portal_logger.debug('Matched %r -> %r' % (ucr_key, value))
			entry = attr_entries[cn]
			entry['category'] = category
			entry['name'] = cn
			if '_links' not in entry:
				links = []
				for host in local_hosts:
					if host:
						links.append(_Link(host=host))
				entry['_links'] = links
			if key == 'link':
				for link in entry['_links']:
					if value.startswith('http'):
						link.full = value
					else:
						link.path = value
			elif key == 'port_http':
				if value:
					for link in entry['_links'][:]:
						if link.protocol == 'https':
							link = copy(link)
							entry['_links'].append(link)
						link.protocol = 'http'
						link.port = value
			elif key == 'port_https':
				if value:
					for link in entry['_links'][:]:
						if link.protocol == 'http':
							link = copy(link)
							entry['_links'].append(link)
						link.protocol = 'https'
						link.port = value
			elif key == 'icon':
				try:
					if value.startswith('/univention-management-console'):
						value = '/univention%s' % value[30:]
					with open('/var/www/%s' % value) as fd:
						entry['icon'] = b64encode(fd.read())
				except EnvironmentError:
					pass
			elif key == 'label':
				entry.setdefault('displayName', [])
				entry['displayName'].append(('en_US', value))
			elif key == 'label/de':
				entry.setdefault('displayName', [])
				entry['displayName'].append(('de_DE', value))
			elif key == 'label/fr':
				entry.setdefault('displayName', [])
				entry['displayName'].append(('fr_FR', value))
			elif key == 'description':
				entry.setdefault('description', [])
				entry['description'].append(('en_US', value))
			elif key == 'description/de':
				entry.setdefault('description', [])
				entry['description'].append(('de_DE', value))
			elif key == 'description/fr':
				entry.setdefault('description', [])
				entry['description'].append(('fr_FR', value))
			else:
				portal_logger.info('Don\'t know how to handle UCR key %s' % ucr_key)
	for cn, attrs in attr_entries.items():
		dn = 'cn=%s,%s' % (escape_dn_chars(cn), pos.getDn())
		unprocessed_links = attrs.pop('_links', [])
		my_links = set()
		no_ports = all(not link.port for link in unprocessed_links)
		for link in unprocessed_links:
			if no_ports:
				if link.protocol == 'http':
					link.port = '80'
				elif link.protocol == 'https':
					link.port = '443'
			if link:
				my_links.add(str(link))
			if not link.protocol:
				link.protocol = 'http'
				if link:
					my_links.add(str(link))
				link.protocol = 'https'
				if link:
					my_links.add(str(link))
		my_links = list(my_links)
		portal_logger.debug('Processing %s' % dn)
		portal_logger.debug('Attrs: %r' % attrs)
		portal_logger.debug('Links: %r' % my_links)
		try:
			obj = init_object('settings/portal_entry', lo, pos, dn)
		except udm_errors.noObject:
			portal_logger.debug('DN not found...')
			if my_links:
				portal_logger.debug('... creating')
				attrs['link'] = my_links
				attrs['portal'] = ['cn=domain,cn=portal,cn=univention,%s' % ucr_get('ldap/base')]
				attrs['activated'] = True
				try:
					create_object_if_not_exists('settings/portal_entry', lo, pos, **attrs)
				except udm_errors.insufficientInformation as exc:
					portal_logger.info('Cannot create: %s' % exc)
			continue
		links = obj['link']
		portal_logger.debug('Existing links: %r' % links)
		links = [_link for _link in links if urlsplit(_link).hostname not in local_hosts]
		links.extend(my_links)
		portal_logger.debug('New links: %r' % links)
		if not links:
			portal_logger.debug('Removing DN')
			remove_object_if_exists('settings/portal_entry', lo, pos, dn)
		else:
			portal_logger.debug('Modifying DN')
			attrs['link'] = links
			modify_object('settings/portal_entry', lo, pos, dn, **attrs)


def handler(ucr, changes):
	try:
		_handler(ucr, changes)
	except SERVER_DOWN:
		portal_logger.error('LDAP server is not available.')
	except Exception:
		portal_logger.exception('Exception in UCR module create_portal_entries')
