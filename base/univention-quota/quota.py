#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Quota
#  Dump Quota settings into a cache directory
#
# Copyright 2015-2019 Univention GmbH
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

from __future__ import absolute_import

import ldap
import pickle
import os

import univention.debug as ud
import univention.lib.policy_result

import listener

name = 'quota'
description = 'Dump quota settings into a cache directory'
filter = '(|(objectClass=univentionPolicyShareUserQuota)(objectClass=organizationalRole)(objectClass=organizationalUnit)(objectClass=univentionBase)(objectClass=univentionShare))'
attributes = []

'''
The listener module has to re-create the cache for one share if the share
path, the share hostname, or the policy reference has been changed at a share
object or if a quota policy has been changed or if a policy reference has
been changed at a parent object.
'''

SHARE_CACHE_DIR = '/var/cache/univention-quota/'
SHARE_CACHE_TODO_DIR = '/var/cache/univention-quota/todo'


def _dump_share_and_policy_result(dn, share_object, policy_result):
	filename = os.path.join(SHARE_CACHE_DIR, dn)

	f = open(filename, 'w+')
	os.chmod(filename, 0o600)
	p = pickle.Pickler(f)
	p.dump((dn, share_object, policy_result))
	p.clear_memo()
	f.close()


def _read_share_and_policy_result(dn):
	filename = os.path.join(SHARE_CACHE_DIR, dn)

	if not os.path.exists(filename):
		return (None, None)

	f = open(filename, 'r')
	(tdn, share_object, policy_result) = pickle.load(f)
	f.close()

	return (share_object, policy_result)


def _remove_cache_for_share(dn):
	filename = os.path.join(SHARE_CACHE_DIR, dn)
	ud.debug(ud.LISTENER, ud.INFO, 'Remove "%s"' % filename)
	if os.path.exists(filename):
		os.remove(filename)


def _is_share(new, old):
	if new and 'univentionShare' in new.get('objectClass'):
		return True
	if old and 'univentionShare' in old.get('objectClass'):
		return True
	return False


def _is_quota_policy(new, old):
	if new and 'univentionPolicyShareUserQuota' in new.get('objectClass'):
		return True
	if old and 'univentionPolicyShareUserQuota' in old.get('objectClass'):
		return True
	return False


def _is_container(new, old):
	for oc in ['organizationalRole', 'organizationalUnit', 'univentionBase']:
		if new and oc in new.get('objectClass'):
			return True
		if old and oc in old.get('objectClass'):
			return True
	return False


def _get_ldap_connection():
	try:
		connection = univention.uldap.getMachineConnection(ldap_master=False)
	except ldap.SERVER_DOWN:
		connection = univention.uldap.getMachineConnection()

	return connection


def _is_container_change_relevant(new, old):
	try:
		new_reference = new.get('univentionPolicyReference', [])
	except AttributeError:
		new_reference = []

	try:
		old_reference = old.get('univentionPolicyReference', [])
	except AttributeError:
		old_reference = []

	if not old_reference and not new_reference:
		return False

	result = False

	lo = _get_ldap_connection()
	# Check if one policy is a quota policy
	for dn in old_reference + new_reference:
		ldap_object = lo.get(dn)
		# If the policy doesn't exist, we don't know if the policy was a quota policy
		if not ldap_object:
			result = True
			break
		if _is_quota_policy(ldap_object, None):
			result = True
			break
	lo.lo.unbind()

	return result


def _get_fqdn():
	return '%s.%s' % (listener.baseConfig['hostname'], listener.baseConfig['domainname'])


def _is_share_used_on_this_server(new, old):
	fqdn = _get_fqdn()
	if new and fqdn in new.get('univentionShareHost'):
		return True
	if old and fqdn in old.get('univentionShareHost'):
		return True
	return False


def _add_all_shares_below_this_container_to_dn_list(container_dn):
	lo = _get_ldap_connection()
	for dn, attr in lo.search(base=container_dn, filter='(&(objectClass=univentionShare)(univentionShareHost=%s))' % _get_fqdn(), attr=['dn']):
		_add_share_to_dn_list(dn)
	lo.lo.unbind()


def _add_share_to_dn_list(dn):
	ud.debug(ud.LISTENER, ud.INFO, 'Add %s to share list' % dn)
	filename = os.path.join(SHARE_CACHE_TODO_DIR, dn)
	# Create todo file
	open(filename, 'w').close()


def _get_all_quota_references(dn):
	references = []
	lo = _get_ldap_connection()
	for ddn, attr in lo.search(filter='(univentionPolicyReference=%s)' % dn):
		references.append((ddn, attr))
	lo.lo.unbind()
	return references


def handler(dn, new, old):

	ud.debug(ud.LISTENER, ud.INFO, 'Run handler for dn: %s' % dn)
	listener.setuid(0)
	try:
		if _is_share(new, old):
			ud.debug(ud.LISTENER, ud.INFO, '%s: is share' % dn)
			if _is_share_used_on_this_server(new, old):
				_add_share_to_dn_list(dn)
			ud.debug(ud.LISTENER, ud.INFO, '%s: is share (done)' % dn)

		elif _is_quota_policy(new, old):
			ud.debug(ud.LISTENER, ud.INFO, '%s: is quota policy' % dn)
			references = _get_all_quota_references(dn)
			if references:
				for ndn, attrs in references:
					ud.debug(ud.LISTENER, ud.INFO, '%s: recursion: %s' % (dn, ndn))
					handler(ndn, attrs, None)
			ud.debug(ud.LISTENER, ud.INFO, '%s: is quota policy (done)' % dn)

		elif _is_container(new, old):
			ud.debug(ud.LISTENER, ud.INFO, '%s: is container' % dn)
			if _is_container_change_relevant(new, old):
				_add_all_shares_below_this_container_to_dn_list(dn)
			ud.debug(ud.LISTENER, ud.INFO, '%s: is container (done)' % dn)

	finally:
		listener.unsetuid()


def clean():
	listener.setuid(0)
	try:
		if os.path.exists(SHARE_CACHE_DIR):
			for filename in os.listdir(SHARE_CACHE_DIR):
				if filename == 'todo':
					continue
				os.remove(os.path.join(SHARE_CACHE_DIR, filename))
		if os.path.exists(SHARE_CACHE_TODO_DIR):
			for filename in os.listdir(SHARE_CACHE_TODO_DIR):
				os.remove(os.path.join(SHARE_CACHE_TODO_DIR, filename))
	finally:
		listener.unsetuid()


def postrun():
	listener.setuid(0)
	lo = None
	try:
		for dn in os.listdir(SHARE_CACHE_TODO_DIR):
			filename = os.path.join(SHARE_CACHE_TODO_DIR, dn)
			if not lo:
				lo = _get_ldap_connection()
			attrs = lo.get(dn)
			ud.debug(ud.LISTENER, ud.INFO, '%s: attrs: %s' % (dn, attrs))

			if not attrs or not _get_fqdn() in attrs.get('univentionShareHost'):
				os.remove(filename)
				_remove_cache_for_share(dn)
				continue

			policy_result = univention.lib.policy_result.policy_result(dn)[0]
			ud.debug(ud.LISTENER, ud.INFO, '%s: policy_result: %s' % (dn, policy_result))
			_dump_share_and_policy_result(dn, attrs, policy_result)

			os.remove(filename)
		if lo:
			lo.lo.unbind()
	finally:
		listener.unsetuid()


def initialize():
	pass
