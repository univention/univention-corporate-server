#!/usr/bin/python2.4
# -*- coding: utf-8 -*-

import subprocess
import re
from optparse import OptionParser
import sys

logfile = 'test.log'
#share = '//10.200.21.151/vielefeilz'
#credentials = 'Administrator%univention'

net='/usr/bin/net'
smbcacls='/usr/bin/smbcacls'

parser = OptionParser()
parser.add_option("-A", "--credentialsfile", dest="credentialsfile", help="File that contains the credentials")
parser.add_option("-U", "--user", dest="user", help="User")
parser.add_option("-S", "--src", dest="src", help="Source server")
parser.add_option("-D", "--dst", dest="dst", help="Destination server (default: localhost)")
parser.add_option("-s", "--share", dest="share", help="Name of share to migrate")
parser.add_option("-d", "--dstdomain", dest="dstdomain", help="Destination domain")
parser.add_option("-v", "--verbose", dest="verbose", help="Verbose output (default: False)", action="store_true")

parser.set_defaults (verbose=False, dst='localhost')

options, args = parser.parse_args()

if not (options.src and options.share and options.dstdomain):
	print 'Insufficient arguments'
	sys.exit (1)

class ShareFile (object):
	class Obj (object):
		def __init__ (self, domain, _id):
			#super (object, self).__init__ ()
			self.domain = domain
			self.id = _id
		def __str__ (self):
			return self.id

	class Owner (Obj):
		def __str__ (self):
			return 'OWNER:%s' % (self.id)

	class Group (Obj):
		def __str__ (self):
			return 'GROUP:%s' % (self.id)

	class Acl (Obj):
		def __init__ (self, domain, _id, _type, flags, permissions):
			super (ShareFile.Acl, self).__init__ (domain, _id)
			self.type = _type
			self.flags = flags
			self.permissions = permissions
		def __str__ (self):
			return 'ACL:%s:%s/%s/%s' % (self.id, self.type, self.flags, self.permissions)

	def __init__ (self, filename, credentials):
		"""
		@param filename	I.e. \\server\share\file
		"""
		tmp = filename.split ('\\')
		self.server = tmp[2]
		self.share = tmp[3]
		self.filename = '\\'.join (tmp[4:])
		self.credentials = credentials
		self.revision = None
		self.owner = None
		self.group = None
		self.acls = []

	def __str__ (self):
		return self.filename

	def _fill_permissions (self, output):
		def split_domain_id (x):
			tmp = x.split ('+')
			if len (tmp) == 2:
				return {'domain':tmp[0], 'id':tmp[1]}
			elif len (tmp) == 1:
				return ('', tmp[1])
			else:
				return (None, None)
		def split_permissions (x):
			tmp = x.split ('/')
			if len (tmp) == 3:
				return {'type':tmp[0], 'flags':tmp[1], 'permissions':tmp[2]}
			raise ValueError ('Illegal permissions')
		for line in output:
			try:
				p = line.split (':')
				if p[0] == 'OWNER':
					tmp = split_domain_id (p[1])
					self.owner = ShareFile.Owner (tmp['domain'], tmp['id'])
				elif p[0] == 'GROUP':
					tmp = split_domain_id (p[1])
					self.group = ShareFile.Group (tmp['domain'], tmp['id'])
				elif p[0] == 'REVISION':
					self.revision = p[1]
				elif p[0] == 'ACL':
					tmp = split_domain_id (p[1])
					tmp2 = split_permissions (p[2])
					self.acls.append (ShareFile.Acl (tmp['domain'], tmp['id'], tmp2['type'], tmp2['flags'], tmp2['permissions']))
				else:
					print 'Unknown line: %s' % line
			except:
				import traceback
				traceback.print_exc ()
				print 'Error on parsing permissions. Ignoring line: %s' % line

	def fill_permissions (self):
		cmd = [smbcacls, '\\\\%s\\%s' % (self.server, self.share), self.filename]
		cmd.extend (self.credentials)
		p = subprocess.Popen (cmd, stdout=subprocess.PIPE)
		returncode = p.wait ()
		if returncode:
			raise Exception ('Filling permissions failed with error code: %d' % returncode)
		stdout = p.communicate ()[0]
		self.owner = None
		self.group = None
		self.revision = None
		self.acls = []
		self._fill_permissions (stdout.splitlines ())


	def _set (self, params):
		cmd = [smbcacls, '\\\\%s\\%s' % (self.server, self.share), self.filename]
		cmd.extend (self.credentials)
		cmd.extend (params)
		if options.verbose:
			print " ".join (cmd)
		p = subprocess.Popen (cmd, close_fds=True)
		returncode = p.wait ()
		if returncode:
			print 'Set failed with error code: %d' % returncode
			traceback.print_exc ()

	def set_owner (self, owner):
		if options.verbose:
			print 'Setting owner for file:', self.filename

		self._set (['-C', owner])

	def set_group (self, group):
		if options.verbose:
			print 'Setting group for file:', self.filename

		self._set (['-G', group])

	def set_permissions (self, permissions):
		if options.verbose:
			print 'Setting permissions for file:', self.filename

		self._set (['-S'] + permissions)
	def get_printable_permissions (self):
		from string import Template
		t = Template ("""REVISION:${revision}
${owner}
${group}
${acls}""")
		acls = ''
		for acl in self.acls:
			acls += str (acl) + '\n'
		return t.substitute (revision=self.revision, \
				owner=self.owner, \
				group=self.group, \
				acls=acls)

class MigratedFile (object):
	def __init__ (self, srcfile, dstfile):
		self.srcfile = srcfile
		self.dstfile = dstfile

	def __str__ (self):
		return r'%s => %s' % (self.srcfile, self.dstfile)

	@classmethod
	def translate_domain_id (cls, dstdomain, obj):
		if obj.domain in ['NT-AUTORITÄT']:
			return

		if obj.id in ['Benutzer', 'ERSTELLER-BESITZER']:
			return

		tmp = ShareFile.Obj (dstdomain, obj.id)
		if obj.domain == 'VORDEFINIERT':
			if obj.id == 'Administratoren':
				tmp.id = 'Domain Admins'
		if obj.id == 'Domänen-Benutzer':
			tmp.id = 'Domain Users'
		return tmp

	def migrate_owner (self, dstdomain, src, dst):
		tmp = MigratedFile.translate_domain_id (dstdomain, src.owner)
		if tmp and tmp.id != dst.owner.id:
			if tmp.id == 'Domain Admins':
				tmp.id = 'Administrator'
			return tmp.id

	def migrate_group (self, dstdomain, src, dst):
		tmp = MigratedFile.translate_domain_id (dstdomain, src.group)
		if tmp and tmp.id != dst.group.id:
			return tmp.id

	def migrate_acls (self, dstdomain, src, dst):
		res = []
		if src.acls and src.acls != dst.acls:
			for sa in src.acls:
				tmp = MigratedFile.translate_domain_id (dstdomain, sa)
				if tmp:
					new_a = ShareFile.Acl (tmp.domain, tmp.id, sa.type, sa.flags, sa.permissions)
					res.append (str (new_a))
		if res:
			return [','.join (res)]
		return res

	def migrate_permissions (self, dstdomain):
		self.dstfile.fill_permissions ()
		self.srcfile.fill_permissions ()

		owner = self.migrate_owner (dstdomain, self.srcfile, self.dstfile)
		if owner:
			self.dstfile.set_owner (owner)

		group = self.migrate_group (dstdomain, self.srcfile, self.dstfile)
		if group:
			self.dstfile.set_group (group)

		permissions = self.migrate_acls (dstdomain, self.srcfile, self.dstfile)
		if permissions:
			self.dstfile.set_permissions (permissions)

class Share (object):
	def __init__ (self, srcserver, share, credentialsfile=None, user=None):
		"""
		@param srcserver	Name of source server, i.e. 10.200.21.123
		@param share	Name of share, i.e. myshare
		"""
		self.srcserver = srcserver
		self.share = share
		self.credentials = []
		if credentialsfile:
			self.credentials.extend (['-A', credentialsfile])
		elif user:
			self.credentials.extend (['-U', user])

	def migrate_files_output_to_dict (self, output, dstserver):
		m = re.compile ('copying \[(?P<from>[^]]*)\] => \[(?P<to>[^]]*)\].*')
		res = []
		for line in output:
			r = m.match (line)
			if r:
				d = r.groupdict ()
				res.append (MigratedFile ( \
						ShareFile (d['from'], self.credentials), \
						ShareFile (d['to'], self.credentials)))
		return res

	def migrate_files (self, dstserver='localhost'):
		cmd = [net, 'rpc', 'share', 'migrate', 'files', self.share, '-S', self.srcserver, '-v']
		cmd.extend (self.credentials)
		cmd.append (dstserver)
		if options.verbose:
			print 'Copying files.'
		p = subprocess.Popen (cmd, stdout=subprocess.PIPE)
		returncode = p.wait ()
		if returncode:
			raise Exception ('Migrating files failed with error code: %d' % returncode)
		stdout = p.communicate ()[0]

		return self.migrate_files_output_to_dict (stdout.splitlines (), dstserver)

	def migrate (self, dstdomain, dstserver='localhost'):
		migrated_files = self.migrate_files (dstserver)
		for f in migrated_files:
			f.migrate_permissions (dstdomain)
			if options.verbose:
				print 'Old permissions:\n', f.dstfile.get_printable_permissions ()
				f.dstfile.fill_permissions ()
				print 'New permissions:\n', f.dstfile.get_printable_permissions ()


s = Share (options.src, options.share, credentialsfile=options.credentialsfile, user=options.user)
s.migrate (options.dstdomain, options.dst)
