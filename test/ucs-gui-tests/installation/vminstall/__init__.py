import contextlib

from vminstall.installer import Installer
from vminstall.virtual_machine import VirtualMachine
import logging

logging.basicConfig()


@contextlib.contextmanager
def create_virtual_machine(language, role, environment, server, iso_image, ip_address, output_directory, dns_server=None):
	name = 'installer_test_%s-%s-%s' % (language, role, environment)
	installer_args = ['--ip', ip_address, '--dump-dir', output_directory]
	with VirtualMachine(name=name, server=server, iso_image=iso_image, interfaces=3 if environment == 'multiple_nics' else 1, disks=3 if environment == 'multiple_hdds' else 1) as vm:
		installer_args.append(vm.vnc_host)
		with Installer(args=installer_args, role=role, language=language) as installer:
			adapt_vm_config(installer, environment, dns_server)
			go_through_setup_process(installer, language, environment)
			yield (vm, installer)


def adapt_vm_config(installer, environment, dns_server):
	installer.vm_config.update_ucs_after_install = False
	installer.vm_config.install_all_additional_components = environment == 'additional_software_components'
	if environment == 'difficult_password':
		# FIXME: generate a random one! But be careful: vncdotool has problems
		# with transmitting some special keys, like '@'.
		installer.vm_config.password = "=fooBar99Extr4L4rg3Size"
	installer.vm_config.use_multiple_partitions = environment == 'multiple_partitions'
	if dns_server:
		installer.vm_config.dns_server_ip = dns_server


def go_through_setup_process(installer, language, environment):
	installer.skip_boot_device_selection()
	installer.select_language()
	installer.set_country_and_keyboard_layout()
	installer.network_setup(has_multiple_network_devices=environment == 'multiple_nics')
	installer.account_setup()
	if language in ('en',):
		installer.set_time_zone()
	installer.hdd_setup()
	installer.setup_ucs(expect_login_screen=environment == 'additional_software_components')
