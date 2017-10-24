import argparse
import logging
import univention.testing.udm as udm_test
import univention.testing.selenium as selenium_test


class BaseScreenShooter(object):
	def __init__(self, translator=None):
		self.args = self.parse_args()
		if translator is not None:
			translator.set_language(self.args.language)

		logging.basicConfig(level=logging.INFO)

		self.udm = udm_test.UCSTestUDM()
		self.selenium = selenium_test.UMCSeleniumTest(language=self.args.language)

	def __enter__(self):
		self.udm.__enter__()
		self.selenium.__enter__()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.udm.__exit__(exc_type, exc_value, traceback)
		self.selenium.__exit__(exc_type, exc_value, traceback)

	def parse_args(self):
		parser = argparse.ArgumentParser(description='Script for taking screenshots of the UMC.')
		parser.add_argument(
			'-l', '--language', dest='language', default='en', help='Two digit'
			' language code. Defines the language the screenshots will be made'
			' with. Default is "en".'
		)
		args = parser.parse_args()
		return args

	def take_screenshots(self):
		# Replace this function in your test to add functionality.
		pass
