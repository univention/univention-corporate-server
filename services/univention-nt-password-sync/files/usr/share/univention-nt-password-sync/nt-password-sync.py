#!/usr/bin/python2.4 -OO
#
# Univention NT password sync
#  skript for sending password-hashes to a Windows Host 
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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

import array, socket, cPickle, time, os, shutil, tempfile, univention.debug, M2Crypto, univention_baseconfig

importDir="/usr/share/univention-nt-password-sync/password-changes"
tmpDir = tempfile.mktemp()

baseConfig=univention_baseconfig.baseConfig()
baseConfig.load()

NTAccount = "Administrator"
if baseConfig.has_key("nt-password-sync/account"):
	NTAccount = baseConfig["nt-password-sync/account"]
else:
	univention.debug.debug(univention.debug.LDAP, univention.debug.WARN,"nt-password-sync/account not set")

NTPassword = ""
if baseConfig.has_key("nt-password-sync/password-file"):
	pw_file = baseConfig['nt-password-sync/password-file']
	fp = open(pw_file,'r')
	NTPassword = fp.readline()
	fp.close()
	if NTPassword[-1] == '\n':
		NTPassword = NTPassword[:-1]
else:
	univention.debug.debug(univention.debug.LDAP, univention.debug.WARN,"nt-password-sync/password-file not set")


NTHost = ''
if baseConfig.has_key("nt-password-sync/nt-host"):
	NTHost = baseConfig["nt-password-sync/nt-host"]
else:
	univention.debug.debug(univention.debug.LDAP, univention.debug.ERROR,"nt-password-sync/nt-host not set, can't proceed")
	sys.exit(1)

def _append_length(a, str):
        l = len(str)
        a.append(chr((l & 0xff)))
        a.append(chr((l & 0xff00) >> 8))
        a.append(chr((l & 0xff0000) >> 16))
        a.append(chr((l & 0xff000000) >> 24))

def _append_string(a, strstr):
        for i in range(0,len(strstr)):
                a.append(strstr[i])

def _append(a, strstr):
        _append_length(a, str(strstr))
        _append_string(a, str(strstr))

def _append_array(a, strstr):
        _append_length(a, strstr)
        _append_string(a, strstr)


def _get_integer(str):
        res=ord(str[0]) + (ord(str[1]) << 8) + (ord(str[2]) << 16) + (ord(str[3]) << 24)
        return res

def ssl_init(sd):
        meth = M2Crypto.__m2crypto.sslv2_method();
        ctx = M2Crypto.__m2crypto.ssl_ctx_new (meth);
        ssl = M2Crypto.__m2crypto.ssl_new (ctx);
        M2Crypto.__m2crypto.ssl_set_fd (ssl, sd);
        err = M2Crypto.__m2crypto.ssl_connect (ssl);
        return ssl

def createTmp():
	os.mkdir(tmpDir)
	os.chmod(tmpDir,0700)
	univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"created tmpDir %s" % tmpDir)

def removeTmp():
	def removeFiles(files, directory):
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"removeTmp: removeFiles %s in %s" % (files, directory))
		for filename in files:
			os.remove(os.path.join(directory, filename))
			#print "remove %s" % filename

	def removeDirs(directories):
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"removeTmp: removeDirs %s" % (directories))
		for dirname in directories:
			os.removedirs(dirname)
			#print "remove dir %s" % dirname

	def removeRecursive(directories):
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"removeTmp: removeRecursive %s" % (directories))
		for dirname in directories:
			for root, subdirectories, files in os.walk(dirname):
				removeFiles(files, dirname)
				removeRecursive(subdirectories)
		removeDirs(directories)
	removeRecursive([tmpDir])
		

def filesToSync():
	return os.listdir(importDir)

def syncFiles():
	for filename in filesToSync():
		if not filename == 'tmp':
			syncFile(filename)
	
def syncFile(filename):
	try:
		shutil.move(os.path.join(importDir, filename), tmpDir)
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"syncFile: moved %s" % filename)
	except:
		univention.debug.debug(univention.debug.LDAP, univention.debug.ERROR,"failed to move %s" % filename)
		raise

	try:
		f = open(os.path.join(tmpDir, filename))
		obj = cPickle.load(f)
		f.close()
		if syncObject(obj):
			os.remove(os.path.join(tmpDir, filename))
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"syncFile: password has been synced, remove %s" % filename)
		else:
			univention.debug.debug(univention.debug.LDAP, univention.debug.WARN,"syncFile: synced failed, move back to importDir: %s" % filename)
			try:
				shutil.move(os.path.join(tmpDir, filename), importDir)
			except:
				univention.debug.debug(univention.debug.LDAP, univention.debug.ERROR,"syncFile: move to importDir failed, change will be lost: %s" % filename)
			
	except:
		univention.debug.debug(univention.debug.LDAP, univention.debug.ERROR,"syncFile: failed to sync object with unknown error, change will be lost: %s" % filename)

		
def syncObject(obj):
	(dn, new, old, old_dn) = obj

	LMHash = ""
	NTHash = ""

	if old and not new:
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"syncObject: detected deleted Object, ignored")
		return True

	if new.has_key('uid'):
		username = new['uid'][0]
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"syncObject: found userobject: %s" % username)
	else:
		univention.debug.debug(univention.debug.LDAP, univention.debug.ERROR,"syncObject: Object has no username, can't sync")
		return False

	if new.has_key('sambaLMPassword'):
		LMHash = new['sambaLMPassword'][0]
	
	if new.has_key('sambaNTPassword'):
		NTHash = new['sambaNTPassword'][0]

	if not NTHash and not LMHash:
		univention.debug.debug(univention.debug.LDAP, univention.debug.WARN,"syncObject: Object has no password-hash at all, sync may fail: %s" % username )

	return sendPassword(username, NTHash, LMHash)

def sendPassword(username, NTHash, LMHash):
	try:
		a = array.array('c')
		_append ( a, NTAccount ) # Username
		_append ( a, NTPassword ) # Password
		a.append ( 'S' )
		_append ( a, username ) # username, "compatible_modstring"
		_append ( a, str('%s%s' % (NTHash,LMHash) ) ) # pwd-Hash, NTLM
		package = array.array('c')
		_append_array( package, a)
		
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"sendPassword: generated data-array" )
	except:
		univention.debug.debug(univention.debug.LDAP, univention.debug.ERROR,"sendPassword: generation of data-array failed" )
		return False

	try:
		# Create Socket and send package
		s = socket.socket( socket.AF_INET, socket.SOCK_STREAM );
		s.connect ( (NTHost, 6670) ) # hostname
		ssl=ssl_init(s.fileno())
		M2Crypto.__m2crypto.ssl_write(ssl, package)

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"sendPassword: established connection" )
	except:
		univention.debug.debug(univention.debug.LDAP, univention.debug.ERROR,"sendPassword: failed to established connection to \"%s\", is there an UCS AD Connector daemon running?" % NTHost )
		return False

	try:
		rval = M2Crypto.__m2crypto.ssl_read(ssl, 8192)
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"sendPassword: password accepted")
	except:
		univention.debug.debug(univention.debug.LDAP, univention.debug.ERROR,"sendPassword: sending password failed")
		return False

	return True


def initDebug():
	if baseConfig.has_key('nt-password-sync/debug/function'):
		try:
			function_level = int(baseConfig['nt-password-sync/debug/function'])
		except:
			function_level = 0
	else:
		function_level=0
	univention.debug.init('/var/log/univention/nt-password-sync.log', 1, function_level)
	if baseConfig.has_key('nt-password-sync/debug/level'):
		debug_level = baseConfig['nt-password-sync/debug/level']
	else:
		debug_level=2
	univention.debug.set_level(univention.debug.LDAP, int(debug_level))

def closeDebug():
	_d=univention.debug.function('ldap.close_debug')
	univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "closeDebug: close debug")
	univention.debug.end('/var/log/univention/nt-password-sync.log')
	univention.debug.exit('/var/log/univention/nt-password-sync.log')


initDebug()
univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "startup")
createTmp()
try:
	if filesToSync():		
		syncFiles()			
finally:
	removeTmp()
	
closeDebug()
