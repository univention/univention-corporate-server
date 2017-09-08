from vminstall.installer import Installer

installer_args = ['--ip', '10.200.36.61', '--dump-dir', 'screen_dumps', 'frosta.knut.univention.de:2']
with Installer(args=installer_args, role='master', language='de') as installer:
	installer.skip_boot_device_selection()
	installer.select_language()
	installer.set_country_and_keyboard_layout()
	# Steps are missing, but I only want to test the beginning of the setup anyway
