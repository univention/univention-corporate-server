import os, shutil

FILE_NAME='/etc/apt/mirror.list'

def preinst(baseConfig, changes):
	if os.path.exists('%s.old' % FILE_NAME):
		os.remove('%s.old' % FILE_NAME)
	if os.path.exists(FILE_NAME):
		shutil.copyfile('%s' % FILE_NAME, '%s.old' % FILE_NAME)

def postinst(baseConfig, changes):
	if os.path.exists(FILE_NAME):
		res=open(FILE_NAME, 'r').readlines()
		if len(res) <= 1:
			os.remove(FILE_NAME)
			if os.path.exists('%s.old' % FILE_NAME):
				shutil.copyfile('%s.old' % FILE_NAME, '%s' % FILE_NAME)
		if os.path.exists('%s.old' % FILE_NAME):
			os.remove('%s.old' % FILE_NAME)
