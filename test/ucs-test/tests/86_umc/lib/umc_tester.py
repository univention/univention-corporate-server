import argparse
import logging
import univention.testing.udm as udm_test
import univention.testing.umc_selenium as umc_selenium_test


class BaseUMCTester(object):
	def __init__(self, login=True, translator=None):
		self.args = self.parse_args()
		if translator is not None:
			translator.set_language(self.args.language)

		logging.basicConfig(level=logging.INFO)

		self.udm = udm_test.UCSTestUDM()
		self.selenium = umc_selenium_test.UMCSeleniumTest(
			login=login,
			language=self.args.language,
			host=self.args.host
		)

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
			' language code. Defines the language the UMC will be tested'
			' with. Default is "en".'
		)
		parser.add_argument(
			'--host', dest='host', default='localhost', help='The url to the '
			'UMC, that is to be tested. Default is "localhost".'
		)
		args = parser.parse_args()
		return args

	def test_umc(self):
		# Replace this function in your test to add functionality.
		pass
