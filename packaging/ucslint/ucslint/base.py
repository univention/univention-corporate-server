# -*- coding: iso-8859-15 -*-
#

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
	def __init__(self, id, msg):
		self.id = id
		self.msg = msg

	def __str__(self):
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

