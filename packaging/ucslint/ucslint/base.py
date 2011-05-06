# -*- coding: iso-8859-15 -*-
#

import re

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
