# -*- coding: iso-8859-15 -*-

try:
	import univention.ucslint.base as uub
except:
	import ucslint.base as uub
import re
import os

# 1) check if translation strings are correct; detect something like  _('foo %s bar' % var)  ==> _('foo %s bar') % var
# 2) check if all translation strings are translated in de.po file

class UniventionPackageCheck(uub.UniventionPackageCheckBase):
	def __init__(self):
		uub.UniventionPackageCheckBase.__init__(self)
		self.name = '0008-Translations'

	def getMsgIds(self):
		return { '0008-1': [ uub.RESULT_ERROR, 'file contains construct like _("foo %s bar" % var) that cannot be translated correctly' ],
				 '0008-2': [ uub.RESULT_WARN, 'failed to open file' ],
				 '0008-3': [ uub.RESULT_ERROR, 'po-file contains "fuzzy" string' ],
				 '0008-4': [ uub.RESULT_WARN, 'po-file contains empty msg string' ],
				 '0008-5': [ uub.RESULT_ERROR, 'po-file contains no character set definition' ],
				 '0008-6': [ uub.RESULT_ERROR, 'po-file contains invalid character set definition' ],
				 }

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass

	def check(self, path):
		""" the real check """

		fnlist_joinscripts = {}

		if not os.path.isdir( os.path.join(path, 'debian') ):
			print "ERROR: directory %s does not exist!" % path
			return

		regEx1 = re.compile("""^(?:[^'"#\n]| # non string, non comment prefix
				(?: # matched strings
					('''|""\").*?(?<!\\\\)\\1
					|'(?:[^'\n]|\\\\')*?'
					|"(?:[^"\n]|\\\\")*?"
				))*
				[([{\s,:](_\\(\s* # translation
				(?: # matched strings
					('''|""\").*?(?<!\\\\)\\3
					|'(?:[^'\n]|\\\\')*?'
					|"(?:[^"\n]|\\\\")*?"
				)\s*%\s*	# substitution
				(?:[^)]+\\))?)""", re.DOTALL | re.MULTILINE | re.VERBOSE)

		py_files = []
		po_files = []
		for dirpath, dirnames, filenames in os.walk( path ):
			try: dirnames.remove('.svn') # prune svn directory
			except ValueError: pass
			for fn in filenames:
				if fn.endswith('.py'):
					py_files.append( os.path.join( dirpath, fn ) )
				if fn.endswith('.po'):
					po_files.append( os.path.join( dirpath, fn ) )

		for fn in py_files:
			try:
				f = open(fn, 'r')
				try:
					content = f.read()
				finally:
					f.close()
			except IOError:
				self.addmsg( '0008-2', 'failed to open and read file', fn )
				continue
			self.debug('testing %s' % fn)
			for regex in (regEx1,):
				flen = len(content)
				pos = 0
				while pos < flen:
					match = regex.search( content, pos )
					if not match:
						pos = flen+1
					else:
						line = content.count('\n', 0, match.start()) + 1
						pos = match.end()
						self.addmsg( '0008-1', 'substitutes before translation: %s' % match.group(2), fn, line)

		regEx1 = re.compile('\n#.*?fuzzy')
		regEx2 = re.compile('msgstr ""\n\n', re.DOTALL)
		regExCharset = re.compile('"Content-Type: text/plain; charset=(.*?)\\\\n"', re.DOTALL)

		for fn in po_files:
			try:
				content = open(fn, 'r').read()
			except:
				self.addmsg( '0008-2', 'failed to open and read file', fn )
				continue

			match = regExCharset.search( content )
			if not match:
				self.addmsg( '0008-5', 'cannot find charset definition', fn )
			elif not match.group(1).lower() in ('utf-8'):
				self.addmsg( '0008-6', 'invalid charset (%s) defined' % match.group(1), fn )

			self.debug('testing %s' % fn)
			for regex, errid, errtxt in [ (regEx1, '0008-3', 'contains "fuzzy"'),
										  (regEx2, '0008-4', 'contains empty msgstr') ]:
				flen = len(content)
				pos = 0
				while pos < flen:
					match = regex.search( content, pos )
					if not match:
						pos = flen+1
					else:
						# match.start() + 1 ==> avoid wrong line numbers because regEx1 starts with \n
						line = content.count('\n', 0, match.start() + 1 ) + 1
						pos = match.end()
						self.addmsg( errid, errtxt, fn, line )

