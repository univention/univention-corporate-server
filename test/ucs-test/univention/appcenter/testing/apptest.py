#!/usr/bin/python3
from contextlib import contextmanager
import os
import os.path
import datetime
import logging
import time
import subprocess
import sys
import importlib
import tempfile
from shlex import quote
import shutil
import requests
from http.client import HTTPConnection
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
PROVIDER_PORTAL_JSON = 'https://provider-portal.software-univention.de/appcenter-selfservice/univention-appcenter-catalog.json'


def run_test_file(fname):
	with tempfile.NamedTemporaryFile(suffix='.py') as tmpfile:
		logger.info('Copying file to {}'.format(tmpfile.name))
		shutil.copy2(fname, tmpfile.name)
		with pip_modules(['pytest', 'selenium', 'xvfbwrapper', 'uritemplate']):
			importlib.reload(sys.modules[__name__])
			import pytest
			test_func = os.environ.get('UCS_TEST_ONE_TEST')
			if test_func:
				sys.exit(pytest.main([tmpfile.name + '::' + test_func, '-p', __name__, '-x', '--log-cli-level=INFO', '--pdb']))
			else:
				pass
				sys.exit(pytest.main([tmpfile.name, '-p', __name__]))


@contextmanager
def pip_modules(modules):
	if os.environ.get('UCS_TEST_NO_PIP') == 'TRUE':
		yield
	if subprocess.run(['which', 'pip3'], stdout=subprocess.DEVNULL).returncode != 0:
		raise RuntimeError('pip3 is required. Install python3-pip')
	installed = subprocess.run(['pip3', 'list', '--format=columns'], stdout=subprocess.PIPE)
	logger.info(modules)
	for line in installed.stdout.splitlines()[2:]:
		mod, ver = line.decode('utf-8').strip().split()
		if mod in modules:
			modules.remove(mod)
		if '{}=={}'.format(mod, ver) in modules:
			modules.remove('{}=={}'.format(mod, ver))
	logger.info(modules)
	if modules:
		logger.info('Installing modules via pip3')
		logger.info('  {}'.format(' '.join(modules)))
		subprocess.check_output(['pip3', 'install'] + modules)
	try:
		yield
	finally:
		if modules:
			logger.info('Uninstalling modules via pip3')
			subprocess.check_output(['pip3', 'uninstall', '--yes'] + modules)


@contextmanager
def xserver():
	if os.environ.get('DISPLAY'):
		display = os.environ['DISPLAY'].split(':')[1]
		yield display
	else:
		from xvfbwrapper import Xvfb
		with Xvfb(width=1920, height=1080) as xvfb:
			yield xvfb.new_display


def ffmpg_start(capture_video, display):
	process = subprocess.Popen(['ffmpeg', '-y', '-video_size', '1920x1080', '-framerate', '30', '-f', 'x11grab', '-i', ':{}'.format(display), '-c:v', 'libx264', '-crf', '0', capture_video], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	return process.pid


def ffmpg_stop(pid):
	subprocess.Popen(['kill', str(pid)])


def is_local():
	return os.path.exists('/usr/sbin/univention-upgrade')


class Session(object):
	def __init__(self, display_num, base_url, screenshot_path, driver):
		self.display_num = display_num
		self.base_url = base_url
		self.screenshot_path = screenshot_path
		self.driver = driver
		self.ucs_root_ca = '/etc/univention/ssl/ucsCA/CAcert.pem'
		if os.path.isfile(self.ucs_root_ca) and not os.environ.get('UCS_TEST_APPS_ADD_CERT', 'yes') == 'no':
			self.add_ucs_root_ca_to_chrome_cert_store()

	def add_ucs_root_ca_to_chrome_cert_store(self):
		# add ucs root ca to chromiums cert store
		# certutil -L -d sql:.pki/nssdb/
		# certutil -A -n "UCS root CA" -t "TCu,Cu,Tu" -i /etc/univention/ssl/ucsCA/CAcert.pem -d sql:.pki/nssd
		cert_store = os.path.join(os.environ['HOME'], '.pki', 'nssdb')
		if not os.path.isdir(cert_store):
			os.makedirs(cert_store)
		import_cert = ['certutil', '-A', '-n', 'UCS root CA', '-t', 'TCu,Cu,Tu', '-i', self.ucs_root_ca, '-d', 'sql:{}'.format(cert_store)]
		subprocess.check_output(import_cert)

	def __enter__(self):
		yield self

	def __exit__(self, exc_type, exc_value, traceback):
		self.driver.quit()

	def __del__(self):
		self.driver.quit()

	@contextmanager
	def capture(self, name):
		filename = self._new_filename(name, 'mkv')
		pid = ffmpg_start(filename, self.display_num)
		try:
			yield
		finally:
			ffmpg_stop(pid)
			self.save_screenshot(name)

	def wait_until_clickable(self, css):
		from selenium.webdriver.common.by import By
		from selenium.webdriver.support.ui import WebDriverWait
		from selenium.webdriver.support import expected_conditions as EC
		WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))

	def wait_until_clickable_and_click(self, css):
		self.wait_until_clickable(css)
		self.click_element(css)

	def wait_until_gone(self, css):
		from selenium.webdriver.common.by import By
		from selenium.webdriver.support.ui import WebDriverWait
		from selenium.webdriver.support import expected_conditions as EC
		WebDriverWait(self.driver, 10).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, css)))

	def goto_portal(self):
		self.get('/univention/portal')
		time.sleep(3)
		if self.find_first('span.umcApplianceReadmeCloseButton'):
			self.click_element('span.umcApplianceReadmeCloseButton')
		# open side menu
		self.wait_until_clickable_and_click('#header-button-menu')
		time.sleep(3)
		# choose language
		for elem in self.find_all('.portal-sidenavigation__menu .menu-item'):
			print('menu -%s-' % elem.text)
			if 'change language' in elem.text.lower():
				elem.click()
				time.sleep(3)
				break
		else:
			raise RuntimeError('Could not find "Change Language" in portal sidemenu')
		# choose english
		for elem in self.find_all('.portal-sidenavigation__menu-item--show'):
			print('sub -%s-' % elem.text)
			if 'english' in elem.text.lower():
				elem.click()
				time.sleep(3)
				break
		else:
			raise RuntimeError('Could not find "English" in portal sidemenu')
		# close side menu
		self.wait_until_clickable_and_click('#header-button-menu')

	def portal_login(self, username, password):
		self.wait_until_clickable_and_click('#header-button-menu')
		self.wait_until_clickable_and_click('#loginButton')
		self.enter_input('username', username)
		self.enter_input('password', password)
		self.enter_return()

	def click_portal_tile(self, name):
		from selenium.common.exceptions import NoSuchElementException
		elements = self.find_all('.portal-tile__name')
		for element in elements:
			print('-%s- -> %s' % (element.text, name))
			if element.text == name:
				self.driver.execute_script("arguments[0].click();", element)
				time.sleep(2)
				try:
					# iframe mode
					self.driver.switch_to.frame(self.driver.find_element_by_xpath('//iframe[@class="portal-iframe__iframe"]'))
				except NoSuchElementException:
					# tab mode
					self.change_tab(-1)
				break
		else:
			raise RuntimeError('Could not find {}'.format(name))

	@contextmanager
	def switched_frame(self, css):
		iframe = self.assert_one(css)
		self.driver.switch_to.frame(iframe)
		yield
		self.driver.switch_to.default_content()

	def get(self, url):
		if url.startswith('/'):
			url = self.base_url + url
		self.driver.get(url)

	def get_current_url(self):
		return self.driver.current_url

	def reload(self):
		self.driver.refresh()

	def find_all(self, css):
		logger.info("Searching for %r", css)
		return self.driver.find_elements_by_css_selector(css)

	def find_all_below(self, element, css):
		return element.find_elements_by_css_selector(css)

	def find_first(self, css):
		elements = self.find_all(css)
		logger.info("Found %d elements", len(elements))
		if len(elements) == 0:
			return None
		return elements[0]

	def assert_one(self, css):
		elements = self.find_all(css)
		assert len(elements) == 1, 'len(elements) == {}'.format(len(elements))
		return elements[0]

	def assert_one_below(self, element, css):
		elements = self.find_all_below(element, css)
		assert len(elements) == 1, 'len(elements) == {}'.format(len(elements))
		return elements[0]

	def click_element(self, css):
		self.assert_one(css).click()

	def click_element_below(self, element, css):
		self.assert_one_below(element, css).click()

	def change_tab(self, idx):
		self.driver.switch_to.window(self.driver.window_handles[idx])

	def close_tab(self):
		self.driver.close()

	def enter_input(self, input_name, value):
		self.enter_input_element('[name={}]'.format(input_name), value)

	def enter_input_element(self, css, value):
		from selenium.common.exceptions import InvalidElementStateException
		elem = self.assert_one(css)
		try:
			elem.clear()
		except InvalidElementStateException:
			pass
		elem.send_keys(value)

	def enter_return(self, css=None):
		from selenium.webdriver.common.keys import Keys
		if css:
			self.enter_input_element(css, Keys.RETURN)
		else:
			self.send_keys(Keys.RETURN)

	def enter_shift_tab(self):
		from selenium.webdriver.common.keys import Keys
		from selenium.webdriver import ActionChains
		action = ActionChains(self.driver)
		action.key_down(Keys.SHIFT).send_keys(Keys.TAB).key_up(Keys.SHIFT)
		action.perform()

	def enter_tab(self):
		from selenium.webdriver.common.keys import Keys
		self.send_keys(Keys.TAB)

	def drag_and_drop(self, source, target):
		from selenium.webdriver import ActionChains
		action = ActionChains(self.driver)
		action.drag_and_drop(source, target)

	def send_keys(self, keys):
		from selenium.webdriver import ActionChains
		action = ActionChains(self.driver)
		action.send_keys(keys).perform()

	def _new_filename(self, name, ext):
		timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
		os.makedirs(self.screenshot_path, exist_ok=True)
		return os.path.join(self.screenshot_path, '%s_%s.%s' % (name, timestamp, ext))

	def save_screenshot(self, name):
		filename = self._new_filename(name, 'png')
		logger.info('Saving screenshot %r', filename)
		self.driver.save_screenshot(filename)
		return filename

	@classmethod
	def chrome(cls, display_num, base_url, screenshot_path):
		from selenium import webdriver
		options = webdriver.ChromeOptions()
		options.add_argument('--no-sandbox')  # chrome complains about being executed as root
		if os.environ.get('UCS_TEST_SELENIUM_IGNORE_CERTS'):
			options.add_argument('--ignore-certificate-errors')
		driver = webdriver.Chrome(options=options)
		return cls(display_num, base_url, screenshot_path, driver)

	@classmethod
	@contextmanager
	def running_chrome(cls, base_url, screenshot_path):
		with xserver() as display:
			obj = cls.chrome(display, base_url, screenshot_path)
			obj.driver.maximize_window()
			with obj:
				yield obj


try:
	import pytest
except ImportError:
	pass
else:
	@pytest.fixture(scope='session')
	def config():
		"""Test wide Configuration aka UCR
		Used to get some defaults if not environment variables are
		given. But if UCR is not avaiable, returns an empty dict...
		"""
		try:
			from univention.config_registry import ConfigRegistry
			ucr = ConfigRegistry()
			ucr.load()
			return dict(ucr)
		except ImportError:
			return {}

	@pytest.fixture(scope='session')
	def hostname(config):
		"""Hostname to test against"""
		ret = os.environ.get('UCS_TEST_HOSTNAME')
		if ret is None:
			if config:
				ret = 'https://{hostname}.{domainname}'.format(**config)
			else:
				logger.warning('$UCS_TEST_HOSTNAME not set')
				ret = 'http://localhost'
		return ret

	@pytest.fixture(scope='session')
	def fqdn(config):
		"""fqdn to test against"""
		ret = os.environ.get('UCS_TEST_HOSTNAME')
		if ret is None:
			if config:
				ret = '{hostname}.{domainname}'.format(**config)
			else:
				logger.warning('$UCS_TEST_HOSTNAME not set')
				ret = 'localhost'
		else:
			ret = urlparse(ret).netloc
		return ret

	@pytest.fixture(scope='session')
	def admin_username(config):
		"""Username of the Admin account"""
		ret = os.environ.get('UCS_TEST_ADMIN_USERNAME')
		if not ret:
			ret = config.get('tests/domainadmin/account')
			if ret:
				ret = ret.split(',')[0].split('=')[-1]
			else:
				ret = 'Administrator'
		return ret

	@pytest.fixture(scope='session')
	def admin_password(config):
		"""Password of the Admin account"""
		ret = os.environ.get('UCS_TEST_ADMIN_USERNAME')
		ret = os.environ.get('UCS_TEST_ADMIN_PASSWORD')
		if not ret:
			ret = config.get('tests/domainadmin/pwd', 'univention')
		return ret

	@pytest.fixture(scope='session')
	def umc(hostname, admin_username, admin_password):
		umc_lib = os.environ.get('UCS_TEST_UMC_CLIENT_LIB', 'univention.testing._umc')
		try:
			umc_lib = importlib.import_module(umc_lib)
		except ImportError:
			logger.critical('Could not import {}. Maybe set $UCS_TEST_UMC_CLIENT_LIB'.format(umc_lib))
			raise
		Client = umc_lib.Client
		scheme, hostname = hostname.split('//')
		if scheme == 'http:':
			Client.ConnectionType = HTTPConnection
		client = Client(hostname=hostname, username=admin_username, password=admin_password, useragent='UCS/ucs-test')
		return client

	@pytest.fixture
	def ucs_call(fqdn):
		def _run(args):
			logger.info('Running: %r' % (args,))
			if is_local():
				logger.info('... locally')
				subprocess.run(args, check=True)
			else:
				logger.info('... with SSH, hope you have added your SSH keys to %s?', fqdn)
				subprocess.run(['ssh', fqdn] + [quote(arg) for arg in args], check=True)
		return _run

	@pytest.fixture
	def ucr(umc):
		class UCR(object):
			def __init__(self, client):
				self.client = client
				self._old = {}

			def get(self, key):
				logger.info('Getting UCRV %s', key)
				response = self.client.umc_command('ucr/get', [key])
				value = response.result[0]['value']
				logger.info('Found %r', value)
				return value

			def set(self, updates, revert_afterwards=True):
				if revert_afterwards:
					keys = list(updates.keys())
					response = self.client.umc_command('ucr/get', keys)
					old = zip(keys, [res.get('value') for res in response.result])
					for k, v in dict(old).items():
						if k not in self._old:
							logger.info('Saving %r=%r for later revert', k, v)
							self._old[k] = v
				logger.info('Updating %r', updates)
				self.client.umc_command('ucr/put', [{'object': {'key': k, 'value': v}} for k, v in updates.items() if v is not None])
				self.client.umc_command('ucr/remove', [{'object': k} for k, v in updates.items() if v is None])

		ucr_module = UCR(umc)
		yield ucr_module
		if ucr_module._old:
			ucr_module.set(ucr_module._old, revert_afterwards=False)

	@pytest.fixture(scope='session')
	def appcenter(umc, fqdn):
		class AppCenter(object):
			def __init__(self, client):
				self.client = client

			def install_newest(self, app_id):
				app_version = None
				if '=' in app_id:
					app_id, app_version = tuple(app_id.split('=', 1))
				else:
					app_version = self.get_published_version(app_id)
				app = self.get(app_id)
				# overwright version with published or given version
				if app_version:
					app['version'] = app_version
				app_function = None
				if app['is_installed']:
					logger.info('App already installed')
					if 'candidate_version' in app:
						logger.info('Upgrading App...')
						app_function = 'upgrade'
				else:
					logger.info('Installing App...')
					app_function = 'install'
				if not app_function:
					return app
				data = {
					"action": app_function,
					"auto_installed": [],
					"hosts": {fqdn: app_id},
					"apps": ["{}={}".format(app_id, app['version'])],
					"dry_run": False,
					"settings": {app_id: {}},
				}
				response = self.client.umc_command("appcenter/run", data)
				progress_id = response.result['id']
				finished = False
				i = 0
				while not finished:
					time.sleep(5)
					i += 1
					if i > 600:
						raise RuntimeError('Did not finish within 20 minutes')
					result = self.client.umc_command('appcenter/progress', {'progress_id': progress_id}).result
					finished = result.get('finished')
					assert not result.get('serious_problems')
					for message in result.get('intermediate', []):
						logger.info(message)
				app = self.get(app_id)
				assert app['is_installed']
				return app

			def get_published_version(self, app_id):
				logger.info('Retrieving published App {}'.format(app_id))
				r = requests.get(PROVIDER_PORTAL_JSON)
				for app in r.json():
					if app_id == app['id']:
						return app['version']
				return None

			def get(self, app_id):
				logger.info('Retrieving App {}'.format(app_id))
				response = self.client.umc_command('appcenter/get', {'application': app_id})
				return response.result

		return AppCenter(umc)

	@pytest.fixture(scope='session')
	def udm(hostname, config, admin_username, admin_password):
		"""A UDM instance (REST client)"""
		rest_lib = os.environ.get('UCS_TEST_REST_CLIENT_LIB', 'univention.testing._udm_rest')
		try:
			rest_lib = importlib.import_module(rest_lib)
		except ImportError:
			logger.critical('Could not import {}. Maybe set $UCS_TEST_REST_CLIENT_LIB'.format(rest_lib))
			raise
		uri = os.environ.get('UCS_TEST_UDM_URI')
		if not uri:
			if config:
				hostname = 'https://{}'.format(config.get('ldap/master'))
			else:
				logger.warning('$UCS_TEST_UDM_URI not set')
			uri = '{}/univention/udm/'.format(hostname)
		udm = rest_lib.UDM.http(uri, admin_username, admin_password)
		return udm

	@pytest.fixture(scope='session')
	def users(udm):
		user_mod = udm.get('users/user')
		users = {}
		user_id_cache = {'X': 1}  # very elegant...

		def _users(user_id=None, attrs={}):
			# create mail domain
			if 'mailPrimaryAddress' in attrs:
				my_domain = attrs['mailPrimaryAddress'].split('@', 1)[1]
				mail_domain_mod = udm.get('mail/domain')
				for mail_domain in mail_domain_mod.search(opened=True):
					if mail_domain.properties['name'] == my_domain:
						break
				else:
					md = mail_domain_mod.new()
					md.properties['name'] = my_domain
					md.save()
			username = attrs.get('username')
			if username is None:
				if user_id is None:
					user_id = user_id_cache['X']
					user_id_cache['X'] += 1
				username = 'ucs-test-user-{}'.format(user_id)
			if username not in users:
				user = user_mod.new()
				user.properties.update(attrs)
				if user.properties['username'] is None:
					user.properties['username'] = username
				if user.properties['firstname'] is None:
					user.properties['firstname'] = 'John'
				if user.properties['lastname'] is None:
					user.properties['lastname'] = user.properties['username']
				if user.properties['password'] is None:
					user.properties['password'] = 'univention'
				user.save()
				users[username] = user
			else:
				if attrs:
					user = users[username]
					user.reload()
					user.properties.update(attrs)
					user.save()
			user = users[username]
			user.reload()
			return user
		try:
			yield _users
		finally:
			for user in users.values():
				user.delete()

	@pytest.fixture
	def new_user(users):
		"""Creates a new user and cleans up"""
		user = users()
		return user

	@pytest.fixture(scope='session')
	def db_conn():
		"""A database connection object (sqlalchemy)"""
		import sqlalchemy
		ret = os.environ.get('UCS_TEST_DB_URI')
		if not ret:
			logger.warning('$UCS_TEST_DB_URI not set')
			raise ValueError('Need $UCS_TEST_DB_URI')
		engine = sqlalchemy.create_engine(ret)
		with engine.connect() as conn:
			yield conn

	@pytest.fixture(scope='session')
	def selenium_base_url(hostname):
		"""Base URL for selenium"""
		ret = os.environ.get('UCS_TEST_SELENIUM_BASE_URL')
		if ret is None:
			logger.warning('$UCS_TEST_SELENIUM_BASE_URL not set')
			ret = hostname
			logger.warning('  using {}'.format(ret))
		return ret

	@pytest.fixture(scope='session')
	def selenium_screenshot_path():
		"""Path where selenium should save screenshots"""
		ret = os.environ.get('UCS_TEST_SELENIUM_SCREENSHOT_PATH')
		if ret is None:
			logger.warning('$UCS_TEST_SELENIUM_SCREENSHOT_PATH not set')
			ret = 'selenium'
			logger.warning('  using {}'.format(ret))
		return os.path.abspath(ret)

	@pytest.fixture
	def test_logger():
		"""Our logger instance so you can print some info for pytest"""
		return logger

	@pytest.fixture
	def chrome(selenium_base_url, selenium_screenshot_path):
		"""A running chrome instance, controllable by selenium"""
		with Session.running_chrome(selenium_base_url, selenium_screenshot_path) as c:
			yield c
