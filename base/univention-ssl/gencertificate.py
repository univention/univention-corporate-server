# -*- coding: utf-8 -*-
#
# Univention SSL
"""SSL listener module."""
#
# Copyright 2004-2015 Univention GmbH
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

# pylint: disable-msg=C0103,W0704

__package__ = ''	# workaround for PEP 366
from listener import configRegistry, setuid, unsetuid
import grp
import os

import univention.debug as ud
import subprocess

name = 'gencertificate'
description = 'Generate new Certificates'
filter = '(|' + \
		'(objectClass=univentionDomainController)' + \
		'(objectClass=univentionClient)' + \
		'(objectClass=univentionMobileClient)' + \
		'(objectClass=univentionCorporateClient)' + \
		'(objectClass=univentionMemberServer))'
attributes = []


uidNumber = 0
gidNumber = 0
saved_uid = 65545
SSLDIR = '/etc/univention/ssl'

def initialize():
	"""Initialize the module once on first start or after clean."""
	ud.debug(ud.LISTENER, ud.INFO, 'CERTIFICATE: Initialize')

def handler(dn, new, old):
	"""Handle changes to 'dn'."""
	setuid(0)
	try:
		if configRegistry['server/role'] != 'domaincontroller_master':
			return

		global uidNumber
		try:
			uidNumber = int(new.get('uidNumber', ['0'])[0])
		except (LookupError, TypeError, ValueError):
			uidNumber = 0

		global gidNumber
		try:
			gidNumber = int(grp.getgrnam('DC Backup Hosts')[2])
		except (LookupError, TypeError, ValueError):
			ud.debug(ud.LISTENER, ud.WARN,
					'CERTIFICATE: Failed to get groupID for "%s"' % dn)
			gidNumber = 0

		if new and not old:
			# changeType: add
			try:
				domain = new['associatedDomain'][0]
			except LookupError:
				domain = configRegistry['domainname']
			create_certificate(new['cn'][0], domainname=domain)
		elif old and not new:
			# changeType: delete
			try:
				domain = old['associatedDomain'][0]
			except LookupError:
				domain = configRegistry['domainname']
			remove_certificate(old['cn'][0], domainname=domain)
		else:
			# changeType: modify
			try:
				old_domain = old['associatedDomain'][0]
			except LookupError:
				old_domain = configRegistry['domainname']

			try:
				new_domain = new['associatedDomain'][0]
			except LookupError:
				new_domain = configRegistry['domainname']

			if new_domain != old_domain:
				remove_certificate(old['cn'][0], domainname=old_domain)
				create_certificate(new['cn'][0], domainname=new_domain)
			else:
				# Reset permissions
				fqdn = "%s.%s" % (new['cn'][0], new_domain)
				certpath = os.path.join(SSLDIR, fqdn)
				os.path.walk(certpath, set_permissions, None)
	finally:
		unsetuid()

def set_permissions(_arg, directory, fnames):
	"""Set file permission on directory and files within."""
	ud.debug(ud.LISTENER, ud.INFO,
			'CERTIFICATE: Set permissons for = %s with owner/group %s/%s' % \
					(directory, gidNumber, uidNumber))
	os.chown(directory, uidNumber, gidNumber)
	os.chmod(directory, 0750)

	for fname in fnames:
		filename = os.path.join(directory, fname)
		ud.debug(ud.LISTENER, ud.INFO,
				'CERTIFICATE: Set permissons for = %s with owner/group %s/%s' % \
						(filename, gidNumber, uidNumber))
		os.chown(filename, uidNumber, gidNumber)
		os.chmod(filename, 0640)

def remove_dir(_arg, directory, fnames):
	"""Remove directory and all files within."""
	for fname in fnames:
		filename = os.path.join(directory, fname)
		os.remove(filename)
	os.rmdir(directory)

def create_certificate(hostname, domainname):
	"""Create SSL host certificate."""
	fqdn = '%s.%s' % (hostname, domainname)
	certpath = os.path.join(SSLDIR, fqdn)
	link_path = os.path.join(SSLDIR, hostname)

	if os.path.exists(certpath):
		ud.debug(ud.LISTENER, ud.WARN,
				'CERTIFICATE: Certificate for host %s already exists' % (fqdn,))
		if os.path.islink(link_path):
			return
	else:
		if len(fqdn) > 64:
			ud.debug(ud.LISTENER, ud.ERROR,
					'CERTIFICATE: can\'t create certificate, Common Name too long: %s' % \
							(fqdn,))
			return

		ud.debug(ud.LISTENER, ud.INFO,
				'CERTIFICATE: Creating certificate %s' % hostname)

		cmd = '. /usr/share/univention-ssl/make-certificates.sh;gencert "%s" "%s"' % \
				(fqdn, fqdn)
		subprocess.call(cmd, shell=True)

	# Create symlink
	try:
		os.remove(link_path)
	except OSError:
		pass
	try:
		os.symlink(certpath, link_path)
	except OSError:
		pass
	# Fix permissions
	os.path.walk(certpath, set_permissions, None)

def remove_certificate(hostname, domainname):
	"""Remove SSL host certificate."""
	fqdn = '%s.%s' % (hostname, domainname)
	ud.debug(ud.LISTENER, ud.INFO, 'CERTIFICATE: Revoke certificate %s' % (fqdn,))
	subprocess.call(('/usr/sbin/univention-certificate', 'revoke', '-name', fqdn))

	link_path = os.path.join(SSLDIR, hostname)
	if os.path.exists(link_path):
		os.remove(link_path)

	certpath = os.path.join(SSLDIR, fqdn)
	if os.path.exists(certpath):
		os.path.walk(certpath, remove_dir, None)

def clean():
	"""Handle request to clean-up the module."""
	return

def postrun():
	"""Transition from prepared-state to not-prepared."""
	return
