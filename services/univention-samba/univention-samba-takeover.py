#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Samba
#  takes over another samba domain
#
# Copyright (C) 2006-2009 Univention GmbH
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

import getopt, sys, os, time, ldap, re, string, array
import univention.config_registry
import univention.debug
import univention.admin.uldap
import univention.admin.config
import univention.admin.modules
import univention.admin.allocators
from random import randint

current_account = 0
machines = {}		# machine accounts
users = {}			# user accounts
groups = {}			# groupnames, index is the group name
gname_by_gid = {}

oldSID = ""
newSID = ""
windom = ""
pdbdumpfile = ""
sidfile = ""
smbpasswdfile = ""
serverDN = ""
userbase = ""
computerbase = ""
groupbase = ""
passwdfile = ""
groupfile = ""
groupmapfile = ""

def getCommandOutput(command):
	child = os.popen(command)
	data = child.read()
	err = child.close()
	if err:
		raise RuntimeError, '%s failed with exit code %d' % (command, err)
	return data

# Default disclaimer...
help = """import_samba_accounts [options]
options:
	--sid <new SID>
	--smbpasswdfile <file>
	--pdbdump <file>
	--serverDN <LDAP server base dn>
	--userbase <LDAP user container dn>
	--computerbase <LDAP computer container dn>
	--passwdfile <filename of /etc/passwd>
	--groupfile <filename of /etc/group>
	--groupmapfile <filename of group mappings>
"""

try:
	opts, args = getopt.getopt(sys.argv[1:], [], ["sid=", "smbpasswdfile=", "pdbdump=","serverDN=", "userbase=", "passwdfile=", "groupmapfile=","groupfile=","computerbase=" ])
except getopt.GetoptError:
	print help
	sys.exit()

for o, v in opts:
	if o in "--smbpasswdfile":
		smbpasswdfile = v
	elif o in "--sid":
		sidfile = v
	elif o in "--pdbdump":
		pdbdumpfile = v
	elif o in "--serverDN":
		serverDN = v
	elif o in "--userbase":
		userbase = v
	elif o in "--computerbase":
		computerbase = v
	elif o in "--groupbase":
		groupbase = v
	elif o in "--passwdfile":
		passwdfile = v
	elif o in "--groupfile":
		groupfile = v
	elif o in "--groupmapfile":
		groupmapfile = v
	else:
		print  help


if pdbdumpfile == "":
	print "No PDB dump specified. Exiting..."
	print help
	sys.exit()

if passwdfile == "":
	print "No path to passwd file specified. Exiting..."
	print help
	sys.exit()

if smbpasswdfile == "":
	print "No path to smbpasswd file specified. Exiting..."
	print help
	sys.exit()

if groupfile == "":
	print "No path to group file specified. Exiting..."
	print help
	sys.exit()

if groupmapfile == "":
	print "No path to group mapping file specified. Exiting..."
	print help
	sys.exit()

if sidfile == "":
	print "No sid given. Exiting..."
	print help
	sys.exit()
else:
	newSID = sidfile.strip()

baseConfig=univention.config_registry.baseConfig()
baseConfig.load()

if baseConfig.has_key('domainname') and baseConfig['domainname']:
	domainname = baseConfig['domainname']
	nameComponents= domainname.split('.')
	serverDN=',dc='.join(nameComponents)
	serverDN = 'dc='+serverDN
else:
	print "Could not get domainname"
	sys.exit()

if userbase == "":
	userbase = "cn=users,"+serverDN

if computerbase == "":
	computerbase = "cn=computers,"+serverDN

if groupbase == "":
	groupbase = "cn=groups,"+serverDN

if baseConfig.has_key('ldap/master') and baseConfig['ldap/master']:
	master = baseConfig['ldap/master']
else:
	print "Could not get UCS master"
	sys.exit()

if baseConfig.has_key('windows/domain') and baseConfig['windows/domain']:
	windom = baseConfig['windows/domain']
else:
	print "Could not determine Samba Domain Name"
	sys.exit()

now = int(time.time())

# parse the pdbdump file for information about already existing user data
print "Parsing the pdbdump for user information"

pdbdump_handle = open(pdbdumpfile)

current_user = ""
current_lastname = ""
current_usersid = ""

for line in pdbdump_handle:
	if line[-1] == '\n':
		line = line[:-1]
	if re.match('#', line):
		continue

	if line.startswith("----"):
		if current_user != "" and current_user[-1] != "$":
			users[current_user] = {}
			users[current_user]['lastname'] =  current_lastname
			users[current_user]['sambaRID'] =  current_usersid
			users[current_user]['groups'] =  []
			users[current_user]['primarygroup'] =  ""

		elif current_user != "" and current_user[-1] == "$":
			machines[current_user[0:-1]] = {}
			machines[current_user[0:-1]]['sambaRID'] =  current_usersid

	pdbfields = line.split(':')

	if pdbfields[0].strip() == "Unix username":
		current_user = pdbfields[1].strip()

	if pdbfields[0].strip() == "Full Name":
		current_lastname = pdbfields[1].strip()

	if pdbfields[0].strip() == "User SID":
		current_usersid = pdbfields[1].strip().split("-")[-1]

if current_user != "" and current_user[-1] != "$" and not users.has_key(current_user):
	users[current_user] = {}
	users[current_user]['lastname'] =  current_lastname
	users[current_user]['sambaRID'] =  current_usersid
	users[current_user]['groups'] =  []
	users[current_user]['primarygroup'] =  ""

elif current_user != "" and current_user[-1] == "$" and not users.has_key(current_user):
	machines[current_user[0:-1]] = {}
	machines[current_user[0:-1]]['sambaRID'] =  current_usersid

# Parse the /etc/passwd file and save the POSIX GID of the primary group
# for each username

print "Parsing primary group GID from /etc/passwd"

passwd_handle= open(passwdfile, 'r')
for line in passwd_handle:
	if line[-1] == '\n':
		line = line[:-1]
	if re.match('#', line):
		continue
	passwdfields = line.split(':')

	if users.has_key(passwdfields[0]):
		users[passwdfields[0]]['primarygroup'] = passwdfields[3]

passwd_handle.close()


# Parse the /etc/group file and store membership information for each user
# Also store group names in a dictionary

print "Parsing group membership file"

# file format:
# groupname - passwd hash - GID - members

groupfile_handle= open(groupfile, 'r')
for line in groupfile_handle:
	if line[-1] == '\n':
		line = line[:-1]
	if re.match('#', line):
		continue

	groupfields = line.split(':')
	if groupfields[0] == "nobody":
		continue
	members = groupfields[3].strip().split(",")
	for i in members:
		if users.has_key(i):
			users[i]['groups'].append(groupfields[0])

	groups[groupfields[0]] = {}
	groups[groupfields[0]]['gid'] = groupfields[2]
	groups[groupfields[0]]['rid'] = 0

	gname_by_gid[str(groupfields[2])] = groupfields[0]

groupfile_handle.close()


# Parse group mapping file (net groupmap list > file)
# format:
# groupname (S-1-5-21-238068620-871461374-333507663-7134) -> Description


groupmapfile_handle= open(groupmapfile, 'r')
for line in groupmapfile_handle:
	if line[-1] == '\n':
		line = line[:-1]
	if re.match('#', line):
		continue

	groupmapfields = line.split(' ')
	if groups.has_key(groupmapfields[0]):
		rid = groupmapfields[1].strip()[1:-1].split('-')[-1]
		groups[groupmapfields[0]]['rid'] = rid

groupmapfile_handle.close()

# Generate groups:

for i in groups.keys():
	if int(groups[i]['rid']) == 0:
		print "Skipping local group with GID ", groups[i]['gid']
	else:
		stdout2 = ""

		adm_cr_group = "univention-admin groups/group create --set name=%s" % i
		adm_cr_group = adm_cr_group + " --set gidNumber=" + str(groups[i]['gid']) +  " --option=samba --option=posix"
		adm_cr_group = adm_cr_group + " --set sambaRID=" + str(groups[i]['rid'])
		adm_cr_group = adm_cr_group + " --position=\"%s\"" % groupbase

		try:
			print "Creating group", i
			stdout2 = getCommandOutput(adm_cr_group)
		except RuntimeError, e:
			print "Failed to create group object: %s" % stdout2
			print e


print "Parsing password information from the smbpasswd file"
smbpwHandle = open(smbpasswdfile, 'r')
for line in smbpwHandle:
	if line[-1] == '\n':
		line = line[:-1]
	if re.match('#', line):
		continue
	smbpwfields = line.split(':')

	if smbpwfields[0][-1] == "$":
		if machines.has_key(smbpwfields[0][:-1]):
			machines[smbpwfields[0][:-1]]['__sambaLMPassword'] = smbpwfields[2]
			machines[smbpwfields[0][:-1]]['__sambaNTPassword'] = smbpwfields[3]
			machines[smbpwfields[0][:-1]]['__acct_flags'] = smbpwfields[4]
		elif smbpwfields[0][-1] != "$":
			if users.has_key(smbpwfields[0]):
				users[smbpwfields[0]]['__sambaLMPassword'] = smbpwfields[2]
				users[smbpwfields[0]]['__sambaNTPassword'] = smbpwfields[3]
				users[smbpwfields[0]]['__acct_flags'] = smbpwfields[4]
				users[smbpwfields[0]]['sambaLogonHours'] = '1'*168

smbpwHandle.close()


# ldapsearch -x objectClass=sambaDomain -LLL sambaSID

print "Retrieving old sambaSID"
try:
	l = ldap.open(master)
	l.simple_bind_s('', '')
except ldap.LDAPError, e:
	print e

searchScope = ldap.SCOPE_SUBTREE
searchFilter = "objectClass=sambaDomain"
retrieve_attributes = ['sambaSID']

try:
	ldap_result = l.search_s(serverDN, searchScope, searchFilter, retrieve_attributes)
	for (dn, attr) in ldap_result:
		oldSID = attr['sambaSID'][0]
except ldap.LDAPError, e:
	print "Error while fetching old Samba SID: " + e
	sys.exit()
l.unbind()
print "old SID: %s" % oldSID



if oldSID != newSID:
	lo, position = univention.admin.uldap.getAdminConnection()

	res=lo.search(filter='(objectClass=sambaDomain)', scope='domain')
	if len(res) != 1:
		print 'Not setting new SID for domain object: %d objects found' % len(res)
		sys.exit(1)
	dn, attrs=res[0]

	print 'Setting new SID in %s...' % repr(dn),
	ml=[
		('sambaSID', attrs.get('sambaSID', ''), newSID)
	]
	lo.modify(dn, ml)
	print 'done'

dummypwd = ""
darray = array.array('B')
for i in xrange(8):
	darray.append(randint(0,255))
	dummypwd = darray.tostring()


for name in users.keys():
	if name=="root":
		continue
	stdout2 = ""
	adm_cr_user = "univention-admin users/user create --set username=%s" % name
	adm_cr_user = adm_cr_user + ' --set password="' + dummypwd + '" --option=samba --option=posix --option=mail --option=person'
	adm_cr_user = adm_cr_user + " --position=\"%s\"" % userbase

	for attribute in users[name].keys():
		if users[name][attribute] and not re.match('__', attribute) and not attribute == "groups" and not attribute == "primarygroup":
			adm_cr_user = adm_cr_user + " --set %s=\"%s\"" % (attribute, users[name][attribute])

	try:
		print "Creating user object for %s" % name
		stdout2 = getCommandOutput(adm_cr_user)
	except RuntimeError, e:
		print "Failed to create user object: %s" % stdout2
		print e

try:
	print "Creating Kerberos keys"
	stdout2 = getCommandOutput('/usr/share/univention-heimdal/kerberos_now')
except RuntimeError, e:
	print "Failed to create user object: %s" % stdout2
	print e



for name in users.keys():
	if name=="root":
		continue
	stdout2 = ""


	if users[name].has_key('groups'):
		for i in users[name]['groups']:
			adm_add_gr = 'univention-admin users/user modify  --dn uid="' + name + ',' + userbase + '" --append groups="cn=' + i + ',' + groupbase + '"'
			try:
				print "Adding user", name, "to group", i
				stdout2 = getCommandOutput(adm_add_gr)
			except RuntimeError, e:
				print "Failed to create user object: %s" % stdout2
				print e
	if users[name].has_key('primarygroup'):
		i = users[name]['primarygroup']
		if gname_by_gid.has_key(str(i)):
			adm_add_gr = 'univention-admin users/user modify  --dn uid="' + name + ',' + userbase + '" --set primaryGroup="cn=' + gname_by_gid[str(i)] + ',' + groupbase + '"'
			try:
				print "Setting primary group for ",name,"to", gname_by_gid[str(i)]
				stdout2 = getCommandOutput(adm_add_gr)
			except RuntimeError, e:
				print "Failed to create user object: %s" % stdout2
				print e
		else:
			print "Skipping entry for primary gid", i



for name in machines.keys():
	stdout2 = ""

	adm_cr_user = "univention-admin computers/windows create --set name=%s" % name
	adm_cr_user = adm_cr_user + ' --set password="' + dummypwd + '"'# --option=samba --option=posix --option=mail --option=person"
	adm_cr_user = adm_cr_user + " --position=\"%s\"" % computerbase

	for attribute in machines[name].keys():
		if machines[name][attribute] and not re.match('__', attribute):
			adm_cr_user = adm_cr_user + " --set %s=\"%s\"" % (attribute, machines[name][attribute])

	try:
		print "Creating machine object for %s" % name
		stdout2 = getCommandOutput(adm_cr_user)
	except RuntimeError, e:
		print "Failed to create user object: %s" % stdout2
		print e


print "Changing Samba SID of remaining objects"
if oldSID != newSID:
	try:
		getCommandOutput("/usr/share/univention-samba/change_sid %s %s" % (oldSID, newSID))
	except RuntimeError, e:
		print "Error while changing Samba SIDs of remaining LDAP objects" + e
		sys.exit()

secretHandle = open('/etc/ldap.secret', 'r')
for line in secretHandle:
	if line[-1] == '\n':
		line = line[:-1]
	bindpw = line
binddn = "cn=admin,%s" % serverDN

l = ldap.open(master)
l.simple_bind_s(binddn, bindpw)
print "Creating user passwords"
for name in users.keys():
	if name == "root":
		continue
	userdn = "uid=%s,%s" % (name, userbase)
	try:
		l.modify_s(userdn,[(ldap.MOD_REPLACE, 'sambaNTPassword', [users[name]['__sambaNTPassword']])])
		if users[name].has_key('__sambaLMPassword'):
			l.modify_s(userdn,[(ldap.MOD_REPLACE, 'sambaLMPassword', [users[name]['__sambaLMPassword']])])
		if users[name].has_key('__unixPassword'):
			l.modify_s(userdn,[(ldap.MOD_REPLACE, 'userPassword', [users[name]['__unixPassword']])])
		if users[name].has_key('__acct_flags'):
			l.modify_s(userdn,[(ldap.MOD_REPLACE, 'sambaAcctFlags', [users[name]['__acct_flags']])])
		if users[name].has_key('__sambaLMPassword'):
			l.modify_s(userdn,[(ldap.MOD_REPLACE, 'userPassword', '{LANMAN}%s' % [users[name]['__sambaLMPassword']])])

	except ldap.LDAPError, e:
		print "Modify  for user %s failed: " % name
		print e

print "Creating machine passwords"
for name in machines.keys():
	machinedn = "cn=%s,%s" % (name, computerbase)
	try:
		l.modify_s(machinedn,[(ldap.MOD_REPLACE, 'sambaNTPassword', [machines[name]['__sambaNTPassword']])])
		if machines[name].has_key('__acct_flags'):
			l.modify_s(machinedn,[(ldap.MOD_REPLACE, 'sambaAcctFlags', [machines[name]['__acct_flags']])])

	except ldap.LDAPError, e:
		print "Modify  for user %s failed: " % name
		print e

print "Finished"
sys.exit(0)
