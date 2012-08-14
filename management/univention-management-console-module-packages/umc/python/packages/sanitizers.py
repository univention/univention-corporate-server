from univention.management.console.modules.sanitizers import *

import univention.management.console as umc
_ = umc.Translation('univention-management-console-module-packages').translate

class AptFunctionSanitizer(Sanitizer):
	def _sanitize(self, value, name, further_fields):
		fncarg = {
			'install' : 'install',
			'upgrade' : 'install',
			'uninstall' : 'remove',
		}
		try:
			return fncarg[value]
		except KeyError:
			self.raise_validation_error(_('Should be in %r') % fncarg.keys())

