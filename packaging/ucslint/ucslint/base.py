# -*- coding: utf-8 -*-
# pylint: disable-msg=C0103,C0111,C0301,R0902,R0903,R0912,R0913
#
# Copyright (C) 2008-2014 Univention GmbH
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

import os

RESULT_UNKNOWN = -1
RESULT_OK = 0
RESULT_WARN = 1
RESULT_ERROR = 2
RESULT_INFO = 3
RESULT_STYLE = 4

RESULT_INT2STR = {
	RESULT_UNKNOWN: 'U',
	RESULT_OK: 'OK',
	RESULT_WARN: 'W',
	RESULT_ERROR: 'E',
	RESULT_INFO: 'I',
	RESULT_STYLE: 'S',
	}


class UPCMessage(object):
	"""Univention Policy Check message."""
	def __init__(self, id_, msg=None, filename=None, line=None, pos=None):
		self.id = id_
		self.msg = msg
		self.filename = filename
		self.line = line
		self.pos = pos

		if self.filename is not None and self.filename.startswith('./'):
			self.filename = self.filename[2:]

	def __str__(self):
		if self.filename:
			s = '%s' % self.filename
			if self.line is not None:
				s += ':%s' % self.line
				if self.pos is not None:
					s += ':%s' % self.pos
			return '%s: %s: %s' % (self.id, s, self.msg)
		return '%s: %s' % (self.id, self.msg)

	def getId(self):
		return self.id


class UniventionPackageCheckBase(object):
	def __init__(self):
		self.name = None
		self.msg = []
		self.debuglevel = 0

	def addmsg(self, msgid, msg=None, filename=None, line=None, pos=None):
		message = UPCMessage(msgid, msg=msg, filename=filename, line=line, pos=pos)
		self.msg.append(message)

	def getMsgIds(self):  # pylint: disable-msg=R0201
		return {}

	def setdebug(self, level):
		self.debuglevel = level

	def debug(self, msg):
		if self.debuglevel > 0:
			print '%s: %s' % (self.name, msg)

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass

	def check(self, path):
		""" the real check """
		pass

	def result(self):
		""" return result """
		return self.msg


class UniventionPackageCheckDebian(UniventionPackageCheckBase):
    """Check for debian/ directory."""
    def check(self, path):
        """ the real check """
        super(UniventionPackageCheckDebian, self).check(path)
        if not os.path.isdir( os.path.join(path, 'debian') ):
            raise UCSLintException("directory '%s' does not exist!" % (path,))


class UCSLintException(Exception):
    """Top level exception."""
    pass


class DebianControlNotEnoughSections(UCSLintException):
    """Content exception."""
    pass


class DebianControlParsingError(UCSLintException):
    """Parsing exception."""
    pass


class FailedToReadFile(UCSLintException):
	"""File reading exception."""
	def __init__(self, fn):
		UCSLintException.__init__(self)
		self.fn = fn


class DebianControlEntry(dict):
	def __init__(self, content):
		dict.__init__(self)

		lines = content.splitlines()
		i = 0
		inDescription = False
		# handle multiline entries and merge them into one line
		while i < len(lines):
			if not lines[i] or lines[i].startswith('#'):
				del lines[i]
				continue
			if lines[i].startswith(' ') or lines[i].startswith('\t'):
				if not inDescription:
					lines[i-1] += ' %s' % lines[i].lstrip(' \t')
					del lines[i]
					continue
			i += 1

		# split lines into dictionary
		for line in lines:
			if not ':' in line:
				raise DebianControlParsingError(line)
			key, val = line.split(': ', 1)
			self[ key ] = val


class ParserDebianControl(object):
	"""Parse debian/control file."""
	def __init__(self, filename):
		self.filename = filename
		self.source_section = None
		self.binary_sections = []

		try:
			content = open(self.filename, 'r').read()
		except IOError:
			raise FailedToReadFile(self.filename)

		parts = content.split('\n\n')
		if len(parts) < 2:
			raise DebianControlNotEnoughSections()

		self.source_section = DebianControlEntry(parts[0])
		for part in parts[1:]:
			package = DebianControlEntry(part)
			if package:
				self.binary_sections.append(package)


class RegExTest(object):
	def __init__(self, regex, msgid, msg, cntmin=None, cntmax=None):
		self.regex = regex
		self.msgid = msgid
		self.msg = msg
		self.formatmsg = False
		self.cntmin = cntmin
		self.cntmax = cntmax
		self.cnt = 0

		for val in [ '%(startline)s', '%(startpos)s', '%(endline)s', '%(endpos)s', '%(basename)s', '%(filename)s' ]:
			if val in msg:
				self.formatmsg = True
				break


class UPCFileTester(object):
	""" Univention Package Check - File Tester
		simple class to test if a certain text exists/does not exist in a textfile

		By default only the first 100k of the file will be read.

		>>>	import re
		>>>	x = UPCFileTester()
		>>>	x.open('/etc/fstab')
		>>>	x.addTest( re.compile('ext[234]'), '5432-1', 'Habe ein extfs in Zeile %(startline)s und Position %(startpos)s in Datei %(basename)s gefunden.', cntmax=0)
		>>>	x.addTest( re.compile('squashfs'), '1234-5', 'Habe kein squashfs in Datei %(basename)s gefunden.', cntmin=1)
		>>>	msglist = x.runTests()
		>>>	for msg in msglist:
		>>>		print '%s ==> %s ==> %s' % (msg.id, msg.filename, msg.msg)
		5432-1: /etc/fstab:4:29: Habe ein extfs in Zeile 4 und Position 29 in Datei fstab gefunden.
		5432-1: /etc/fstab:7:19: Habe ein extfs in Zeile 7 und Position 19 in Datei fstab gefunden.
		1234-5: /etc/fstab: Habe kein squashfs in Datei fstab gefunden.
	"""

	def __init__(self, maxsize=100*1024):
		"""
		creates a new UPCFileTester object
		maxsize: maximum number of bytes read from specified file
		"""
		self.maxsize = maxsize
		self.filename = None
		self.basename = None
		self.raw = None
		self.lines = []
		self.tests = []

	def open(self, filename):
		"""
		opens the specified file and reads up to 'maxsize' bytes into memory
		"""
		self.filename = filename
		self.basename = os.path.basename(self.filename)
		# hold raw file in memory (self.raw) and a unwrapped version (self.lines)
		# the raw version is required to calculate the correct position.
		# tests will be done with unwrapped version.
		self.raw = open(filename,'r').read(self.maxsize)
		self.raw.rstrip('\n')
		lines = self.raw.replace('\\\n','  ').replace('\\\r\n','   ')
		self.lines = lines.splitlines()

	def _getpos(self, linenumber, pos_in_line):
		"""
		Converts 'unwrapped' position values (line and position in line) into
		position values corresponding to the raw file.
		Counting of lines and position starts at 1, so first byte is at line 1 pos 1!
		"""
		pos = sum((len(_) + 1 for _ in self.lines[:linenumber]))
		pos += pos_in_line
		raw = self.raw[:pos]
		realpos = len(raw) - raw.rfind('\n')
		realline = raw.count('\n')
		return (realline+1, realpos)

	def addTest(self, regex, msgid, msg, cntmin=None, cntmax=None):
		"""
		add a new test
		regex: regular expression
		msgid: msgid for UPCMessage
		msg: message for UPCMessage
			 if msg contains one or more of the keywords '%(startline)s', '%(startpos)s', '%(endline)s', '%(endpos)s' or '%(basename)s'
			 they will get replaced by their corresponding value.
		cntmin: 'regex' has to match at least 'cntmin' times otherwise a UPCMessage will be added
		cntmax: 'regex' has to match at most 'cntmax' times otherwise a UPCMessage will be added

		an exception will be raised if neither cntmin nor cntmax has been set
		"""
		if cntmin is None and cntmax is None:
			raise ValueError('cntmin or cntmax has to be set')
		self.tests.append( RegExTest( regex, msgid, msg, cntmin, cntmax) )

	def runTests(self):
		"""
		runs all given tests on loaded file and returns a list of UPCMessage objects
		"""
		if not self.filename:
			raise Exception('no file has been loaded')

		msglist = []
		for t in self.tests:
			t.cnt = 0
		# iterate over all lines
		for linenum, line in enumerate(self.lines):
			# iterate over all tests
			for t in self.tests:
				# test regex with current line
				match = t.regex.search(line)
				if match:
					# found a match ==> increase counter
					t.cnt += 1
					if t.cntmax != None and t.cnt > t.cntmax:
						# a maximum counter has been defined and maximum has been exceeded
						startline, startpos = self._getpos( linenum, match.start(0) )
						endline, endpos = self._getpos( linenum, match.end(0) )
						msg = t.msg
						if t.formatmsg:
							# format msg
							msg = msg % { 'startline': startline, 'startpos': startpos, 'endline': endline, 'endpos': endpos, 'basename': self.basename, 'filename': self.filename }
						# append UPCMessage
						msglist.append( UPCMessage( t.msgid, msg=msg, filename=self.filename, line=startline, pos=startpos ) )

		# check if mincnt has been reached by counter - if not then add UPCMessage
		for t in self.tests:
			if t.cntmin != None and t.cnt < t.cntmin:
				msg = t.msg
				if t.formatmsg:
					msg = msg % { 'basename': self.basename, 'filename': self.filename }
					# append msg
					msglist.append( UPCMessage( t.msgid, msg=msg, filename=self.filename ) )
		return msglist


class FilteredDirWalkGenerator(object):
	def __init__(self, path, ignore_dirs=None, prefixes=None, suffixes=None, ignore_suffixes=None, ignore_files=None, ignore_debian_subdirs=True, reHashBang=None, readSize=2048):
		"""
		FilteredDirWalkGenerator is a generator that walks down all directories and returns all matching filenames.

		There are several posibilities to limit returned results:
		- ignore_dirs: a list of directory names that will be excluded when traversing subdirectories (e.g. [ '.git', '.svn' ] )
		- prefixes: a list of prefixes files have to start with (e.g. ['univention-', 'preinst'])
		- suffixes: a list of suffixes files have to end with (e.g. [ '.py', '.sh', '.patch' ])
		- ignore_suffixes: files, that end with one of defined suffixes, will be ignored (e.g. ['~', '.bak'])
		- ignore_files: list of files that will be ignored (e.g. ['.gitignore', 'config.sub'])
		- ignore_debian_subdirs: boolean that defines if .../debian/* directories are ignored or not
		- reHashBang: if defined, only files are returned whose first bytes match specified regular expression
		- readSize: number of bytes that will be read for e.g. reHashBang

		example:
		>>> for fn in FilteredDirWalkGenerator(path, suffixes=['.py']):
		>>>   print fn
		"""
		self.path = path
		if ignore_dirs is None:
			self.ignore_dirs = ['.git', '.svn', 'CVS']
		else:
			self.ignore_dirs = ignore_dirs
		self.prefixes = prefixes
		self.suffixes = suffixes
		if ignore_suffixes is None:
			self.ignore_suffixes = [ '~', '.bak' ]
		else:
			self.ignore_suffixes = ignore_suffixes
		if ignore_files is None:
			self.ignore_files = ( 'config.guess', 'configure', 'libtool', 'depcomp', 'install-sh', 'config.sub', 'missing', 'config.status' )
		else:
			self.ignore_files = ignore_files
		self.ignore_debian_subdirs = ignore_debian_subdirs
		self.reHashBang = reHashBang
		self.readSize = readSize

	def __iter__(self):
		for dirpath, dirnames, filenames in os.walk( self.path ):
			# remove undesired directories
			if self.ignore_dirs:
				for item in self.ignore_dirs:
					if item in dirnames:
						dirnames.remove(item)

			# ignore all subdirectories in debian directory if requested
			if self.ignore_debian_subdirs and os.path.basename(dirpath) == 'debian':
				del dirnames[:]

			# iterate over filenames
			for filename in filenames:
				fn = os.path.join(dirpath, filename)

				# check if filename is on ignore list
				if self.ignore_files and filename in self.ignore_files:
					continue

				# check if filename ends with ignoresuffix
				if self.ignore_suffixes:
					for suffix in self.ignore_suffixes:
						if fn.endswith(suffix):
							continue

				# check if filename starts with required prefix
				if self.prefixes:
					for prefix in self.prefixes:
						if filename.startswith(prefix):
							break
					else:
						continue

				# check if filename ends with required suffix
				if self.suffixes:
					for suffix in self.suffixes:
						if filename.endswith(suffix):
							break
					else:
						continue

				if self.reHashBang:
					try:
						content = open(fn,'r').read(self.readSize)
					except IOError:
						continue
					if not self.reHashBang.search(content):
						continue

				# return complete filename
				yield fn
		return


def _test():
	"""Run simple test."""
	import re
	x = UPCFileTester()
	x.addTest( re.compile('ext[234]'), '5432-1', 'Habe ein extfs in Zeile %(startline)s und Position %(startpos)s in Datei %(basename)s gefunden.', cntmax=0)
	x.addTest( re.compile('squashfs'), '1234-5', 'Habe kein squashfs in Datei %(basename)s gefunden.', cntmin=1)
	x.open('/etc/fstab')
	msglist = x.runTests()
	for msg in msglist:
		print str(msg)
	x.open('/etc/passwd')
	msglist = x.runTests()
	for msg in msglist:
		print str(msg)


if __name__ == '__main__':
    _test()
