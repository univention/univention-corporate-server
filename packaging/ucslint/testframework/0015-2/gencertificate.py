# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2004-2019 Univention GmbH

from listener import *

import univention.debug
import univention.misc

name='gencertificate'
description='Generate new Certificates'
filter='(|(objectClass=univentionDomainController)(objectClass=univentionClient)(objectClass=univentionMobileClient)(objectClass=univentionMemberServer))'
attributes=[]


uidNumber = 0
gidNumber = 0
saved_uid = 65545

def set_privileges_cert(root=0):
	global saved_uid
	if root:
		saved_uid=os.geteuid()
		os.seteuid(0)
	else:
		os.seteuid(saved_uid)

def initialize():
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'CERTIFICATE: Initialize' )
	return

def handler(dn, new, old):
	set_privileges_cert(root=1)

	if baseConfig['server/role'] != 'domaincontroller_master':
		set_privileges_cert(root=0)
		return

	try:
		if new and not old:
			if new.has_key('associatedDomain'):
				domain=new['associatedDomain'][0]
			else:
				domain=baseConfig['domainname']
			create_certificate(new['cn'][0], int(new['uidNumber'][0]), domainname=domain)
		elif old and not new:
			if old.has_key('associatedDomain'):
				domain=old['associatedDomain'][0]
			else:
				domain=baseConfig['domainname']
			remove_certificate(old['cn'][0], domainname=domain)
		else:
			if old.has_key('associatedDomain'):
				old_domain=old['associatedDomain'][0]
			else:
				old_domain=baseConfig['domainname']

			if new.has_key('associatedDomain'):
				new_domain=new['associatedDomain'][0]
			else:
				new_domain=baseConfig['domainname']

			if new_domain != old_domain:
				remove_certificate(old['cn'][0], domainname=old_domain)
				create_certificate(new['cn'][0], int(new['uidNumber'][0]), domainname=new_domain)
	finally:
		set_privileges_cert(root=0)
	return

def set_permissions(tmp1, directory, filename):
	global uidNumber
	global gidNumber

	univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'CERTIFICATE: Set permissions for = %s with owner/group %s/%s' % (directory, gidNumber, uidNumber))
	os.chown(directory, uidNumber, gidNumber)
	os.chmod(directory, 0750)

	for f in filename:
		file=os.path.join(directory,f)
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'CERTIFICATE: Set permissions for = %s with owner/group %s/%s' % (file, gidNumber, uidNumber))
		os.chown(file, uidNumber, gidNumber)
		os.chmod(file, 0750)

def remove_dir(tmp1, directory, filename):
	for f in filename:
		file=os.path.join(directory,f)
		os.remove(file)
	os.rmdir(directory)

def create_certificate(name, serverUidNumber, domainname):
	global uidNumber
	global gidNumber
	uidNumber = serverUidNumber

	ssldir='/etc/univention/ssl'
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'CERTIFICATE: Creating certificate %s' % name)

	certpath=os.path.join(ssldir,name+'.'+domainname)
	if os.path.exists(certpath):
		univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'CERTIFICATE: Certificate for host %s.%s already exists' % (name,domainname))
		return

	try:
		gidNumber = int(pwd.getpwnam('%s$' % (name) )[3])
	except:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'CERTIFICATE: Failed to get groupID for "%s"' % name)
		gidNumber = 0

	if len("%s.%s" % (name,domainname)) > 64:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'CERTIFICATE: can\'t create certificate, Common Name too long: %s.%s' % (name,domainname))
		return

	p = os.popen('source /usr/share/univention-ssl/make-certificates.sh; gencert %s.%s %s.%s' % (name,domainname,name,domainname) )
	p.close()
	p = os.popen('ln -sf %s/%s.%s %s/%s' % (ssldir,name,domainname,ssldir,name) )
	p.close()


	a=os.path.walk(certpath,set_permissions, None)

	return

def remove_certificate(name, domainname):

	ssldir='/etc/univention/ssl'

	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'CERTIFICATE: Revoke certificate %s.%s' % (name,domainname))
	p = os.popen('/usr/sbin/univention-certificate revoke -name %s.%s' % (name,domainname) )
	p.close()

	link_path=os.path.join(ssldir,name)
	if os.path.exists(link_path):
		os.remove(link_path)

	certpath=os.path.join(ssldir,"%s.%s" % (name,domainname))
	if os.path.exists(certpath):
		a=os.path.walk(certpath,remove_dir, None)

	return

def clean():
	return

def postrun():
	return

