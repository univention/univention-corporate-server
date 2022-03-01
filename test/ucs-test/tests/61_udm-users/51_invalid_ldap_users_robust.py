#!/usr/share/ucs-test/runner pytest-3 -s
# -*- coding: utf-8 -*-
## desc: Test UDM cannot get broken by users with missing object classes
## exposure: dangerous
## roles: [domaincontroller_master]
## packages: [python3-univention-directory-manager]

import base64
import random
import traceback

import univention.admin.uexceptions

mapping = {
	'default': {
		'sn': 'foo',
		'cn': 'foo',
		'uid': '%(uid)s',
		'userPassword': base64.b64decode('e2NyeXB0fSQ2JDVZcjNsMGxReHN5d2Z1Ni8kQnR3bjRsL3BPcFNmUFJBYnllME1heTdWemVwUFFZRHJNWTBuUU1NZUhneHBmZUdybWJjVmdKaU1EY3hvQk0venRvZXFNWTlORWFoWUwybkwwMlVRWC4='),
		'objectClass': [b'person', b'univentionObject'],
		'univentionObjectType': 'users/user',
	},
	'person': {
		'title': 'foo',
		'objectClass': [b'inetOrgPerson', b'organizationalPerson'],
	},
	'posix': {
		'gidNumber': '5001',
		'homeDirectory': '/home/%(uid)s',
		'loginShell': '/bin/bash',
		'uidNumber': '%(rid)s',
		'objectClass': [b'posixAccount', b'shadowAccount'],
	},
	'samba': {
		'sambaAcctFlags': '[U          ]',
		'sambaBadPasswordCount': '0',
		'sambaBadPasswordTime': '0',
		'sambaNTPassword': 'CAA1239D44DA7EDF926BCE39F5C65D0F',
		'sambaPasswordHistory': 'F95F7674B861E4111BE93E107320D9D2C40973C67B4B710AFE8DC317047D7F10',
		'sambaPrimaryGroupSID': '%(sid)s-513',
		'sambaPwdLastSet': '1553939189',
		'sambaSID': '%(sid)s-%(rid)s',
		'objectClass': [b'sambaSamAccount'],
	},
	'kerberos': {
		'objectClass': [b'krb5KDCEntry', b'krb5Principal'],
		'krb5KDCFlags': '126',
		'krb5Key': base64.b64decode('MDGhEzARoAMCAQGhCgQI3IyR5c6FsymiGjAYoAMCAQOhEQQPREVWLkxPQ0FMZm9vYmFy'),
		'krb5KeyVersionNumber': '1',
		'krb5MaxLife': '86400',
		'krb5MaxRenew': '604800',
		'krb5PrincipalName': '%(uid)s@%(domain)s',
	},
	'mail': {
		'objectClass': [b'univentionMail'],
	}
}

constellations = [
	# ['person', 'posix', 'samba', 'kerberos'],
	['person', 'posix', 'samba', 'mail'],
	['person', 'posix', 'kerberos', 'mail'],
	['person', 'samba', 'kerberos', 'mail'],
	# ['posix', 'samba', 'kerberos', 'mail'],
]


def test_invalid_users_do_not_break_udm(random_username, lo, wait_for_replication, ucr, udm):
	dns = []
	sid = lo.getAttr(lo.binddn, 'sambaSID')[0].decode('ASCII').rsplit('-', 1)[0]
	rid = random.randint(2000, 3000)
	try:
		for options in constellations:
			uid = random_username()
			defaults = {
				'uid': uid,
				'sid': sid,
				'rid': rid,
				'domain': ucr['domainname'].upper(),
				'base': ucr['ldap/base'],
			}
			ocs = []
			al = []
			for option in options + ['default']:
				ocs.extend(mapping[option]['objectClass'])
				al.extend([(key, (val % defaults).encode('UTF-8')) for key, val in mapping[option].items() if key not in ['objectClass', 'userPassword', 'krb5Key']])
			al.append(('objectClass', ocs))
			dn = 'uid=%s,cn=users,%s' % (uid, ucr['ldap/base'])
			print('Adding', dn, 'with', options, 'and', al)
			lo.add(dn, al)
			dns.append(dn)

		wait_for_replication()

		users = dict(udm.list_objects('users/user'))
		assert users, 'No users exists'

		for dn in dns:
			assert dn not in users.keys(), 'Invalid object was detected'
			try:
				udm.verify_udm_object('users/user', dn, None)
			except univention.admin.uexceptions.wrongObjectType:
				print('dn', dn, 'correctly identified as wrong')

	finally:
		for dn in dns:
			try:
				lo.delete(dn)
			except Exception:
				print(traceback.format_exc())
