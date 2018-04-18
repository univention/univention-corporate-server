"""
.. module:: simplesquid
	:platform: Unix

.. moduleauthor:: Ammar Najjar <najjar@univention.de>
"""
import os
from subprocess import call
import time
import univention.testing.ucr as ucr_test
import univention.testing.utils as utils


def get_lines_containing(filename, string):
	with open(filename) as input_file:
		return [line for line in input_file if string in line]


class SimpleSquid(object):
	"""
	:param path: path for the executable squid
	:type path: str
	"""

	def __init__(self, path=None):
		self.path = path if path else "/etc/init.d/squid"
		self.basename = os.path.basename(self.path)
		self.conf = "/etc/%s/squid.conf" % self.basename

	def restart(self):
		"""Trying to restart"""
		print 'Restarting squid'
		return call([self.path, "restart"])

	def reconfigure(self):
		"""Reconfigure squid (faster than a restart)"""
		print("Reconfigure squid")
		return call([self.basename, "-k", "reconfigure"])

	def is_not_running(self):
		"""Check the current running status\n
		:return boolean : True if not running, Flase if running
		"""
		return call([self.basename, "-k", "check"])

	def is_running(self, tolerance=5):
		"""Check if it is running within the given tolerance of time\n
		Use when waiting for squid to be running.\n
		:param tolerance: time duration
		:type tolerance: int for seconds
		:return boolean:True if running, False if not running
		"""
		result = False
		# Give 5 seconds max for squid to be ready
		for interval in xrange(tolerance):
			if self.is_not_running():
				result = False
				time.sleep(1)
			else:
				result = True
				break
		return result

	def redirector_is(self, expected_redirector):
		"""Check if the redirector is the same as the passed parameter\n
		:param expected_redirector: in the config file
		:type expected_redirector: string
		:return boolean:True if match, False if not match
		"""
		result = False
		with ucr_test.UCSTestConfigRegistry():
			config_lines = get_lines_containing(self.conf, 'url_rewrite_program')
			if config_lines:
				# in config file the first line setting the redirector is activated
				config_line = config_lines[0]
				result = ('url_rewrite_program %s\n' % (expected_redirector,) == config_line)
			else:
				utils.fail("Squid config redirector line does not exist")
		return result
