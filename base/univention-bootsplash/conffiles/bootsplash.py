import os

def postinst(baseConfig, changes):
	theme = changes.get("bootsplash/theme", False)
	if theme and type(()) == type(theme):
		old, new = theme
		if new:
			os.system("plymouth-set-default-theme %s" % new)
			os.system("update-initramfs -u")
