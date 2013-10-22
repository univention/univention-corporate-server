from univention.management.console.modules.setup.netconf import SkipPhase
from univention.management.console.modules.setup.netconf.common import AddressMap
import os


class PhaseRewriteWins(AddressMap):
	"""
	Rewrite IP configuration stored in wins.dat.
	"""
	priority = 95
	filename = "/var/lib/samba/wins.dat"

	def check(self):
		super(PhaseRewriteWins, self).check()
		if not os.path.exists(self.filename):
			raise SkipPhase("No wins.dat")

	def pre(self):
		mapping = self._get_address_mapping()
		tmp_wins = "%s.%d" % (self.filename, os.getpid())
		with open(self.filename, "r") as read_wins:
			with open(tmp_wins, "w") as write_wins:
				for line in read_wins:
					try:
						name, ttl, address, flags = line.split(None, 3)
						new_ip = mapping[address]
						line = ' '.join((name, ttl, new_ip, flags))
					except (ValueError, KeyError):
						pass
					write_wins.write(line)
		self.logger.info("Updating %s'", self.filename)
		if self.changeset.no_act:
			os.unlink(tmp_wins)
		else:
			os.rename(tmp_wins, self.filename)

	def _get_address_mapping(self):
		mapping = dict((
			(str(old_ip.ip), str(new_ip.ip))
			for (old_ip, new_ip) in self.ip_changes.items()
		))
		return mapping
