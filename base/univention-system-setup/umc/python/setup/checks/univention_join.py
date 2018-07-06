import os
import subprocess

import univention.config_registry
from univention.lib.i18n import Translation
from univention.management.console.modules import UMC_Error

UCR = univention.config_registry.ConfigRegistry()
UCR.load()
_ = Translation('univention-management-console-module-setup').translate

def set_role_and_check_if_join_will_work(role, master_fqdn, admin_username, admin_password):
	with open('/root/tmp_pwd', 'w') as password_file:
		password_file.write(admin_password)
	UCR['server/role'] = role
	UCR.save()

	try:
		subprocess.check_call([
			'univention-join',
			'-dcname', master_fqdn,
			'-dcaccount', admin_username,
			'-dcpwd', '/root/tmp_pwd',
			'-checkPrerequisites'
		])
	except subprocess.CalledProcessError:
		raise UMC_Error(_(
			"univention-join will not work with the given setup. "
			"Check /var/log/univention/join.log to see what went wrong."
		))
	finally:
		os.remove('/root/tmp_pwd')
