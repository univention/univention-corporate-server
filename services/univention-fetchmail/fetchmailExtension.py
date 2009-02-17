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
# should
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
name = 'fetchmailExtension'
description = 'write user-configuration to fetchmailrc'
filter = '(objectClass=univentionFetchmail)'
attributes = []

import listener
import univention.debug
import univention.utf8
import re
import ldap
import univention.config_registry

#sys.setdefaultencoding('iso8859-15')
fn_fetchmailrc = '/etc/fetchmailrc'
__initscript = '/etc/init.d/fetchmail'

REpassword = re.compile("^poll .*? there with password '(.*?)' is '[^']+' here")

# ----- function to open an textfile with setuid(0) for root-action
def load_rc(ofile):
	l = None
	listener.setuid(0)
	try:
		f = open(ofile,"r")
		l = f.readlines()
		f.close()
	except Exception, e:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Failed to open "%s": %s' % (ofile, str(e)) )
	listener.unsetuid()
	return l

# ----- function to write to an textfile with setuid(0) for root-action
def write_rc(flist, wfile):
	listener.setuid(0)
	try:
		f = open(wfile,"w")
		f.writelines(flist)
		f.close()
	except Exception, e:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Failed to write to file "%s": %s' % (wfile, str(e)))
	listener.unsetuid()

# ----- function to get current password of a user from fetchmailrc
def get_pw_from_rc(lines, uid):
	if not uid:
		return None
	for line in lines:
		l = line.rstrip()
		if l.endswith("#UID='%s'" % uid):
			match = REpassword.match(l)
			if match:
				return match.group(1)
	return None

# ----- function to delete an object in filerepresenting-list if old settings are found
def objdelete(dlist, old):
	if old and old.has_key('uid') and old['uid'][0]:
		return [ line for line in dlist if not re.search("#UID='%s'[ \t]*$" % old['uid'][0], line) ]
	else:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'Removal of user in fetchmailrc failed: %s' % str(old.get('uid')))


# ----- function to add new entry
def objappend(flist, new, password = None):
	passwd = password
	if details_complete(new):
		passwd = new.get('univentionFetchmailPasswd', [ passwd ])[0]

		flist.append( "poll %s with proto %s auth password user '%s' there with password '%s' is '%s' here options fetchall  #UID='%s'\n" % \
					  ( new['univentionFetchmailServer'][0],
						new['univentionFetchmailProtocol'][0],
						new['univentionFetchmailAddress'][0],
						passwd,
						new['mailPrimaryAddress'][0],
						new['uid'][0] ) )
	else:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO,'Adding user to "fetchmailrc" failed')


def details_complete(obj, incl_password = False):
	complete = True
	if not obj:
		complete = False
	else:
		attrlist = [ 'mailPrimaryAddress', 'univentionFetchmailServer', 'univentionFetchmailProtocol', 'univentionFetchmailAddress' ]
		if incl_password:
			attrlist.append( 'univentionFetchmailPasswd' )
		for attr in attrlist:
			if not obj.get( attr ):
				complete = False
			elif not obj.get( attr )[0]:
				complete = False
	return complete


def only_password_reset(old, new):
	# if one or both objects are missing ==> false
	if (old and not new) or (not old and new) or (not old and not new):
		return False
	else:
		# if one of the following attributes changed ==> false
		attrlist = [ 'mailPrimaryAddress', 'univentionFetchmailServer', 'univentionFetchmailProtocol', 'univentionFetchmailAddress' ]
		for attr in attrlist:
			if old.get( attr ) != new.get( attr ):
				return False

		# if password hasn't been reset (reset == "old.pw and not new.pw") ==> false
		if not old.get( 'univentionFetchmailPasswd' ) or new.get( 'univentionFetchmailPasswd' ):
			return False

	return True


def handler(dn, new, old):
	flist = load_rc(fn_fetchmailrc)

	if old and not new:
		# object has been deleted ==> remove entry from rc file
		flist = objdelete(flist, old)
		write_rc(flist, fn_fetchmailrc)

	elif old and new and details_complete(old) and not details_complete(new):
		# data is now incomplete ==> remove entry from rc file
		flist = objdelete(flist, old)
		write_rc(flist, fn_fetchmailrc)

	elif new and details_complete(new):
		# obj has been created or modified

		passwd = None
		if old:
			# old exists ==> object has been modified ==> get old password and remove object entry from rc file
			passwd = get_pw_from_rc( flist, new.get('uid')[0] )
			flist = objdelete(flist, old)

		if not details_complete(new, incl_password=True):
			if only_password_reset(old, new):
				univention.debug.debug( univention.debug.LISTENER, univention.debug.INFO, 'fetchmail: password has been reset - nothing to do' )
				# only password has been reset ==> nothing to do
				return

			# new obj does not contain password
			if passwd:
				# passwd has been set in old ==> use old password
				univention.debug.debug( univention.debug.LISTENER, univention.debug.INFO, 'fetchmail: using old password' )
				objappend(flist, new, passwd)
				write_rc(flist, fn_fetchmailrc)
			else:
				univention.debug.debug( univention.debug.LISTENER, univention.debug.ERROR, 'fetchmail: user "%s": no password set in old and new' % new['uid'][0] )
		else:
			# new obj contains password ==> use new password
			objappend(flist, new)
			write_rc(flist, fn_fetchmailrc)

			univention.debug.debug( univention.debug.LISTENER, univention.debug.INFO, 'fetchmail: using new password' )

			configRegistry = univention.config_registry.ConfigRegistry()
			configRegistry.load()

			baseDN = configRegistry.get('ldap/base')
			fqdnMaster = configRegistry.get('ldap/master')

			if not baseDN:
				univention.debug.debug( univention.debug.LISTENER, univention.debug.ERROR, 'fetchmail: cannot get UCR variable ldap/base' )
				return

			if not fqdnMaster:
				univention.debug.debug( univention.debug.LISTENER, univention.debug.ERROR, 'fetchmail: cannot get UCR variable ldap/master' )
				return

			bindpw = ''
			listener.setuid(0)
			try:
				bindpw = open('/etc/ldap.secret').read()
				bindpw = bindpw.strip('\n')
			finally:
				listener.unsetuid()

			if not bindpw:
				univention.debug.debug( univention.debug.LISTENER, univention.debug.ERROR, 'fetchmail: cannot get password for cn=admin,%s' % baseDN )
				return

			try:
				lo = ldap.open( fqdnMaster, 389 )
				lo.simple_bind_s("cn=admin,"+baseDN, bindpw)

				modlist = [ (ldap.MOD_DELETE, 'univentionFetchmailPasswd', new['univentionFetchmailPasswd'][0]) ]
				lo.modify_s(dn, modlist)
				univention.debug.debug( univention.debug.LISTENER, univention.debug.INFO, 'fetchmail: reset password successfully' )
			except Exception, e:
				univention.debug.debug( univention.debug.LISTENER, univention.debug.ERROR, 'fetchmail: cannot reset password in LDAP (%s): %s' % (dn, str(e)) )


def initialize():
	pass

def postrun():
	global __initscript
	initscript = __initscript
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'Restarting fetchmail-daemon')
	listener.setuid(0)
	try:
		listener.run(initscript, ['fetchmail', 'restart'], uid=0)
	finally:
		listener.unsetuid()
