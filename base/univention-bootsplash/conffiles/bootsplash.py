import os


def postinst(baseConfig, changes):
	theme = baseConfig.get("bootsplash/theme", "/usr/lib/usplash/univention-theme.so")
	update = "update-alternatives --set usplash-artwork " + theme
	os.system(update)
	os.system("update-initramfs -u")
