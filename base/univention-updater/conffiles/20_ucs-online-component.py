import os, shutil

FILE_NAME='/etc/apt/sources.list.d/20_ucs-online-component.list'

def preinst(baseConfig, changes):
	if os.path.exists('%s.old' % FILE_NAME):
		os.remove('%s.old' % FILE_NAME)
	if os.path.exists(FILE_NAME):
		shutil.copyfile('%s' % FILE_NAME, '%s.old' % FILE_NAME)

def postinst(baseConfig, changes):
	if os.path.exists(FILE_NAME):
		check = False
		for key in baseConfig.keys():
			if key.startswith('repository/online/component/'):
				component_part = key.split('repository/online/component/')[1]
				if component_part.find('/') == -1 and baseConfig[key].lower() in [ 'true', 'yes', 'enabled', '1']:
					check = True
					break

		if check:
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

