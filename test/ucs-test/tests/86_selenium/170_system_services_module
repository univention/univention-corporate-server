#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: Test the 'System services' module
## packages:
##  - univention-management-console-module-services
## roles-not:
##  - basesystem
## tags:
##  - SKIP
##  - umc-producttest
## join: true
## exposure: dangerous

import psutil
import time

from univention.testing import selenium
from univention.service_info import ServiceInfo
from univention.admin import localization
from univention.testing.selenium.utils import expand_path

translator = localization.translation('ucs-test-selenium')
_ = translator.translate


class UmcError(Exception):
	pass


class UMCTester(object):

	def search(self, search_value):
		self.selenium.enter_input('pattern', search_value)
		self.selenium.submit_input('pattern')
		self.selenium.wait_until_all_standby_animations_disappeared()

	def search_and_action(self, name, action):
		self.search(name)
		self.selenium.click_grid_entry(name)
		self.selenium.click_button(action)
		self.selenium.click_button(_('OK'))
		self.selenium.wait_until_all_standby_animations_disappeared()
		#  self.search(name) # grid should autoreload

	def setup(self):
		self.srvs = ServiceInfo()
		self.selenium.do_login()
		self.selenium.open_module(_('System services'))

	def reset(self):
		# TODO This is not really a reset.
		# This justs starts all services and sets the start type to 'automatically'
		# but that should be the default anyway
		self.search('')
		self.selenium.click_element(expand_path('//*[@containsClass="dgrid-header"]//*[@containsClass="dgrid-selector"]'))
		self.selenium.click_button(_('more'))
		self.selenium.click_text(_('Start automatically'))
		self.selenium.click_button(_('OK'))
		self.selenium.wait_until_all_standby_animations_disappeared()

		self.search('')
		self.selenium.click_element(expand_path('//*[@containsClass="dgrid-header"]//*[@containsClass="dgrid-selector"]'))
		self.selenium.click_button(_('Start'))
		self.selenium.click_button(_('OK'))
		self.selenium.wait_until_all_standby_animations_disappeared()

	def test_umc(self):
		self.setup()
		self.test_start_stop_restart_all_services()
		self.test_chaning_start_type()
		self.reset()

	#
	# Code for changing start type
	#
	def test_chaning_start_type(self):
		ignore_these = [
			'apache2',
			'univention-management-console-server',
			'univention-management-console-web-server',
			'univention-welcome-screen',  # TODO do the jenkins vms for the selenium test have a display manager installed?
			'heimdal-kdc',  # TODO services['heimdal-kdc']['programs'] has mismatching output with psutil.Process.cmdline()
			'bind9',  # started automatically on reboot even if start type is manually
			'rpcbind',  # started automatically on reboot even if start type is manually
			'slapd',  # needed for login
			#  'ssh',
		]
		services = [key for key in self.srvs.services.iterkeys() if key not in ignore_these]
		if len(services) < 3:
			pass  # TODO can't test all start types at once
		count_per_start_type = len(services) / 3
		d = {}
		for idx, start_type in enumerate(('automatically', 'manually', 'never')):
			start = idx * count_per_start_type
			end = start + count_per_start_type
			d[start_type] = services[start:end]

		for start_type, services in d.iteritems():
			for service in services:
				if start_type != 'automatically':
					self.do_and_confirm_start_type_change(service, start_type)
				self.search_and_action(service, _('Stop'))

	def do_and_confirm_start_type_change(self, service, start_type):
		self.search(service)
		self.selenium.click_grid_entry(service)
		self.selenium.click_button(_('more'))
		self.selenium.click_text({
			'manually': _('Start manually'),
			'never': _('Start never'),
		}[start_type])
		self.selenium.click_button(_('OK'))
		self.selenium.wait_until_all_standby_animations_disappeared()

		grid_start_type = self.get_service_grid_start_type(service)
		wanted_start_type = {
			'manually': _('Manually'),
			'never': _('Never'),
		}[start_type]
		if grid_start_type != wanted_start_type:
			raise UmcError('Trying to change the start type of service "%s" to "%s" failed. The start type in the grid did not change' % (service, start_type))

	def get_service_grid_start_type(self, service):
		start_type_cell_xpath = expand_path('//td[@containsClass="field-service"]/descendant-or-self::*[text() = "%s"]/following::td[@containsClass="field-autostart"]/descendant-or-self::*[text() = "Automatically" or text() = "Manually" or text() = "Never"]' % service)
		return self.selenium.driver.find_element_by_xpath(start_type_cell_xpath).text

	#
	# Code for starting, stopping, restarting
	#
	def test_start_stop_restart_all_services(self):
		ignore_these = [
			'apache2',
			'univention-management-console-server',
			'univention-management-console-web-server',
			'univention-welcome-screen',  # TODO do the jenkins vms for the selenium test have a display manager installed?
			'heimdal-kdc',  # TODO services['heimdal-kdc']['programs'] has mismatching output from psutil.Process.cmdline()
		]
		for service in self.srvs.services.iterkeys():
			if service in ignore_these:
				continue
			self.test_stop_start_and_restart(service)

	def test_stop_start_and_restart(self, service):
		for cmd in ('stop', 'start', 'stop', 'restart', 'restart'):
			self.do_and_confirm_status_change(service, cmd)

	def do_and_confirm_status_change(self, service, cmd):
		action = {
			'stop': _('Stop'),
			'start': _('Start'),
			'restart': _('Restart')
		}[cmd]
		self.search_and_action(service, action)
		self.confirm_status(service, cmd)

	def confirm_status(self, service, cmd):
		err_txt_for_cmd = {
			'stop': 'stopped',
			'start': 'started',
			'restart': 'restarted',
		}[cmd]

		# check that status in the grid is correct
		grid_status = self.get_service_grid_status(service)
		wanted_status = {
			'stop': 'stopped',
			'start': 'running',
			'restart': 'running',
		}[cmd]
		if grid_status != wanted_status:
			time.sleep(5)
			self.search(service)
			grid_status = self.get_service_grid_status(service)
			if grid_status != wanted_status:
				raise UmcError('Service "%s" did not change status in grid after being %s' % (service, err_txt_for_cmd))

		# check that the status with psutil is correct
		proc = [proc for proc in psutil.process_iter() if self.srvs.services[service]['programs'] in proc.cmdline()]
		if cmd == 'stop' and proc:
			raise UmcError('Service "%s" was %s but is still visible in psutil' % (service, err_txt_for_cmd))
		elif cmd != 'stop' and not proc:
			raise UmcError('Service "%s" was %s but is not visible in psutil' % (service, err_txt_for_cmd))

	def get_service_grid_status(self, service):
		status_cell_xpath = expand_path('//td[@containsClass="field-service"]/descendant-or-self::*[text() = "%s"]/following::td[@containsClass="field-isRunning"]/descendant-or-self::*[text() = "stopped" or text() = "running"]' % service)
		return self.selenium.driver.find_element_by_xpath(status_cell_xpath).text


if __name__ == '__main__':
	with selenium.UMCSeleniumTest() as s:
		umc_tester = UMCTester()
		umc_tester.selenium = s

		umc_tester.test_umc()
