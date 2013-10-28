from univention.management.console.modules.setup.netconf import SkipPhase
from univention.management.console.modules.setup.netconf.common import AddressMap
import os


class PhaseRewritePxe(AddressMap):
	"""
	Rewrite IP configuration of PXE boot.
	"""
	priority = 95
	dirname = "/var/lib/univention-client-boot/pxelinux.cfg"

	def check(self):
		super(PhaseRewritePxe, self).check()
		if not os.path.exists(self.dirname):
			raise SkipPhase("No '%s'" % (self.dirname,))

	def pre(self):
		mapping = dict((
			(
				"%s:" % (old_ip.ip,),
				"%s:" % (new_ip.ip,),
			) for (old_ip, new_ip) in self.ipv4_changes().items()
		))
		for filename in os.listdir(self.dirname):
			pathname = os.path.join(self.dirname, filename)
			self._rewrite_pxe(pathname, mapping)

	def _rewrite_pxe(self, pathname, mapping):
		self.logger.debug("Processing '%s'...", pathname)
		with open(pathname, "r") as read_pxe:
			orig = config = read_pxe.read()
		for (old_ip, new_ip) in mapping.items():
			config = config.replace(old_ip, new_ip)
		if orig == config:
			self.logger.debug("No change in %s", pathname)
			return
		self.logger.debug("Updating '%s'...", pathname)
		if self.changeset.no_act:
			return
		with open(pathname, "w") as write_pxe:
			write_pxe.write(config)
