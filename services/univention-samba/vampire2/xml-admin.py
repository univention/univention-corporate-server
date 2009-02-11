#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Samba
#  takes over a Windows NT4 domain
#
# Copyright (C) 2004-2009 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
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

import os, getopt
import libxml2, sys
import codecs, copy
import time
import traceback
import univention.debug
import univention.config_registry

import univention.admin.uldap
import univention.admin.config
import univention.admin.modules
import univention.admin.objects
import univention.admin.allocators
import univention.admin.handlers.users.user
import univention.admin.handlers.groups.group
import univention.admin.handlers.computers.computer
import univention.admin.handlers.settings.sambadomain
import univention.admin.handlers.settings.sambaconfig


# global variables
lo=None
next_rid=0
builtin={}
domain={}
position=None

# update choices-lists which are defined in LDAP
univention.admin.syntax.update_choices()

def _debug_traceback(level, text):
	'''
	print traceback with univention.debug.debug, level is i.e. univention.debug.INFO
	'''
	exc_info = sys.exc_info()
	_d=univention.debug.function('_debug_traceback')
	lines = apply(traceback.format_exception, exc_info)
	text = text + '\n'
	for line in lines:
		text += line
	univention.debug.debug(univention.debug.MAIN, level , text)

# creates two data structures from the XML file: one holding the users
# and groups and the other one for builtin information
def __xml2dict(xmlfile, builtin, domain):
	doc = libxml2.parseFile(xmlfile)
	root = doc.children
	if root.name != "samba":
		univention.debug.debug(univention.debug.MAIN, univention.debug.ERROR, 'Error during xml parsing: root.name failed')
		sys.exit(1)

	child = root.children
	while child:
		if child.name == 'domain':
			domain_child=child.children
			while domain_child:
				if  domain_child.type == 'element':
					domain[domain_child.name]=[]
					domain_grandchild=domain_child.children
					while domain_grandchild:
						if domain_grandchild.type == 'element':
							domain_great_grandchild=domain_grandchild.children
							dict={}
							if domain_grandchild.prop('rid'):
								dict['rid']=domain_grandchild.prop('rid')
							while domain_great_grandchild:
								if domain_great_grandchild.type == 'element':
									if dict.has_key(domain_great_grandchild.name):
										dict[domain_great_grandchild.name].append(domain_great_grandchild.content)
									else:
										dict[domain_great_grandchild.name]=[domain_great_grandchild.content]

								domain_great_grandchild=domain_great_grandchild.next
							domain[domain_child.name].append(dict)

						domain_grandchild=domain_grandchild.next
				domain_child=domain_child.next
		if child.name == 'builtin':
			builtin_child=child.children
			while builtin_child:
				if  builtin_child.type == 'element':
					builtin[builtin_child.name]=[]
					builtin_grandchild=builtin_child.children
					while builtin_grandchild:
						if builtin_grandchild.type == 'element':
							builtin_great_grandchild=builtin_grandchild.children
							dict={}
							if builtin_grandchild.prop('rid'):
								dict['rid']=builtin_grandchild.prop('rid')
							while builtin_great_grandchild:
								if builtin_great_grandchild.type == 'element':
									if dict.has_key(builtin_great_grandchild.name):
										dict[builtin_great_grandchild.name].append(builtin_great_grandchild.content)
									else:
										dict[builtin_great_grandchild.name]=[builtin_great_grandchild.content]

								builtin_great_grandchild=builtin_great_grandchild.next
							builtin[builtin_child.name].append(dict)

						builtin_grandchild=builtin_grandchild.next
				builtin_child=builtin_child.next

		child=child.next

	doc.freeDoc()

	pass



# checks for old samba domain objects. If there is more than one ->exit

def __check_old_samba_object( ):
	result=lo.search(filter='(objectClass=sambaDomain)', scope='domain')
	if len(result) > 1:
		univention.debug.debug(univention.debug.MAIN, univention.debug.ERROR, 'Found more than on Samba Domain Object.')
		print 'ERROR: Found more than on Samba Domain Object.'
		for i in range(0,len(result)):
			dn, attrs=result[i]
			univention.debug.debug(univention.debug.MAIN, univention.debug.ERROR, ' \t-> %s (%s)' % (attrs['sambaDomainName'][0],dn))
		sys.exit(1)
	elif len(result) < 1:
		return None, None

	dn, attrs=result[0]
	return attrs['sambaDomainName'][0], attrs['sambaSID'][0]

def nt_password_to_arcfour_hmac_md5(nt_password):

	# all arcfour-hmac-md5 keys begin this way
	key='0\x1d\xa1\x1b0\x19\xa0\x03\x02\x01\x17\xa1\x12\x04\x10'

	for i in range(0, 16):
		o=nt_password[2*i:2*i+2]
		key+=chr(int(o, 16))
	return key

def lm_password_to_user_password(lm_password):
	return '{LANMAN}%s' % lm_password

# change the domain name and the SID
def __change_domain_object(old_domainname, old_domainsid, domainname, domainsid):
	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Old Samba Domainname = %s' % old_domainname)
	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'New Samba Domainname = %s' % domainname)
	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Old Samba SID = %s' % old_domainsid)
	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'New Samba SID = %s' % domainsid)

	result=lo.search(filter='(objectClass=sambaDomain)', scope='domain')
	if len(result) > 1:
		univention.debug.debug(univention.debug.MAIN, univention.debug.ERROR, 'Not setting new SID for domain object: %d objects found' % len(result))
		sys.exit(1)
	elif len(result) == 1:
		dn, attrs=result[0]

	if old_domainsid != domainsid and  domainname != old_domainname:
		if dn:
			lo.delete(dn)
		module=univention.admin.modules.get("settings/sambadomain")
		position.setDn('cn=samba,'+position.getBase())
		object=univention.admin.handlers.settings.sambadomain.object(None, lo, position=position)
		object.open()
		object['name']=domainname
		object['SID']=domainsid
		object.create()


def __change_sids(old_domainsid, domainsid):
	if old_domainsid == domainsid:
		univention.debug.debug(univention.debug.MAIN, univention.debug.INFO, 'old_domainsid and domainsid are the same')
		return
	for dn, attrs in lo.search(filter='(&(sambaSID=*)(objectClass=sambaIdmapEntry))', attr=['sambaSID']):
		if attrs.has_key('sambaSID') and attrs['sambaSID'][0].startswith(old_domainsid):
			oldval=attrs['sambaSID'][0]
			newval=oldval.replace(old_domainsid, domainsid)
			new_dn=dn.replace(oldval,newval)
			univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'DEBUG: Rename old=[%s] new=[%s]' % (repr(dn) , repr(new_dn)))
			lo.lo.rename(dn,new_dn)

	for dn, attrs in lo.search(filter='(|(sambaSID=*)(sambaPrimaryGroupSID=*))', attr=['sambaSID','sambaPrimaryGroupSID']):
		ml=[]
		if attrs.has_key('sambaPrimaryGroupSID') and attrs['sambaPrimaryGroupSID'][0].startswith(old_domainsid):
			oldval=attrs['sambaPrimaryGroupSID'][0]
			newval=oldval.replace(old_domainsid, domainsid)
			ml.append(('sambaPrimaryGroupSID', oldval, newval))
		if attrs.has_key('sambaSID') and attrs['sambaSID'][0].startswith(old_domainsid):
			oldval=attrs['sambaSID'][0]
			newval=oldval.replace(old_domainsid, domainsid)
			ml.append(('sambaSID', oldval, newval))
		if ml:
			univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'DEBUG: Changing SID in %s' % repr(dn))
			lo.modify(dn, ml)

def search_rid(domainsid, rid):
	result=lo.search(filter='sambaSID=%s-%s' % (domainsid, rid))
	univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, 'DEBUG: search_rid result=%s' % result)
	return result

def _create_group(position, xml_group):

	module=univention.admin.modules.get("groups/group")


	object=module.object(None, lo, position=position, superordinate=None)

	object.open()
	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Create Group "%s"' % codecs.latin_1_encode(xml_group['nt_groupname'])[0])
	univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, '\t name="%s"' % codecs.latin_1_encode(xml_group['nt_groupname'])[0])
	univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, '\t sambaRID="%s"' % codecs.latin_1_encode(xml_group['rid'])[0])
	univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, '\t description="%s"' % codecs.latin_1_encode(xml_group['acct_desc'])[0])

	object['name']=xml_group['nt_groupname']
	object['sambaRID']=xml_group['rid']
	object['description']=xml_group['acct_desc']

	dn=object.create()

	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Successful created group "%s"' % codecs.latin_1_encode(xml_group['nt_groupname'])[0])

def _modify_object(domainsid, dn, rid, description=None):

	ldap_object=lo.search(base=dn)

	ml=[]

	if ldap_object and ldap_object[0][1].has_key('objectClass') and 'posixGroup' in ldap_object[0][1]['objectClass']:
		if ldap_object[0][1].has_key('sambaSID'):
			group_members=lo.search(filter='sambaPrimaryGroupSID=%s' % (ldap_object[0][1]['sambaSID'][0]), attr=['uid', 'sambaPrimaryGroupSID'])
			for group_member in group_members:
				lo.modify(group_member[0], [('sambaPrimaryGroupSID', group_member[1]['sambaPrimaryGroupSID'], ['%s-%s' % (domainsid,rid)])])


		if not 'sambaGroupMapping' in ldap_object[0][1]['objectClass']:
			oc=copy.deepcopy(ldap_object[0][1]['objectClass'])
			oc.append('sambaGroupMapping')
			ml.append(('objectClass', ldap_object[0][1]['objectClass'], oc))
			#FIXME
			ml.append(('sambaGroupType', None, "2"))
			pass

	if rid:
		if ldap_object[0][1].has_key('sambaSID'):
			ml.append(('sambaSID', ldap_object[0][1]['sambaSID'], ['%s-%s' % (domainsid,rid)]))
		else:
			ml.append(('sambaSID', None, ['%s-%s' % (domainsid,rid)]))
	if description:
		if  ldap_object[0][1].has_key('description'):
			if codecs.latin_1_encode(ldap_object[0][1]['description'][0])[0] != codecs.latin_1_encode(description)[0]:
				ml.append(('description', ldap_object[0][1]['description'], description))
		else:
			ml.append(('description', None, description))
	if ml:
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Modify object: %s' % codecs.latin_1_encode(ldap_object[0][0])[0])
		lo.modify(ldap_object[0][0], ml)
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'done ')

def __modify_account_samba_settings(dn, xml_account, remove_user_password=1):

	ldap_object=lo.search(base=dn)

	ml=[]

	old=None
	if ldap_object[0][1].has_key('sambaNTPassword'):
		old=ldap_object[0][1]['sambaNTPassword']

	if xml_account.has_key('nt_password') and xml_account['nt_password'][0]:
		if old !=  xml_account['nt_password']:
			remove_user_password=1
		ml.append(('sambaNTPassword', old, xml_account['nt_password']))
	elif old:
		ml.append(('sambaNTPassword', old, None))

	old=None
	if ldap_object[0][1].has_key('sambaLMPassword'):
		old=ldap_object[0][1]['sambaLMPassword']

	if xml_account.has_key('lm_password') and xml_account['lm_password'][0]:
		ml.append(('sambaLMPassword', old, xml_account['lm_password']))
	elif old:
		ml.append(('sambaLMPassword', old, None))

	# delete the old user password if LM and NT password were set
	if remove_user_password:
		if ldap_object[0][1].has_key('userPassword'):
			if xml_account.has_key('lm_password'):
				ml.append(('userPassword', ldap_object[0][1]['userPassword'], [lm_password_to_user_password( xml_account['lm_password'][0])]))
			else:
				ml.append(('userPassword', ldap_object[0][1]['userPassword'], None))
		#kerberos now
		old=None
		if ldap_object[0][1].has_key('krb5Key'):
			old=ldap_object[0][1]['krb5Key']
		if xml_account.has_key('nt_password') and xml_account['nt_password']:
			ml.append(('krb5Key', old, [nt_password_to_arcfour_hmac_md5( xml_account['nt_password'][0])]))

	old=None
	if ldap_object[0][1].has_key('sambaBadPasswordCount'):
		old=ldap_object[0][1]['sambaBadPasswordCount']

	if xml_account.has_key('bad_pw_count') and xml_account['bad_pw_count'][0]:
		ml.append(('sambaBadPasswordCount', old, xml_account['bad_pw_count']))
	elif old:
		ml.append(('sambaBadPasswordCount', old, None))

	old=None
	if ldap_object[0][1].has_key('sambaPwdLastSet'):
		old=ldap_object[0][1]['sambaPwdLastSet']
	if xml_account.has_key('pwd_last_set') and xml_account['pwd_last_set'][0]:
		ml.append(('sambaPwdLastSet', old, xml_account['pwd_last_set']))
	elif old:
		ml.append(('sambaPwdLastSet', old, None))

	old=None
	if ldap_object[0][1].has_key('sambaMungedDial'):
		old=ldap_object[0][1]['sambaMungedDial']
	if xml_account.has_key('parameters') and xml_account['parameters'][0]:
		ml.append(('sambaMungedDial', old, xml_account['parameters']))
	elif old:
		ml.append(('sambaMungedDial', old, None))

	if ml:
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Modify DN=[%s]' % dn)
		lo.modify(dn, ml)

def create_account(domainsid, position, xml_account):

	module=univention.admin.modules.get("users/user")

	object=univention.admin.handlers.users.user.object(None, lo, position=position)

	object.open()

	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Create User "%s"' % codecs.latin_1_encode(xml_account['nt_username'][0])[0])

	object.set_uid_umlauts()
	object['username']=xml_account['nt_username'][0]
	object['sambaRID']=xml_account['rid']
	a,b=os.popen2('/usr/bin/makepasswd --minchars=8')
	line=b.readline()
	if line[-1] == '\n':
		line=line[0:-1]
	object['password']=line

	if xml_account.has_key('acct_desc'):
		object['description']=xml_account['acct_desc'][0]
	if xml_account.has_key('fullname') and xml_account['fullname'][0]:
		object['lastname']=xml_account['fullname'][0].replace( ':', ' ' )
	else:
		object['lastname']=xml_account['nt_username'][0]

	if xml_account.has_key('workstations'):
		object['sambaUserWorkstations']=xml_account['workstations'][0].split(',')
	if xml_account.has_key('profile_path'):
		object['profilepath']=xml_account['profile_path'][0]
	if xml_account.has_key('dir_drive'):
		object['homedrive']=xml_account['dir_drive'][0]
	if xml_account.has_key('logon_script'):
		object['scriptpath']=xml_account['logon_script'][0]
	if xml_account.has_key('home_dir'):
		object['sambahome']=xml_account['home_dir'][0]

	#primary group
	if xml_account.has_key('group_rid'):
		result=lo.search(filter='(&(sambaSID=%s-%s)(objectClass=posixGroup))' % (domainsid, xml_account['group_rid'][0]))
		if not result:
			object['primaryGroup']=univention.admin.config.getDefaultValue(lo, 'group')
		else:
			object['primaryGroup']=result[0][0]
	else:
		object['primaryGroup']=univention.admin.config.getDefaultValue(lo, 'group')

	if xml_account.has_key('acct_expiry_time') and xml_account['acct_expiry_time'][0] != "2147483647" and  xml_account['acct_expiry_time'][0] != "0":
		# 2147483647 -> account does not expire
		print 'set userexpiry'
		object['userexpiry']=time.strftime("%d.%m.%y",time.gmtime(long(xml_account['acct_expiry_time'][0])+(3600*24)))


	#define ACB_DISABLED   0x0001  /* 1 = User account disabled */
	#define ACB_HOMDIRREQ  0x0002  /* 1 = Home directory required */
	#define ACB_PWNOTREQ   0x0004  /* 1 = User password not required */
	#define ACB_TEMPDUP    0x0008  /* 1 = Temporary duplicate account */
	#define ACB_NORMAL     0x0010  /* 1 = Normal user account */
	#define ACB_MNS        0x0020  /* 1 = MNS logon user account */
	#define ACB_DOMTRUST   0x0040  /* 1 = Interdomain trust account */
	#define ACB_WSTRUST    0x0080  /* 1 = Workstation trust account */
	#define ACB_SVRTRUST   0x0100  /* 1 = Server trust account (BDC) */
	#define ACB_PWNOEXP    0x0200  /* 1 = User password does not expire */
	#define ACB_AUTOLOCK   0x0400  /* 1 = Account auto locked */
	if xml_account.has_key('acb_info'):
		acb_info=int(xml_account['acb_info'][0])
		if (acb_info & 1) == 1:
			object['disabled']="1"
		if (acb_info & 1024) == 1024:
			object['locked']="1"

	dn=object.create()

	__modify_account_samba_settings(dn, xml_account)


def utf8_modify(dict_old):
	dict_new={}
	for key in dict_old.keys():
		if type(dict_old[key]) == type([]):
			dict_new[key]=[]
			for k in dict_old[key]:
				dict_new[key].append(unicode(k, 'utf8'))
		else:
			dict_new[key]=dict_old[key]
	return dict_new



def sync_groups(domainname, domainsid):


	global position, lo
	global next_rid
	global builtin, domain

	# search all NT groups for a group with the same name in the LDAP directory
	baseConfig=univention.config_registry.baseConfig()
	baseConfig.load()

	if baseConfig.has_key('samba/defaultcontainer/group') and baseConfig['samba/defaultcontainer/group']:
		position.setDn(baseConfig['samba/defaultcontainer/group'])
	else:
		position.setDn(univention.admin.config.getDefaultContainer(lo, 'groups/group'))

	group_count=len(domain['groups'])

	for i in range(0, len(domain['groups'])):

		try:
			xml_group=domain['groups'][i]


			if xml_group.has_key('nt_groupname'):
				xml_group['nt_groupname']=unicode(xml_group['nt_groupname'][0], 'utf8')
				xml_group['acct_desc']=unicode(xml_group['acct_desc'][0], 'utf8')

			univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Checking Group [%d from %d] -> %s' % (i, group_count, xml_group['nt_groupname']))

			# does the name already exist in the LDAP directory?
			ldap_groups=univention.admin.handlers.groups.group.lookup(None, lo, filter_s='(cn=%s)' % xml_group['nt_groupname'], scope='domain', base=position.getDomain())
			if ldap_groups:
				ldap_group=ldap_groups[0]

				ldap_group.open()

				# hat diese LDAP Gruppe die Samba Objekte?
				if ldap_group.has_key('sambaRID'):
					# hat diese LDAP Gruppe die Samba Objekte? -> Ja

					# ist die RID im NT und im LDAP gleich?
					if ldap_group['sambaRID'] == xml_group['rid']:
						# ist die RID im NT und im LDAP gleich? -> Ja

						description=None
						if xml_group.has_key('acct_desc'):
							description=xml_group['acct_desc']

						_modify_object( domainsid, ldap_group.dn, None, description)
						pass
					else:
						# ist die RID im NT und im LDAP gleich? -> Nein
						univention.debug.debug(univention.debug.MAIN, univention.debug.INFO, 'DEBUG: rid change')
						result=search_rid( domainsid, xml_group['rid'])
						if not result:
							univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'DEBUG: change rid from %s' % ldap_group['name'])
							description=None
							if xml_group.has_key('acct_desc'):
								description=xml_group['acct_desc']

							_modify_object( domainsid, ldap_group.dn, xml_group['rid'], description)
						else:
							#die rid ist bereits vergeben
							univention.debug.debug(univention.debug.MAIN, univention.debug.INFO, ' rid used by %s' % result[0][0])
							next_rid=next_rid+1
							_modify_object( domainsid, result[0][0], next_rid, None)

							description=None
							if xml_group.has_key('acct_desc'):
								description=xml_group['acct_desc']

							_modify_object(domainsid, ldap_group.dn, xml_group['rid'], description)
						pass
				else:
					# hat diese LDAP Gruppe die Samba Objekte? -> Nein
					univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'found LDAP Group %s without rid' % (codecs.latin_1_encode(ldap_group['name'])[0]))
					description=None
					if xml_group.has_key('acct_desc'):
						description=xml_group['acct_desc']
					_modify_object(domainsid, ldap_group.dn, xml_group['rid'], description)
			else:
				# Ist der Gruppenname bereits im LDAP vorhanden? --> Nein

				#existiert eine Gruppe mit der RID?
				ldap_groups=univention.admin.handlers.groups.group.lookup(None, lo, filter_s='(sambaSID=%s-%s)' % (domainsid,xml_group['rid']), scope='domain', base=position.getDomain())
				if ldap_groups:
					next_rid=next_rid+1
					_modify_object(domainsid, ldap_groups[0].dn, str(next_rid), None)
					_create_group(position, xml_group)
				else:
					_create_group(position, xml_group)
		except:
			_debug_traceback(univention.debug.ERROR, 'Unknown exception during group sync' )

	pass

def __get_max_rid():
	'''
	searches max rid from xmlfile and from LDAP
	'''

	max_rid=0

	# die hoechste RID aus dem XML suchen
	for i in range(0, len(domain['groups'])):
		group=domain['groups'][i]
		if group.has_key('rid'):
			if int(group['rid']) > max_rid:
				max_rid=int(group['rid'])

	for i in range(0, len(domain['accounts'])):
		account=domain['accounts'][i]
		if account.has_key('rid'):
			if int(account['rid']) > max_rid:
				max_rid=int(account['rid'])


	# die hoechste RID aus dem LDAP suchen
	result=lo.search(filter='(&(sambaSID=*)(!(objectClass=sambaDomain)))', attr=['sambaSID'])
	for i in range(0,len(result)):
		dn, attr=result[i]
		if attr.has_key('sambaSID'):
			if int(attr['sambaSID'][0].split('-')[-1]) > max_rid:
				max_rid=int(attr['sambaSID'][0].split('-')[-1])

	univention.debug.debug(univention.debug.MAIN, univention.debug.INFO, 'DEBUG: Found max RID = %d' % max_rid)

	return max_rid

def __added_samba_objects_to_user(domainsid, ldap_user, xml_account):
	ml=[]

	ml.append(('sambaSID', None, '%s-%s' % (domainsid, xml_account['rid'])))
	ocs=ldap_user.oldattr.get('objectClass', [])
	ml.append(('objectClass', ocs, ocs+['sambaSamAccount']))

	if ml:
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Modify DN=[%s]' % ldap_user.dn)
		lo.modify(ldap_user.dn, ml)

def __modify_account(domainsid, ldap_user,xml_account):

	if xml_account.has_key('acct_desc'):
		ldap_user['description']=xml_account['acct_desc'][0]

	if xml_account.has_key('fullname') and xml_account['fullname'][0]:
		ldap_user['lastname']=xml_account['fullname'][0]
	else:
		ldap_user['lastname']=xml_account['nt_username'][0]

	if xml_account.has_key('workstations'):
		ldap_user['sambaUserWorkstations']=xml_account['workstations'][0].split(',')
	if xml_account.has_key('profile_path'):
		ldap_user['profilepath']=xml_account['profile_path'][0]
	if xml_account.has_key('dir_drive'):
		ldap_user['homedrive']=xml_account['dir_drive'][0]
	if xml_account.has_key('logon_script'):
		ldap_user['scriptpath']=xml_account['logon_script'][0]
	if xml_account.has_key('home_dir'):
		ldap_user['sambahome']=xml_account['home_dir'][0]

	#primary group
	if xml_account.has_key('group_rid'):
		result=lo.search(filter='(&(sambaSID=%s-%s)(objectClass=posixGroup))' % (domainsid, xml_account['group_rid'][0]))
		if not result:
			ldap_user['primaryGroup']=univention.admin.config.getDefaultValue(lo, 'group')
		else:
			ldap_user['primaryGroup']=result[0][0]
	else:
		ldap_user['primaryGroup']=univention.admin.config.getDefaultValue(lo, 'group')

	if xml_account.has_key('acct_expiry_time') and xml_account['acct_expiry_time'][0] != "2147483647" and  xml_account['acct_expiry_time'][0] != "0":
		# 2147483647 scheint zu bedeuten, das das Konto nicht abläuft
		print 'set userexpiry'
		ldap_user['userexpiry']=time.strftime("%d.%m.%y",time.gmtime(long(xml_account['acct_expiry_time'][0])+(3600*24)))


	#define ACB_DISABLED   0x0001  /* 1 = User account disabled */
	#define ACB_HOMDIRREQ  0x0002  /* 1 = Home directory required */
	#define ACB_PWNOTREQ   0x0004  /* 1 = User password not required */
	#define ACB_TEMPDUP    0x0008  /* 1 = Temporary duplicate account */
	#define ACB_NORMAL     0x0010  /* 1 = Normal user account */
	#define ACB_MNS        0x0020  /* 1 = MNS logon user account */
	#define ACB_DOMTRUST   0x0040  /* 1 = Interdomain trust account */
	#define ACB_WSTRUST    0x0080  /* 1 = Workstation trust account */
	#define ACB_SVRTRUST   0x0100  /* 1 = Server trust account (BDC) */
	#define ACB_PWNOEXP    0x0200  /* 1 = User password does not expire */
	#define ACB_AUTOLOCK   0x0400  /* 1 = Account auto locked */
	if xml_account.has_key('acb_info'):
		acb_info=int(xml_account['acb_info'][0])
		if (acb_info & 1) == 1:
			ldap_user['disabled']="1"
		if (acb_info & 1024) == 1024:
			ldap_user['locked']="1"

	ldap_user.modify()

	__modify_account_samba_settings(ldap_user.dn, xml_account, remove_user_password=0)

	pass

def __modify_workstation_samba_settings(domainsid, dn, xml_account):

	ldap_object=lo.search(base=dn)

	#jetzt werden noch die Attribute geändert, die nicht im Admin sind
	ml=[]

	old=None
	if ldap_object[0][1].has_key('sambaSID'):
		old=ldap_object[0][1]['sambaSID']
	ml.append(('sambaSID', old, '%s-%s' % (domainsid, xml_account['rid'])))

	ocs=ldap_object[0][1]['objectClass']
	if not 'sambaSamAccount' in ocs:
		ml.append(('objectClass', ocs, ocs+['sambaSamAccount']))

	if not ldap_object[0][1].has_key('sambaAcctFlags'):
		acctFlags=univention.admin.samba.acctFlags(flags={'W':1})
		ml.append(('sambaAcctFlags', None, [acctFlags.decode()]))

	old=None
	if ldap_object[0][1].has_key('sambaNTPassword'):
		old=ldap_object[0][1]['sambaNTPassword']

	if xml_account.has_key('nt_password') and xml_account['nt_password'][0]:
		ml.append(('sambaNTPassword', old, xml_account['nt_password']))
	elif old:
		ml.append(('sambaNTPassword', old, None))

	old=None
	if ldap_object[0][1].has_key('sambaLMPassword'):
		old=ldap_object[0][1]['sambaLMPassword']

	if xml_account.has_key('lm_password') and xml_account['lm_password'][0]:
		ml.append(('sambaLMPassword', old, xml_account['lm_password']))
	elif old:
		ml.append(('sambaLMPassword', old, None))

	old=None
	if ldap_object[0][1].has_key('sambaBadPasswordCount'):
		old=ldap_object[0][1]['sambaBadPasswordCount']

	if xml_account.has_key('bad_pw_count') and xml_account['bad_pw_count'][0]:
		ml.append(('sambaBadPasswordCount', old, xml_account['bad_pw_count']))
	elif old:
		ml.append(('sambaBadPasswordCount', old, None))

	old=None
	if ldap_object[0][1].has_key('sambaPwdLastSet'):
		old=ldap_object[0][1]['sambaPwdLastSet']
	if xml_account.has_key('pwd_last_set') and xml_account['pwd_last_set'][0]:
		ml.append(('sambaPwdLastSet', old, xml_account['pwd_last_set']))
	elif old:
		ml.append(('sambaPwdLastSet', old, None))

	old=None
	if ldap_object[0][1].has_key('sambaMungedDial'):
		old=ldap_object[0][1]['sambaMungedDial']
	if xml_account.has_key('parameters') and xml_account['parameters'][0]:
		ml.append(('sambaMungedDial', old, xml_account['parameters']))
	elif old:
		ml.append(('sambaMungedDial', old, None))

	if ml:
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Modify DN=[%s]' % dn)
		lo.modify(dn, ml)

	pass

def __create_workstation(domainsid, position, xml_account):

	module=univention.admin.modules.get("computers/windows")

	object=univention.admin.handlers.computers.windows.object(None, lo, position=position)

	object.open()
	object.options.remove('samba')

	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Create Workstation "%s"' % codecs.latin_1_encode(xml_account['nt_username'][0])[0])

	object.set_name_umlauts()
	object['name']=xml_account['nt_username'][0].strip('$')
	dn=object.create()

	__modify_workstation_samba_settings(domainsid, dn, xml_account)


	pass

def sync_workstation(domainname, domainsid, xml_account):
	global next_rid
	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Checking workstation: %s' % xml_account['nt_username'][0])

	# Ist der Computername bereits im LDAP vorhanden?
	ldap_account=univention.admin.handlers.computers.windows.lookup(None, lo, filter_s='(uid=%s)' % xml_account['nt_username'][0], scope='domain', base=position.getDomain())

	# ist dieser Computer bereits als Benutzer in UCS angelegt?
	if not ldap_account:
		ldap_users=univention.admin.handlers.users.user.lookup(None, lo, filter_s='(uid=%s)' % xml_account['nt_username'][0], scope='domain', base=position.getDomain())
		if ldap_users:
			univention.debug.debug(univention.debug.MAIN, univention.debug.ERROR, 'Workstation trust account exists as user account')
			return

	if ldap_account:
		# Ist der Computername bereits im LDAP vorhanden? --> Ja
		ldap_account=ldap_account[0]

		ldap_account.open()

		# hat dieser LDAP Rechner die Samba Objekte?
		if ldap_account.oldattr.get('sambaSID', []):
			# hat dieser LDAP Rechner die Samba Objekte? -> Ja

			# ist die RID im NT und im LDAP gleich?
			if ldap_account.oldattr.get('sambaSID',[''])[0] == xml_account['rid']:
				# ist die RID im NT und im LDAP gleich? -> Ja
				univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, 'DEBUG: modify_workstation')
				__modify_workstation_samba_settings(domainsid, ldap_account.dn, xml_account)
				pass
			else:
				# ist die RID im NT und im LDAP gleich? -> Nein
				univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, 'DEBUG: rid change')
				result=search_rid( domainsid, xml_account['rid'])
				if not result:
					univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, 'DEBUG: we must change rid from %s' % codecs.latin_1_encode(ldap_account['name'])[0])
					__modify_workstation_samba_settings(domainsid, ldap_account.dn, xml_account)
				else:
					next_rid=next_rid+1
					_modify_object( domainsid, result[0][0], next_rid, None)
					__modify_workstation_samba_settings(domainsid, ldap_account.dn, xml_account)
				pass
		else:
			# hat dieser LDAP Account die Samba Objekte? -> Nein
			univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, 'DEBUG: found LDAP Account %s without rid' % (codecs.latin_1_encode(ldap_account['name'])[0]))
			__modify_workstation_samba_settings(domainsid, ldap_account.dn, xml_account)
	else:
		# Ist der Computername bereits im LDAP vorhanden? --> Nein

		#existiert ein Benutzer mit der RID?
		ldap_account=univention.admin.handlers.users.user.lookup(None, lo, filter_s='(sambaSID=%s-%s)' % (domainsid,xml_account['rid']), scope='domain', base=position.getDomain())
		if not ldap_account:
			ldap_account=univention.admin.handlers.computers.computer.lookup(None, lo, filter_s='(sambaSID=%s-%s)' % (domainsid,xml_account['rid']), scope='domain', base=position.getDomain())
		if not ldap_account:
			ldap_account=univention.admin.handlers.groups.group.lookup(None, lo, filter_s='(sambaSID=%s-%s)' % (domainsid,xml_account['rid']), scope='domain', base=position.getDomain())
		if ldap_users:
			univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, 'DEBUG: Computer nicht, aber RID im LDAP vorhanden')
			next_rid=next_rid+1
			_modify_object( domainsid, ldap_account[0].dn, str(next_rid), None)
			__create_workstation( domainsid, position, xml_account )
		else:
			univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, 'DEBUG: Rechner und RID nicht im LDAP vorhanden')
			__create_workstation( domainsid, position, xml_account )
			pass

def sync_user(domainname, domainsid, xml_account):

	global next_rid

	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Checking account: %s' % xml_account['nt_username'][0])


	# Ist der Benutzername bereits im LDAP vorhanden?
	ldap_users=univention.admin.handlers.users.user.lookup(None, lo, filter_s='(uid=%s)' % xml_account['nt_username'][0], scope='domain', base=position.getDomain())

	# ist dieser Benutzer evtl. bereits als Rechner in UCS angelegt?
	if not ldap_users:
		ldap_users=univention.admin.handlers.computers.computer.lookup(None, lo, filter_s='(uid=%s)' % xml_account['nt_username'][0], scope='domain', base=position.getDomain())
		if ldap_users:
			univention.debug.debug(univention.debug.MAIN, univention.debug.ERROR, 'User exists as computer account')
			return

	if ldap_users:
		# Ist der Benutzername bereits im LDAP vorhanden? --> Ja
		univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, 'DEBUG: Benutzer im LDAP vorhanden')

		# wir verwenden zunächst nur den ersten Benutzer, es darf ja auch nicht mehr geben
		ldap_user=ldap_users[0]

		ldap_user.open()

		# hat dieser LDAP Benutzer die Samba Objekte?
		if ldap_user.has_key('sambaRID'):
			# hat dieser LDAP Benutzer die Samba Objekte? -> Ja

			# ist die RID im NT und im LDAP gleich?
			if ldap_user['sambaRID'] == xml_account['rid']:
				# ist die RID im NT und im LDAP gleich? -> Ja
				univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, 'DEBUG: modify_account')
				__modify_account(domainsid, ldap_user,xml_account)
				pass
			else:
				# ist die RID im NT und im LDAP gleich? -> Nein
				univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, 'DEBUG: rid change')
				result=search_rid( domainsid, xml_account['rid'])
				if not result:
					univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, 'DEBUG: we must change rid from %s' % (codecs.latin_1_encode(ldap_user['username'])[0]))
					#description=None
					#if xml_group.has_key('acct_desc'):
					#	description=xml_group['acct_desc']

					_modify_object(domainsid, ldap_user.dn, xml_account['rid'], None)
					__modify_account(domainsid, ldap_user,xml_account)
				pass
		else:
			# hat dieser LDAP Benutzer die Samba Objekte? -> Nein
			univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, 'DEBUG: found LDAP User %s without rid' % (codecs.latin_1_encode(ldap_user['username'])[0]))
			__added_samba_objects_to_user(domainsid, ldap_user, xml_account)
			__modify_account(domainsid, ldap_user,xml_account)
	else:
		# Ist der Benutzername bereits im LDAP vorhanden? --> Nein

		#existiert ein Benutzer mit der RID?
		ldap_users=univention.admin.handlers.users.user.lookup(None, lo, filter_s='(sambaSID=%s-%s)' % (domainsid,xml_account['rid']), scope='domain', base=position.getDomain())
		if ldap_users:
			univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, 'DEBUG: Benutzer nicht, aber RID im LDAP vorhanden')
			next_rid=next_rid+1
			_modify_object( domainsid, ldap_users[0].dn, str(next_rid), None)
			create_account( domainsid, position, xml_account )
		else:
			univention.debug.debug(univention.debug.MAIN, univention.debug.ALL, 'DEBUG: Benutzer und RID nicht im LDAP vorhanden')
			create_account( domainsid, position, xml_account )
			pass

def sync_accounts(domainname, domainsid):
	baseConfig=univention.config_registry.baseConfig()
	baseConfig.load()

	if baseConfig.has_key('samba/defaultcontainer/user') and baseConfig['samba/defaultcontainer/user']:
		user_position=baseConfig['samba/defaultcontainer/user']
	else:
		user_position=univention.admin.config.getDefaultContainer(lo, 'users/user')

	if baseConfig.has_key('samba/defaultcontainer/computers') and baseConfig['samba/defaultcontainer/computer']:
		workstation_position=baseConfig['samba/defaultcontainer/computer']
	else:
		workstation_position=univention.admin.config.getDefaultContainer(lo, 'computers/windows')

	# Accounts
	for i in range(0, len(domain['accounts'])):
		try:
			xml_account=utf8_modify(domain['accounts'][i])
			if xml_account.has_key('acb_info') and xml_account['acb_info'][0]:

				if (int(xml_account['acb_info'][0]) & 16) == 16:
					univention.debug.debug(univention.debug.MAIN, univention.debug.WARN, 'Processing normal user account: %s' % xml_account['nt_username'][0])
					position.setDn(user_position)
					sync_user(domainname, domainsid, xml_account)

				elif (int(xml_account['acb_info'][0]) & 64) == 64:
					univention.debug.debug(univention.debug.MAIN, univention.debug.WARN, 'Ignore interdomain trust account; name=[%s]' % xml_account['nt_username'][0])

				elif (int(xml_account['acb_info'][0]) & 128) == 128:
					univention.debug.debug(univention.debug.MAIN, univention.debug.WARN, 'Processing workstation trust account; name=[%s]' % xml_account['nt_username'][0])
					position.setDn(workstation_position)
					sync_workstation(domainname, domainsid, xml_account)

				elif (int(xml_account['acb_info'][0]) & 256) == 256:
					univention.debug.debug(univention.debug.MAIN, univention.debug.WARN, 'Ignore server trust account (BDC); name=[%s]' % xml_account['nt_username'][0])

				else:
					univention.debug.debug(univention.debug.MAIN, univention.debug.WARN, 'Ignore unknown account' % xml_account['nt_username'][0])

		except:
			_debug_traceback(univention.debug.ERROR, 'Unknown exception during account sync' )
			try:
				print 'WARNING: failed to sync account [%s]' % codecs.latin_1_encode(xml_account['nt_username'][0])[0]
			except:
				print 'WARNING: failed to sync account one account, check logfile'


def sync_groupmembership(domainname, domainsid):
	for i in range(0, len(domain['groups'])):
		try:
			# Pointer zur aktuellen Gruppe
			xml_group=domain['groups'][i]

			univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Checking Group Membership for %s' % (xml_group['nt_groupname']))

			if xml_group.has_key('member_rid'):
				ldap_groups=univention.admin.handlers.groups.group.lookup(None, lo, filter_s='(cn=%s)' % (xml_group['nt_groupname']), scope='domain', base=position.getDomain())
				ldap_group=ldap_groups[0]
				ldap_group.open()
				member=[]
				for j in range(0, len(xml_group['member_rid'])):
					ldap_object=lo.search(filter='sambaSID=%s-%s' % (domainsid, xml_group['member_rid'][j]), attr=['uid'])
					if ldap_object and ldap_object[0][1].has_key('uid') and len(ldap_object[0][0]) > 0:
						member.append(ldap_object[0][0])
				if member:

					# wenn die Gruppe noch keine Mitglieder hat, dann existiert eine Liste mit einem leeren Eintrag
					if (len(ldap_group['users']) == 1 and ldap_group['users'][0] == '') or ldap_group['users'] < 1:
						ldap_group['users']=member
					else:
						for m in member:
							if m not in ldap_group['users']:
								ldap_group['users'].append(m)
					ldap_group.modify()

		except:
			_debug_traceback(univention.debug.ERROR, 'Unknown exception during groupmembership sync' )

	pass

def __samba_config_object(globals):
	global position

	samba_config=univention.admin.handlers.settings.sambaconfig.lookup(None, lo, filter_s='(name=%s)' % (globals['domain_name'][0]), scope='domain', base=position.getDomain())
	if samba_config:
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Modify Samba Config Object')
		samba_config=samba_config[0]
		samba_config.open()
		create=None
	else:
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'Create Samba Config Object')
		module=univention.admin.modules.get("settings/sambaconfig")

		position.setDn('cn=samba,%s' % position.getDomain())
		samba_config=univention.admin.handlers.settings.sambaconfig.object(None, lo, position=position)
		samba_config.open()
		samba_config['name']=globals['domain_name'][0]
		create=1


	if globals.has_key('max_pwd_age'):
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'max_pwd_age=%s' % globals['max_pwd_age'][0])
		samba_config['maxPasswordAge']=globals['max_pwd_age'][0]
	elif samba_config.has_key('maxPasswordAge'):
		samba_config['maxPasswordAge']=None

	if globals.has_key('min_pwd_age'):
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'min_pwd_age=%s' % globals['min_pwd_age'][0])
		samba_config['minPasswordAge']=globals['min_pwd_age'][0]
	elif samba_config.has_key('minPasswordAge'):
		samba_config['minPasswordAge']=None

	if globals.has_key('force_logoff'):
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'force_logoff=%s' % globals['force_logoff'][0])
		samba_config['disconnectTime']=globals['force_logoff'][0]
	elif samba_config.has_key('disconnectTime'):
		samba_config['disconnectTime']=None

	if globals.has_key('lockout_reset'):
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'lockout_reset=%s' % globals['lockout_reset'][0])
		samba_config['resetCountMinutes']=str(int(globals['lockout_reset'][0])/60)
	elif samba_config.has_key('resetCountMinutes'):
		samba_config['resetCountMinutes']=None

	if globals.has_key('lockout_duration'):
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'lockout_duration=%s' % globals['lockout_duration'][0])
		samba_config['lockoutDuration']=globals['lockout_duration'][0]
	elif samba_config.has_key('lockoutDuration'):
		samba_config['lockoutDuration']=None

	if globals.has_key('pwd_history_len'):
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'pwd_history_len=%s' % globals['pwd_history_len'][0])
		samba_config['passwordHistory']=globals['pwd_history_len'][0]
	elif samba_config.has_key('passwordHistory'):
		samba_config['passwordHistory']=None

	if globals.has_key('min_pwd_len'):
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'min_pwd_len=%s' % globals['min_pwd_len'][0])
		samba_config['passwordLength']=globals['min_pwd_len'][0]
	elif samba_config.has_key('passwordLength'):
		samba_config['passwordLength']=None

	if globals.has_key('bad_attempt_lockout'):
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'bad_attempt_lockout=%s' % globals['bad_attempt_lockout'][0])
		samba_config['badLockoutAttempts']=globals['bad_attempt_lockout'][0]
	elif samba_config.has_key('badLockoutAttempts'):
		samba_config['badLockoutAttempts']=None

	if globals.has_key('logon_chgpass'):
		val = "0"
		if(globals['logon_chgpass'][0]=="2"):
			val = "1"
		univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS, 'logon_chgpass=%s' % globals['logon_chgpass'][0])
		samba_config['logonToChangePW']=val
	elif samba_config.has_key('logonToChangePW'):
		samba_config['logonToChangePW']=None

	if create:
		samba_config.create()
	else:
		samba_config.modify()


	pass



# main

def main():

	xmlfile=None
	global lo
	global next_rid
	global builtin
	global domain
	global position



	# parse command line arguments
	opts, args = getopt.getopt(sys.argv[1:], 'f:')
	for opt, val in opts:
		if opt == '-f':
			xmlfile=val


	if not xmlfile:
		print 'ERROR: Missing -f <xmlfile>'
		sys.exit(1)

	__xml2dict(xmlfile, builtin, domain)

	univention.debug.init('/var/log/univention/pdc-takeover.log', 1, 0)
	univention.debug.set_level(univention.debug.MAIN, univention.debug.ALL)

	lo, position = univention.admin.uldap.getAdminConnection(decode_ignorelist=['krb5Key'])

	baseConfig=univention.config_registry.baseConfig()
	baseConfig.load()

	if baseConfig.has_key('samba/defaultcontainer/user') and baseConfig['samba/defaultcontainer/user']:
		try:
			lo.searchDn(base=baseConfig['samba/defaultcontainer/user'])
		except univention.admin.uexceptions.noObject:
			univention.debug.debug(univention.debug.MAIN, univention.debug.ERROR,  'Check baseconfig variable samba/defaultcontainer/user')
			sys.exit(1)

	if baseConfig.has_key('samba/defaultcontainer/group') and baseConfig['samba/defaultcontainer/group']:
		try:
			lo.searchDn(base=baseConfig['samba/defaultcontainer/group'])
		except univention.admin.uexceptions.noObject:
			univention.debug.debug(univention.debug.MAIN, univention.debug.ERROR,  'Check baseconfig variable samba/defaultcontainer/group')
			sys.exit(1)

	if baseConfig.has_key('samba/defaultcontainer/computer') and baseConfig['samba/defaultcontainer/computer']:
		try:
			lo.searchDn(base=baseConfig['samba/defaultcontainer/computer'])
		except univention.admin.uexceptions.noObject:
			univention.debug.debug(univention.debug.MAIN, univention.debug.ERROR,  'Check baseconfig variable samba/defaultcontainer/computer')
			sys.exit(1)

	domainname=domain['globals'][0]['domain_name'][0]
	domainsid=domain['globals'][0]['domain_sid'][0]

	old_domainname, old_domainsid = __check_old_samba_object()
	__change_domain_object( old_domainname, old_domainsid, domainname, domainsid)
	__change_sids(old_domainsid, domainsid)

	# Samba Config Object
	__samba_config_object(domain['globals'][0])



	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS,  'Found %d accounts' % len(domain['accounts']))
	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS,  'Found %d groups' % len(domain['groups']))

	next_rid=__get_max_rid()+1

	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS,  'Sync groups')
	sync_groups(domainname, domainsid)
	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS,  'Sync accounts')
	sync_accounts(domainname, domainsid)
	univention.debug.debug(univention.debug.MAIN, univention.debug.PROCESS,  'Sync groupmembership')
	sync_groupmembership(domainname, domainsid)

	univention.debug.debug(univention.debug.MAIN, univention.debug.INFO, 'max rid=%d' % next_rid)

	pass



try:
	main()
except KeyboardInterrupt:
	pass
