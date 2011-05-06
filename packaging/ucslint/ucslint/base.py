# -*- coding: iso-8859-15 -*-
#

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
	def __init__(self, id, msg=None, filename=None, line=None, pos=None):
		self.id = id
		self.msg = msg
		self.filename = filename
		self.line = line
		self.pos = pos

	def __str__(self):
		s = ''
		if self.filename:
			s = '%s' % self.filename
			if self.line != None:
				s += ':%s' % self.line
				if self.pos != None:
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

	def getMsgIds(self):
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

class UCSLintException(Exception): pass

class DebianControlNotEnoughSections(UCSLintException): pass

class DebianControlParsingError(UCSLintException): pass

class FailedToReadFile(UCSLintException):
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
			if lines[i].startswith(' ') or lines[i].startswith('\t'):
				if not inDescription:
					lines[i-1] += ' %s' % lines[i].lstrip(' \t')
					del lines[i]
					continue
			i += 1

		# split lines into dictionary
		for line in lines:
			if not ':' in line:
				raise DebianControlParsingError()
			key, val = line.split(': ',1)
			self[ key ] = val


class ParserDebianControl(object):
	def __init__(self, filename):
		self.filename = filename
		self.source_section = None
		self.binary_sections = []

		try:
			content = open(self.filename, 'r').read()
		except:
			raise FailedToReadFile(self.filename)

		parts = content.split('\n\n')
		if len(parts) < 2:
			raise DebianControlNotEnoughSections()

		self.source_section = DebianControlEntry(parts[0])
		for part in parts[1:]:
			self.binary_sections.append( DebianControlEntry(part) )

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
		pos = sum(map(len, self.lines[:linenumber]))
		pos += linenumber
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
		if cntmin==None and cntmax==None:
			raise ValueError('cntmin or cntmax has to be set')
		self.tests.append( RegExTest( regex, msgid, msg, cntmin, cntmax) )

	def runTests(self):
		"""
		runs all given tests on loaded file and returns a list of UPCMessage objects
		"""
		if not self.filename:
			raise Exception('no file has been loaded')

		msglist = []
		linenum = 0
		for t in self.tests:
			t.cnt = 0
		# iterate over all lines
		for line in self.lines:
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
			linenum += 1

		# check if mincnt has been reached by counter - if not then add UPCMessage
		for t in self.tests:
			if t.cntmin != None and t.cnt < t.cntmin:
				msg = t.msg
				if t.formatmsg:
					msg = msg % { 'basename': self.basename, 'filename': self.filename }
					# append msg
					msglist.append( UPCMessage( t.msgid, msg=msg, filename=self.filename ) )
		return msglist

if __name__ == '__main__':
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
