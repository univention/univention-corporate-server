import os, shutil

FILE_NAME='/etc/apt/sources.list.d/18_ucs-online-security.list'

def preinst(baseConfig, changes):
	if os.path.exists('%s.old' % FILE_NAME):
		os.remove('%s.old' % FILE_NAME)
	if os.path.exists(FILE_NAME):
		shutil.copyfile('%s' % FILE_NAME, '%s.old' % FILE_NAME)

def postinst(baseConfig, changes):
	if os.path.exists(FILE_NAME):
		# This check is necessary otherwise this handler will reconstruct the
		# old file because the new file will be empty. 
		if not baseConfig['version/security-patchlevel'] == '0':
			res=open(FILE_NAME, 'r').readlines()
			if len(res) <= 1:
				os.remove(FILE_NAME)
				if os.path.exists('%s.old' % FILE_NAME):
					shutil.copyfile('%s.old' % FILE_NAME, '%s' % FILE_NAME)
			if os.path.exists('%s.old' % FILE_NAME):
				os.remove('%s.old' % FILE_NAME)
			pass
		else:
			if os.path.exists('%s.old' % FILE_NAME):
				os.remove('%s.old' % FILE_NAME)
	pass

