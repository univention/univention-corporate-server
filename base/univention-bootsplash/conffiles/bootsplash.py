import os


def postinst(baseConfig, changes):
	os.system("update-initramfs -u")
