from subprocess import call


def postinst(baseConfig, changes):
	theme = changes.get("bootsplash/theme", False)
	try:
		old, new = theme
	except (TypeError, ValueError):
		pass
	else:
		if new:
			call(("plymouth-set-default-theme", "--rebuild-initrd", new))
