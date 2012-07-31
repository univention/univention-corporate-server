# -*- coding: iso-8859-15 -*-

try:
	import univention.ucslint.base as uub
except ImportError:
	import ucslint.base as uub
import re
import os


def containsHashBang(path):
	try:
		fp = open(path, 'r')
	except IOError, e:
		return False
	for line in fp:
		if '#!/bin/sh' in line or '#!/bin/bash' in line:
			fp.close()
			return True
	return False



class UniventionPackageCheck(uub.UniventionPackageCheckDebian):
	def __init__(self):
		super(UniventionPackageCheck, self).__init__()
		self.name = '0017-Shell'

	def getMsgIds(self):
		return { '0017-1': [ uub.RESULT_WARN,   'script contains unquoted calls of eval $(ucr shell)' ]}

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass


	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		REucr_shell = re.compile('eval\s+(`|[$][(])\s*(/usr/sbin/)?(ucr|univention-baseconfig|univention-config-registry)\s+shell\s*[^`)]*[`)]\s*')

		#
		# search shell scripts
		#
		scripts = []
		for root, dirs, files in os.walk('.'):
			for file in files:
				script_path = file
				if not root.startswith('.'):
					script_path = '%s%s' % (root, script_path)
				if file.endswith('.sh') or containsHashBang(script_path):
					scripts.append(script_path)
					self.debug('found %s' % script_path)



		#
		# check scripts for unquoted eval $(ucr shell) calls
		#
		for script in scripts:
			try:
				fp = open(script, 'r')
			except IOError, e:
				self.debug('could not look for unquoted calls of eval $(ucr shell) in %s' % script)
			else:
				lines = fp.readlines()
				fp.close()
				for i in range(len(lines)):
					if REucr_shell.search(lines[i]):
						self.addmsg('0017-1', '%s, line %i: unquoted call of eval $(ucr shell)' % (script, i+1))
					
