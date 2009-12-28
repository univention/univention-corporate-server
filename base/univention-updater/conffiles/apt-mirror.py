import os, shutil

FILE_NAME='/etc/apt/mirror.list'

def preinst(baseConfig, changes):
	if os.path.exists('%s.old' % FILE_NAME):
		os.remove('%s.old' % FILE_NAME)
	if os.path.exists(FILE_NAME):
		shutil.copyfile('%s' % FILE_NAME, '%s.old' % FILE_NAME)
	if 'local/repository' in set(changes):
		""" Immediately resolve pending policy changes if local/repository is changed (Bug #16646) """
		os.system('/usr/lib/univention-directory-policy/univention-policy-set-repository-server >>/var/log/univention/repository.log')

def postinst(baseConfig, changes):
	if os.path.exists(FILE_NAME):
		res=open(FILE_NAME, 'r').readlines()
		if len(res) <= 1:
			os.remove(FILE_NAME)
			if os.path.exists('%s.old' % FILE_NAME):
				shutil.copyfile('%s.old' % FILE_NAME, '%s' % FILE_NAME)
		if os.path.exists('%s.old' % FILE_NAME):
			os.remove('%s.old' % FILE_NAME)
