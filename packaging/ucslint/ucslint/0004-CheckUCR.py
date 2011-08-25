# -*- coding: iso-8859-15 -*-

try:
	import univention.ucslint.base as uub
except:
	import ucslint.base as uub
import re, os

# Check 4
# 1) Nach UCR-Templates suchen und prüfen, ob die Templates in einem info-File auftauchen
# 2) In den UCR-Templates nach UCR-Variablen suchen (Code-Blöcke) und prüfen, ob diese in den info-Files registriert sind
# 3) In den UCR-Templates nach einem UCR-Header suchen
# 3.1) check, ob @%@BCWARNING=# @%@ verwendet wird
# 3.2) check, ob @%@UCRWARNING=# @%@ verwendet wird
# 4) Prüfen, ob der Pfad zum UCR-Template im File steht und stimmt
# 5) check, ob für jedes Subfile auch ein Multifile-Eintrag vorhanden ist
# 6) check, ob jede Variable/jedes VarPattern im SubFile auch am Multifile-Eintrag steht
# 7) check, ob univention-install-config-registry in debian/rules vorhanden ist, sofern debian/*.univention-config-registry existiert
# 8) check, ob univention-install-config-registry-info in debian/rules vorhanden ist, sofern debian/*.univention-config-registry-variables existiert

#
# TODO / FIXME
# - auf unbekannte Keywords in debian/*.univention-config-registry testen ==> WARNING
#




class UniventionPackageCheck(uub.UniventionPackageCheckBase):
	def __init__(self):
		uub.UniventionPackageCheckBase.__init__(self)
		self.name = '0004-CheckUCR'
		self.UCR_VALID_SPECIAL_CHARACTERS = '/_-'

	def getMsgIds(self):
		return { '0004-1': [ uub.RESULT_WARN,   'The given path in UCR header seems to be incorrect' ],
				 '0004-2': [ uub.RESULT_ERROR,  'debian/rules seems to be missing' ],
				 '0004-3': [ uub.RESULT_ERROR,  'UCR .info-file contains entry without "Type:" line' ],
				 '0004-4': [ uub.RESULT_ERROR,  'UCR .info-file contains entry of "Type: multifile" without "Multifile:" line' ],
				 '0004-5': [ uub.RESULT_ERROR,  'UCR .info-file contains entry of "Type: subfile" without "Subfile:" line' ],
				 '0004-6': [ uub.RESULT_ERROR,  'UCR .info-file contains entry of "Type: subfile" without "Multifile:" line' ],
				 '0004-7': [ uub.RESULT_ERROR,  'UCR .info-file contains entry of "Type: subfile" with multiple "Subfile:" line' ],
				 '0004-8': [ uub.RESULT_ERROR,  'UCR .info-file contains entry of "Type: subfile" with multiple "Multifile:" line' ],
				 '0004-9': [ uub.RESULT_ERROR,  'UCR .info-file contains entry without valid "Type:" line' ],
				 '0004-10': [ uub.RESULT_WARN,  'UCR .info-file contains entry of "Type: subfile" without corresponding entry of "Type: multifile"' ],
				 '0004-11': [ uub.RESULT_ERROR, 'DEPRECATED: UCR .info-file contains entry of "Type: subfile" with variables that are not registered at corresponding multifile entry' ],
				 '0004-12': [ uub.RESULT_ERROR, 'UCR template file contains UCR variables that are not registered in .info-file' ],
				 '0004-13': [ uub.RESULT_ERROR, 'UCR template file contains UCR variables with invalid characters' ],
				 '0004-14': [ uub.RESULT_WARN,  'UCR template file is found in directory conffiles/ but is not registered in any debian/*.univention-config-registry file ' ],
				 '0004-15': [ uub.RESULT_WARN,  'UCR template file is registered in UCR .info-file but cannot be found in conffiles/' ],
				 '0004-16': [ uub.RESULT_WARN,  'UCR template file contains no UCR header (please use "@%@BCWARNING=# @%@")' ],
				 '0004-17': [ uub.RESULT_WARN,  'UCR template file is registered in UCR .info-file but cannot be found in conffiles/' ],
				 '0004-18': [ uub.RESULT_WARN,  'UCR header is maybe missing in UCR multifile (please check all subfiles)' ],
				 '0004-19': [ uub.RESULT_ERROR,  'UCR .info-file contains entry of "Type: subfile" with multiple "Preinst:" line' ],
				 '0004-20': [ uub.RESULT_ERROR,  'UCR .info-file contains entry of "Type: subfile" with multiple "Postinst:" line' ],
				 '0004-21': [ uub.RESULT_ERROR,  'UCR .info-file contains entry of "Type: file" with multiple "Preinst:" line' ],
				 '0004-22': [ uub.RESULT_ERROR,  'UCR .info-file contains entry of "Type: file" with multiple "Postinst:" line' ],
				 '0004-23': [ uub.RESULT_ERROR,  'debian/*.univention-config-registry exists but debian/rules contains no univention-install-config-registry' ],
				 '0004-24': [ uub.RESULT_STYLE,	 'debian/*.univention-config-registry exists but no corresponding debian/*.univention-config-registry-variables file' ],
				 '0004-25': [ uub.RESULT_STYLE,  'debian/rules contains old univention-install-baseconfig call' ],
				 '0004-26': [ uub.RESULT_STYLE,  'DEPRECATED: debian/*.univention-config-registry-variables exists but debian/rules contains no univention-install-config-registry-info' ],
				 '0004-27': [ uub.RESULT_WARN,   'cannot open/read file' ],
				 '0004-28': [ uub.RESULT_ERROR,  'invalid formatted line without ":" found' ],
				 '0004-29': [ uub.RESULT_ERROR,  'UCR template file contains UCR variables that are not registered in .info-file' ],
				 '0004-30': [ uub.RESULT_ERROR,  'debian/*.univention-config-registry-variables contains non-UTF-8 strings' ],
				 }

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass

	def check_invalid_variable_name(self, var):
		"""
	 	Returns True if given variable name contains invalid characters
	 	"""
		for i in range(0,len(var)):
			c = var[i]
			if not c.isalpha() and not c.isdigit() and not c in self.UCR_VALID_SPECIAL_CHARACTERS:
				if c == '%' and ( i < len(var)-1 ):
					if not var[i+1] in [ 'd', 's' ]:
						return True
				else:
					return True
		return False


	def check(self, path):
		""" the real check """

		#
		# search UCR templates
		#
		conffiles = {}

		if os.path.isdir( os.path.join(path, 'conffiles') ):
			for dirpath, dirnames, filenames in os.walk( os.path.join( path, 'conffiles' ) ):
				if not '/.svn/' in dirpath and not dirpath.endswith('/.svn'):   # ignore svn files
					for fn in filenames:
						if not fn.endswith('~'):
							conffiles[ os.path.join( dirpath, fn ) ] = { 'headerfound': False, 'variables': [], 'placeholder': [], 'bcwarning': False, 'ucrwarning': False }
			self.debug('found conffiles: %s' % conffiles.keys())


		#
		# search UCR variables
		#
		reUCRVarList = [
			re.compile("""(?:baseConfig|configRegistry)\s*\[\s*['"]([^'"]+)['"]\s*\]"""),
			re.compile("""(?:baseConfig|configRegistry).has_key\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
			re.compile("""(?:baseConfig|configRegistry).get\s*\(\s*['"]([^'"]+)['"]"""),
			re.compile("""(?:baseConfig|configRegistry).is_(?:true|false)\s*\(\s*['"]([^'"]+)['"]\s*"""),
			]
		reUCRPlaceholderVar1 = re.compile('@%@([^@]+)@%@')

		for fn in conffiles.keys():
			try:
				content = open(fn,'r').read()
			except:
				self.addmsg( '0004-27', 'cannot open/read file', fn)
				continue

			for regEx in (reUCRPlaceholderVar1, ):
				flen = len(content)
				pos = 0
				while pos < flen:
					match = regEx.search( content, pos )
					if not match:
						pos = flen+1
					else:
						if match.group(1).startswith('BCWARNING='):
							conffiles[ fn ][ 'bcwarning' ] = True
						elif match.group(1).startswith('UCRWARNING='):
							conffiles[ fn ][ 'ucrwarning' ] = True
						elif not match.group(1) in conffiles[ fn ][ 'placeholder' ]:
							conffiles[ fn ][ 'placeholder' ].append( match.group(1) )
						pos = match.end()
				if conffiles[ fn ][ 'placeholder' ]:
					self.debug('found UCR placeholder variables in %s\n- %s' % (fn, '\n- '.join( conffiles[ fn ][ 'placeholder' ] ) ) )

			for regEx in reUCRVarList:
				#
				# subcheck: check if UCR header is present
				#
				if 'Warning: This file is auto-generated and might be overwritten by' in content and \
					'Warnung: Diese Datei wurde automatisch generiert und kann durch' in content:
					conffiles[fn]['headerfound'] = True

				flen = len(content)
				pos = 0
				while pos < flen:
					match = regEx.search( content, pos )
					if not match:
						pos = flen+1
					else:
						if not match.group(1) in conffiles[ fn ][ 'variables' ]:
							conffiles[ fn ][ 'variables' ].append( match.group(1) )
						pos = match.end()
				if conffiles[ fn ][ 'variables' ]:
					self.debug('found UCR variables in %s\n- %s' % (fn, '\n- '.join( conffiles[ fn ][ 'variables' ] ) ) )

			if conffiles[fn]['headerfound']:
				#
				# subcheck: check if path in UCR header is correct
				#
				reUCRHeaderFile = re.compile('#[\t ]+(/etc/univention/templates/files(/[^ \n\t\r]*?))[ \n\t\r]')
				match = reUCRHeaderFile.search(content)
				if match:
					if match.group(2) != fn[ fn.find('/conffiles/')+10 : ]:
						self.addmsg( '0004-1', 'Path in UCR header seems to be incorrect.\n      - template filename = /etc/univention/templates/files%s\n      - path in header    = %s' %
											( fn[ fn.find('/conffiles/')+10 : ], match.group(1) ), fn )


		#
		# check UCR templates
		#
		all_multifiles = {}  # { MULTIFILENAME ==> OBJ }
		all_subfiles = {}    # { MULTIFILENAME ==> [ OBJ, OBJ, ... ]
		all_files = []       # [ OBJ, OBJ, ... ]
		all_modules = []     # [ OBJ, OBJ, ... ]
		all_scripts = []     # [ OBJ, OBJ, ... ]
		all_preinst = []     # [ FN, FN, ... ]
		all_postinst = []    # [ FN, FN, ... ]
		if not os.path.exists( os.path.join(path, 'debian') ):
			self.addmsg( '0004-2', 'file is missing', 'debian/rules' )
			return
		else:
			# read debian/rules
			fn_rules = os.path.join(path, 'debian', 'rules' )
			if os.path.exists( fn_rules ):
				try:
					rules_content = open(fn_rules, 'r').read()
				except:
					rules_content = ''
			if 'univention-install-baseconfig' in rules_content:
				self.addmsg( '0004-25', 'file contains old univention-install-baseconfig call', 'debian/rules')

			# find debian/*.u-c-r and check for univention-config-registry-install in debian/rules
			reUICR = re.compile('[\n\t ]univention-install-(baseconfig|config-registry)[\n\t ]')
			reUICRI = re.compile('[\n\t ]univention-install-config-registry-info[\n\t ]')
			for f in os.listdir( os.path.join(path, 'debian') ):
				if f.endswith('.univention-config-registry') or f.endswith('.univention-baseconfig'):
					tmpfn = os.path.join(path, 'debian', '%s.univention-config-registry-variables' % f.rsplit('.')[0])
					self.debug( 'testing %s' % tmpfn )
					if not os.path.exists( tmpfn ):
						self.addmsg( '0004-24', '%s exists but corresponding %s is missing' % (f, tmpfn), tmpfn )
					else:
						# test debian/$PACKAGENAME.u-c-r-variables
						self.test_config_registry_variables(tmpfn)

					if not reUICR.search(rules_content):
						self.addmsg( '0004-23', '%s exists but debian/rules contains no univention-install-config-registry' % f, 'debian/rules' )
						break

			for f in os.listdir( os.path.join(path, 'debian') ):
				if f.endswith('.univention-config-registry') or f.endswith('.univention-baseconfig'):
					fn = os.path.join( path, 'debian', f )
					self.debug('Reading %s' % fn)
					try:
						content = open(fn, 'r').read()
					except Exception, e:
						self.addmsg( '0004-27', 'cannot open/read file', fn )
						continue

					# OBJ = { 'Type': [ STRING, ... ],
					#         'Subfile': [ STRING, ... ] ,
					#         'Multifile': [ STRING, ... ],
					#         'Variables': [ STRING, ... ]
					# or instead of "Subfile" and "Multifile" one of the following:
					#         'File': [ STRING, ... ] ,
					#         'Module': [ STRING, ... ] ,
					#         'Script': [ STRING, ... ] ,
					#       }
					multifiles = {}  # { MULTIFILENAME ==> OBJ }
					subfiles = {}    # { MULTIFILENAME ==> [ OBJ, OBJ, ... ]
					files = []       # [ OBJ, OBJ, ... ]
					modules = []     # [ OBJ, OBJ, ... ]
					scripts = []     # [ OBJ, OBJ, ... ]
					preinst = []     # [ FN, FN, ... ]
					postinst = []    # [ FN, FN, ... ]
					for part in content.split('\n\n'):
						entry = {}
						for line in part.splitlines():
							try:
								key, val = line.split(': ',1)
							except:
								self.addmsg( '0004-28', 'file contains line without ":"', fn )
								continue
							if entry.has_key(key):
								entry[key].append(val)
							else:
								entry[key] = [ val ]

						self.debug('Entry: %s' % entry)

						if not entry.has_key('Type'):
							self.addmsg( '0004-3', 'file contains entry without "Type:"', fn )
						else:

							if entry['Type'][0] == 'multifile':
								if not entry.has_key('Multifile'):
									self.addmsg( '0004-4', 'file contains multifile entry without "Multifile:" line', fn )
								else:
									multifiles[ entry['Multifile'][0] ] = entry

							elif entry['Type'][0] == 'subfile':
								if not entry.has_key('Subfile'):
									self.addmsg( '0004-5', 'file contains subfile entry without "Subfile:" line', fn )
								elif not entry.has_key('Multifile'):
									self.addmsg( '0004-6', 'file contains subfile entry without "Multifile:" line', fn )
								else:
									if len(entry['Subfile']) != 1:
										self.addmsg( '0004-7', 'file contains subfile entry with multiple "Subfile:" lines', fn )
									if len(entry['Multifile']) != 1:
										self.addmsg( '0004-8', 'file contains subfile entry with multiple "Multifile:" lines', fn )
									if len(entry.get('Preinst',[])) > 1:
										self.addmsg( '0004-19', 'file contains subfile entry with multiple "Preinst:" lines', fn )
									if len(entry.get('Postinst',[])) > 1:
										self.addmsg( '0004-20', 'file contains subfile entry with multiple "Postinst:" lines', fn )

									if subfiles.has_key( entry['Multifile'][0] ):
										subfiles[ entry['Multifile'][0] ].append( entry )
									else:
										subfiles[ entry['Multifile'][0] ] = [ entry ]

									if len(entry.get('Preinst',[])) > 0:
										preinst.append( entry['Preinst'][0] )
									if len(entry.get('Postinst',[])) > 0:
										postinst.append( entry['Postinst'][0] )

							elif entry['Type'][0] == 'file':
								files.append( entry )
								if len(entry.get('Preinst',[])) > 0:
									preinst.append( entry['Preinst'][0] )
									if len(entry['Preinst']) != 1:
										self.addmsg( '0004-21', 'file contains file entry with multiple "Preinst:" lines', fn )

								if len(entry.get('Postinst',[])) > 0:
									postinst.append( entry['Postinst'][0] )
									if len(entry['Postinst']) != 1:
										self.addmsg( '0004-22', 'file contains file entry with multiple "Postinst:" lines', fn )

							elif entry['Type'][0] == 'module':
								modules.append( entry )
							elif entry['Type'][0] == 'script':
								scripts.append( entry )
							else:
								self.addmsg( '0004-9', 'file contains entry without valid "Type:" entry (Type: %s)' % (entry['Type'][0]), fn )

					self.debug('Multifiles: %s' % multifiles)
					self.debug('Subfiles: %s' % subfiles)
					self.debug('Files: %s' % files)
					for multifile, subfileentries in subfiles.items():
						if not multifiles.has_key( multifile ):
							self.addmsg( '0004-10', 'file contains subfile entry without corresponding multifile entry.\n      - subfile = %s\n      - multifile = %s' % (subfileentries[0]['Subfile'][0], multifile), fn )
# DISABLED DUE TO BUG #15422
#						else:
#							for entry in subfileentries:
#								notregistered = []
#								for var in entry.get('Variables',[]):
#									if not var in multifiles[ multifile ].get('Variables',[]):
#										found = False
#										for mvar in multifiles[ multifile ].get('Variables',[]):
#											if '.*' in mvar:
#												regEx = re.compile(mvar)
#												if regEx.match( var ):
#													found = True
#													break
#										else:
#											notregistered.append(var)
#								if len(notregistered):
#									self.addmsg( '0004-11', 'file contains subfile entry whose variables are not registered in multifile\n	  - subfile = %s\n		- multifile = %s\n		- unregistered variables:\n			   %s' % (entry['Subfile'][0], multifile, '\n			 '.join(notregistered)), fn )

					# merge into global list
					for mfn, item in multifiles.items():
						if all_multifiles.has_key(mfn):
							all_multifiles[ mfn ].extend( item )
						else:
							all_multifiles[ mfn ] = [ item ]
					for sfn, items in subfiles.items():
						if sfn in all_subfiles:
							all_subfiles[ sfn ].extend( items )
						else:
							all_subfiles[ sfn ] = items
					all_files.extend( files )
					all_modules.extend( modules )
					all_scripts.extend( scripts )
					all_preinst.extend( preinst )
					all_postinst.extend( postinst )

		#
		# check if all variables are registered
		#
		short2conffn = {}
		for conffn in conffiles.keys():
			conffnfound = False
			shortconffn = conffn[ conffn.find('/conffiles/')+11 : ]
			short2conffn[ shortconffn ] = conffn
			objlist = []
			for mfn in all_subfiles.keys():
				objlist.extend( all_subfiles[mfn] )
			objlist.extend( all_files )
			objlist.extend( all_modules )
			objlist.extend( all_scripts )

			for obj in objlist:
				cfn = obj.get( 'File', [ None ] )[0]
				if not cfn:
					cfn = obj.get( 'Subfile', [ None ] )[0]
				if not cfn:
					cfn = obj.get( 'Module', [ None ] )[0]
				if not cfn:
					cfn = obj.get( 'Script', [ None ] )[0]
				if not cfn:
					print 'FIXME: no File or Subfile or Module or Script entry: %s' % obj
				elif cfn == shortconffn:
					conffnfound = True
					notregistered = []
					invalidUCRVarNames = set()

					mfn = obj.get('Multifile',[None])[0]
					if mfn and mfn in all_multifiles:
						# "Multifile" entry exists ==> obj is a subfile
						knownvars = set()
						# add known variables from multifile entry
						knownvars.update( all_multifiles[mfn][0].get('Variables',[]) ) # ...otherwise it contains empty list or UCR variable names
						# iterate over all subfile entries for this multifile
						for sf in all_subfiles[mfn]:
							# if subfile matches current subtemplate...
							if cfn == sf.get('Subfile',[''])[0]:
								# ...then add variables to list of known variables
								knownvars.update( sf.get('Variables',[]) )

						# check all variables against knownvars
						for var in conffiles[conffn]['variables']:
							if not var in knownvars:
								# if not found check if regex matches
								for rvar in knownvars:
									if '.*' in rvar:
										regEx = re.compile(rvar)
										if regEx.match( var ):
											break
								else:
									notregistered.append(var)

							# check for invalid UCR variable names
							if self.check_invalid_variable_name(var):
								invalidUCRVarNames.add(var)

						if len(notregistered):
							self.debug('cfn = %r' % cfn)
							self.debug('knownvars(mf+sf) = %r' % knownvars)
							self.addmsg( '0004-29', 'template file contains variables that are not registered in multifile or subfile entry:\n	- %s' % ('\n	- '.join(notregistered)), conffn)

					else:
						# no subfile ==> File, Module, Script
						for var in conffiles[conffn]['variables']:
							if not var in obj.get('Variables',[]):
								for rvar in obj.get('Variables',[]):
									if '.*' in rvar:
										regEx = re.compile(rvar)
										if regEx.match( var ):
											break
								else:
									notregistered.append(var)

							# check for invalid UCR variable names
							if self.check_invalid_variable_name(var):
								invalidUCRVarNames.add(var)

						if len(notregistered):
							self.addmsg( '0004-12', 'template file contains variables that are not registered in file entry:\n	- %s' % ('\n	- '.join(notregistered)), conffn)

					for var in conffiles[conffn]['placeholder']:
						# check for invalid UCR placeholder variable names
						if self.check_invalid_variable_name(var):
							invalidUCRVarNames.add(var)

					if invalidUCRVarNames:
						invalidUCRVarNames = list(invalidUCRVarNames)
						invalidUCRVarNames.sort()
						self.addmsg( '0004-13', 'template contains invalid UCR variable names:\n      - %s' % ('\n      - '.join(invalidUCRVarNames)), conffn )

			if not conffnfound:
				if conffn.rsplit('/')[-1] in all_preinst:
					conffnfound = True
				if conffn.rsplit('/')[-1] in all_postinst:
					conffnfound = True

			if not conffnfound:
				self.addmsg( '0004-14', 'template file is not registered in *.univention-config-registry', conffn )

		#
		# check if headers are present
		#
		# Part1: simple templates
		for obj in all_files:
			fn = obj.get('File',[None])[0]
			if not fn:
				print 'FIXME: no File entry in obj: %s' % obj
			else:
				conffn = short2conffn.get( fn, '' )
				if not conffn:
					self.addmsg( '0004-15', 'UCR template file is registered but not found in conffiles/ (1)', fn )
				else:
					if not conffiles[ conffn ]['headerfound'] and \
							not conffiles[ conffn ]['bcwarning'] and \
							not conffiles[ conffn ]['ucrwarning']:
						self.addmsg( '0004-16', 'UCR header is missing', fn )

		# Part2: subfile templates
		for mfn, items in all_subfiles.items():
			found = False
			for obj in items:
				fn = obj.get('Subfile',[None])[0]
				if not fn:
					print 'FIXME: no Subfile entry in obj: %s' % obj
				else:
					conffn = short2conffn.get( fn, '' )
					if not conffn:
						self.addmsg( '0004-17', 'UCR template file is registered but not found in conffiles/ (2)', fn )
					else:
						if conffiles[ conffn ]['headerfound']:
							found = True
						if conffiles[ conffn ]['bcwarning'] or conffiles[ conffn ]['ucrwarning']:
							found = True
			if not found:
				self.addmsg( '0004-18', 'UCR header is maybe missing in multifile %s' % mfn )


	def test_config_registry_variables(self, tmpfn):
		try:
			lines = open(tmpfn,'r').readlines()
		except:
			lines = []

		linecnt = 0
		for line in lines:
			linecnt += 1
			try:
				x = line.decode('utf-8')
			except UnicodeError:
				self.addmsg( '0004-30', 'contains invalid characters', tmpfn, linecnt )
