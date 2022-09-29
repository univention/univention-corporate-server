#!/usr/bin/python2.7 -u
# -*- coding: utf-8 -*-

"""
UCS installation via VNC
"""

from vncautomate import init_logger, VNCConnection
from vncautomate.config import OCRConfig
from vncdotool.api import VNCDoException

from languages import english
from languages import french
from languages import german

import time
import sys
import os
import logging
from argparse import Namespace  # noqa: F401
from functools import wraps

KVM_INTERFACE = 'ens8'


def verbose(msg, fmt="", skip=1):  # type (str, str, int) -> Callabble[[T], T]
	def decorator(f):  # type (Callable) -> Callable
		@wraps(f)
		def wrapper(*args, **kwargs):  # type (*Any, **Any) -> Any
			print(("%s:BEGIN " + fmt) % ((msg,) + args[skip:][:fmt.count("%")]))
			sys.stdout.flush()
			try:
				return f(*args, **kwargs)
			finally:
				print("%s:END" % msg)
				sys.stdout.flush()
		return wrapper
	return decorator


@verbose("sleep", "%.1f", skip=0)
def sleep(seconds):  # type: (float) -> None
	time.sleep(seconds)


class UCSInstallation(object):

	def __init__(self, args):  # type: (Namespace) -> None
		# see https://github.com/tesseract-ocr/tesseract/issues/2611
		os.environ['OMP_THREAD_LIMIT'] = '1'
		init_logger('info')
		self.args = args
		self.config = OCRConfig()
		self.config.update(lang=self.args.language)
		self.timeout = 120
		self.setup_finish_sleep = 900
		self.connect()

	def _clear_input(self):  # type: () -> None
		self.client.keyPress('end')
		time.sleep(0.1)
		for i in range(100):
			self.client.keyPress('bsp')
			time.sleep(0.1)

	def screenshot(self, filename):  # type: (str) -> None
		if not os.path.isdir(self.args.screenshot_dir):
			os.mkdir(self.args.screenshot_dir)
		screenshot_file = os.path.join(self.args.screenshot_dir, filename)
		self.client.captureScreen(screenshot_file)

	@verbose("click", "%r")
	def click(self, text):  # type: (str) -> None
		self.client.waitForText(text, timeout=self.timeout)
		self.client.mouseClickOnText(text)

	def connect(self):  # type: () -> None
		self.conn = VNCConnection(self.args.vnc)
		self.client = self.conn.__enter__()
		self.client.updateOCRConfig(self.config)

	def text_is_visible(self, text, timeout=120):  # type: (str, int) -> bool
		try:
			self.client.waitForText(text, timeout=timeout)
			return True
		except VNCDoException:
			self.connect()
			return False

	@verbose("NEXT")
	def move_to_next_and_click(self):  # type: () -> None
		sleep(1)
		self.client.mouseMove(910, 700)
		sleep(1)
		logging.info('clicking next')
		self.client.mousePress(1)

	@verbose("INSTALLER")
	def installer(self):  # type: () -> None
		# language
		for i in range(3):
			self.client.waitForText('Select a language', timeout=self.timeout + 120, prevent_screen_saver=True)
			self.client.enterText(self._['english_language_name'])
			self.click('Continue')
			try:
				self.client.waitForText(self._['select_location'], timeout=self.timeout)
				break
			except VNCDoException:
				self.connect()
				self.click('Go Back')
		self.client.enterText(self._['location'])
		self.client.keyPress('enter')
		self.client.waitForText(self._['select_keyboard'], timeout=self.timeout)
		self.client.enterText(self._['us_keyboard_layout'])
		self.client.keyPress('enter')

		if not self.network_setup():
			self.client.mouseMove(100, 320)
			self.client.mousePress(1)
			sleep(1)

		# root
		self.client.waitForText(self._['user_and_password'], timeout=self.timeout)
		self.client.enterText(self.args.password)
		self.client.keyPress('tab')
		self.client.keyPress('tab')
		self.client.enterText(self.args.password)
		self.client.keyPress('enter')
		if self.args.language == 'eng':
			self.client.waitForText(self._['configure_clock'], timeout=self.timeout)
			#self.client.enterText(self._['clock'])
			sleep(1)
			self.client.keyPress('enter')
		# hd
		sleep(60)
		self.client.waitForText(self._['partition_disks'], timeout=self.timeout)
		if self.args.role == 'applianceLVM':
			#self.click(self._['entire_disk_with_lvm'])
			# LVM is the default so just press enter
			self.client.keyPress('enter')
			sleep(3)
			self.client.keyPress('enter')
			self.click(self._['all_files_on_partition'])
			self.client.keyPress('enter')
			sleep(3)
			self.client.keyPress('down')
			self.client.keyPress('enter')
			self.client.waitForText(self._['continue_partition'], timeout=self.timeout)
			self.client.keyPress('down')
			self.client.keyPress('enter')
		elif self.args.role == 'applianceEC2':
			# Manuel
			self.click(self._['manual'])
			self.client.keyPress('enter')
			sleep(3)
			# Virtuelle Festplatte 1
			self.click(self._['virtual_disk_1'])
			sleep(3)
			self.client.keyPress('enter')
			sleep(3)
			self.client.keyPress('down')
			sleep(3)
			self.client.keyPress('enter')
			sleep(3)
			self.click(self._['free_space'])
			self.client.keyPress('enter')
			sleep(3)
			# neue partition erstellen
			self.client.keyPress('enter')
			sleep(3)
			# enter: ganze festplattengröße ist eingetragen
			self.client.keyPress('enter')
			sleep(3)
			# enter: primär
			self.client.keyPress('enter')
			sleep(3)
			self.click(self._['boot_flag'])
			# enter: boot-flag aktivieren
			self.client.keyPress('enter')
			sleep(3)
			self.click(self._['finish_create_partition'])
			self.client.keyPress('enter')
			sleep(3)
			self.click(self._['finish_partition'])
			self.client.keyPress('enter')
			sleep(3)
			# Nein (kein swap speicher)
			self.click(self._['no'])
			self.client.keyPress('enter')
			self.client.waitForText(self._['continue_partition'], timeout=self.timeout)
			self.client.keyPress('down')
			self.client.keyPress('enter')
			self.client.keyPress('enter')
		else:
			self.click(self._['entire_disk'])
			self.client.keyPress('enter')
			sleep(3)
			self.client.keyPress('enter')
			sleep(3)
			self.client.keyPress('enter')
			self.click(self._['finish_partition'])
			self.client.keyPress('enter')
			self.client.waitForText(self._['continue_partition'], timeout=self.timeout)
			self.client.keyPress('down')
			self.client.keyPress('enter')
		sleep(600)
		self.client.waitForText(self._['finish_installation'], timeout=1300)
		self.client.keyPress('enter')
		sleep(30)

	@verbose("NETWORK")
	def network_setup(self):  # type: () -> bool
		sleep(60)
		# we may not see this because the only interface is configured via dhcp
		if not self.text_is_visible(self._['configure_network'], timeout=120):
			return False
		self.client.waitForText(self._['configure_network'], timeout=self.timeout)
		if not self.text_is_visible(self._['ip_address'], timeout=self.timeout):
			# always use first interface
			self.click(self._['continue'])
			sleep(60)
		if self.args.ip:
			if self.text_is_visible(self._['not_using_dhcp'], timeout=self.timeout):
				self.client.waitForText(self._['not_using_dhcp'], timeout=self.timeout)
				self.client.keyPress('enter')
				self.client.waitForText(self._['manual_network_config'], timeout=self.timeout)
				self.client.mouseClickOnText(self._['manual_network_config'])
				self.client.keyPress('enter')
			self.client.waitForText(self._['ip_address'], timeout=self.timeout)
			self.client.enterText(self.args.ip)
			self.client.keyPress('enter')
			self.client.waitForText(self._['netmask'], timeout=self.timeout)
			if self.args.netmask:
				self.client.enterText(self.args.netmask)
			self.client.keyPress('enter')
			self.client.waitForText(self._['gateway'], timeout=self.timeout)
			if self.args.gateway:
				self.client.enterText(self.args.gateway)
			self.client.keyPress('enter')
			self.client.waitForText(self._['name_server'], timeout=self.timeout)
			if self.args.dns:
				self.client.enterText(self.args.dns)
			self.client.keyPress('enter')
		return True

	def configure_kvm_network(self):  # type: () -> None
		if 'all' in self.args.components or 'kde' in self.args.components:
			sleep(10)
			self.client.keyDown('alt')
			self.client.keyDown('ctrl')
			self.client.keyPress('f1')
			self.client.keyUp('alt')
			self.client.keyUp('ctrl')
		elif self.args.role == 'basesystem':
			sleep(3)
		else:
			self.client.waitForText('corporate server')
			self.client.keyPress('enter')
		sleep(3)
		self.client.enterText('root')
		self.client.keyPress('enter')
		sleep(5)
		self.client.enterText(self.args.password)
		self.client.keyPress('enter')
		self.client.enterText('ucr set interfaces-%s-tzpe`manual' % KVM_INTERFACE)
		self.client.keyPress('enter')
		sleep(30)
		self.client.enterText('ip link set %s up' % KVM_INTERFACE)
		self.client.keyPress('enter')
		self.client.enterText('echo ')
		self.client.keyDown('shift')
		self.client.enterText('2')  # @
		self.client.keyUp('shift')
		self.client.enterText('reboot -sbin-ip link set %s up ' % KVM_INTERFACE)
		self.client.keyDown('shift')
		self.client.enterText("'")  # |
		self.client.keyUp('shift')
		self.client.enterText(' crontab')
		self.client.keyPress('enter')

	@verbose("LIGHTTHEME")
	def lighttheme(self):  # type: () -> None
		# since a firefox update dark theme strings are not recognized any more
		sleep(20)
		sleep(1)
		self.client.keyDown('ctrl')
		sleep(1)
		self.client.keyPress('q')
		sleep(2)
		self.client.keyUp('ctrl')
		sleep(3)
		self.client.keyPress('enter')
		sleep(3)
		self.client.enterText('root')
		self.client.keyPress('enter')
		sleep(1)
		self.client.enterText('univention')
		self.client.keyPress('enter')
		sleep(3)
		self.client.enterText('ucr set ucs-web-theme´light')
		self.client.keyPress('enter')
		sleep(1)
		self.client.enterText('ucr set szstem-setup-boot-pages-blacklist`welcome')
		self.client.keyPress('enter')
		sleep(1)
		self.client.enterText('ucr set szstem-setup-boot-pages-blacklist')
		self.client.keyPress('tab')
		sleep(1)
		self.client.keyPress('left')
		self.client.keyPress('left')
		self.client.enterText(' locale network')
		self.client.keyPress('enter')
		sleep(1)
		self.client.enterText('service univention\\szstem\\setup\\boot restart')
		self.client.keyPress('enter')
		sleep(10)

	@verbose("SETUP")
	def setup(self):  # type: () -> None
		self.client.waitForText(self._['domain_setup'], timeout=self.timeout + 900)
		if self.args.role == 'master':
			self.click(self._['new_domain'])
			self.move_to_next_and_click()
			self.client.waitForText(self._['account_information'], timeout=self.timeout)
			self.client.enterText('home')
			self.client.keyPress('tab')
			self.client.keyPress('tab')
			self.client.keyPress('tab')
			self.client.enterText(self.args.password)
			sleep(1)
			self.client.keyPress('tab')
			self.client.enterText(self.args.password)
			self.move_to_next_and_click()
		elif self.args.role in ['slave', 'backup', 'member']:
			self.click(self._['join_domain'])
			self.move_to_next_and_click()
			if self.text_is_visible(self._['no_dc_dns']):
				self.click(self._['change_settings'])
				self.click(self._['preferred_dns'])
				self.client.enterText(self.args.dns)
				self.client.keyPress('enter')
				sleep(120)
				if self.text_is_visible(self._['repositories_not_reachable']):
					self.client.keyPress('enter')
					sleep(30)
				self.click(self._['join_domain'])
				self.move_to_next_and_click()
			self.client.waitForText(self._['role'])
			if self.args.role == 'backup':
				self.click('Backup Directory Node')
				self.move_to_next_and_click()
			if self.args.role == 'slave':
				self.click('Replica Directory Node')
				self.move_to_next_and_click()
			if self.args.role == 'member':
				self.click('Managed Node')
				self.move_to_next_and_click()
		elif self.args.role == 'admember':
			self.click(self._['ad_domain'])
			self.move_to_next_and_click()
			self.client.waitForText(self._['no_dc_dns'], timeout=self.timeout)
			self.client.keyPress('enter')
			self.click(self._['preferred_dns'])
			sleep(1)
			self.client.enterText(self.args.dns)
			self.client.keyPress('enter')
			sleep(120)
			if self.text_is_visible(self._['repositories_not_reachable']):
				self.client.keyPress('enter')
				sleep(30)
			if self.text_is_visible('APIPA', timeout=self.timeout):
				self.client.keyPress('enter')
				sleep(60)
			self.move_to_next_and_click()
			self.move_to_next_and_click()
		elif self.args.role == 'basesystem':
			self.click(self._['no_domain'])
			self.click(self._['next'])
			self.client.waitForText(self._['warning_no_domain'], timeout=self.timeout)
			self.click(self._['next'])
		elif self.args.role == 'applianceEC2' or self.args.role == 'applianceLVM':
			self.client.keyDown('ctrl')
			self.client.keyPress('q')
			self.client.keyUp('ctrl')
			sleep(60)
			sys.exit(0)
		else:
			raise NotImplementedError

	@verbose("JOIN")
	def joinpass(self):  # type: () -> None
		if self.args.role not in ['slave', 'backup', 'member']:
			return
		self.client.waitForText(self._['start_join'], timeout=self.timeout)
		for i in range(2):
			self.click(self._['hostname_primary'])
			sleep(5)
			self.client.keyPress('tab')
			self._clear_input()
			self.client.enterText(self.args.join_user)
			self.client.keyPress('tab')
			self._clear_input()
			self.client.enterText(self.args.join_password)
			self.move_to_next_and_click()
			try:
				self.client.waitForText(self._['error'], timeout=self.timeout)
				self.client.keyPress('enter')
				self.client.keyPress('caplk')
			except VNCDoException:
				self.connect()
				break

	def joinpass_ad(self):  # type: () -> None
		if self.args.role not in ['admember']:
			return
		# join/ad password and user
		self.client.waitForText(self._['ad_account_information'], timeout=self.timeout)
		for i in range(2):
			self.click(self._['address_ad'])
			self.client.keyPress('tab')
			self._clear_input()
			self.client.enterText(self.args.join_user)
			self.client.keyPress('tab')
			self._clear_input()
			self.client.enterText(self.args.join_password)
			self.move_to_next_and_click()
			try:
				self.client.waitForText(self._['error'], timeout=self.timeout)
				self.client.keyPress('enter')
				self.client.keyPress('caplk')
			except VNCDoException:
				self.connect()
				break

	def hostname(self):  # type: () -> None
		# name hostname
		if self.args.role == 'master':
			self.client.waitForText(self._['host_settings'], timeout=self.timeout)
		else:
			self.client.waitForText(self._['system_name'])
		self._clear_input()
		self.client.enterText(self.args.fqdn)
		if self.args.role == 'master':
			self.client.keyPress('tab')
		self.move_to_next_and_click()

	@verbose("FINISH")
	def finish(self):  # type: () -> None
		self.client.waitForText(self._['confirm_config'], timeout=self.timeout)
		self.client.keyPress('enter')
		sleep(self.setup_finish_sleep)
		self.client.waitForText(self._['setup_successful'], timeout=2100)
		self.client.keyPress('tab')
		self.client.keyPress('enter')
		sleep(10)
		self.client.waitForText('univention', timeout=self.timeout)

	def ucsschool(self):  # type: () -> None
		# ucs@school role
		if self.args.school_dep:
			self.client.waitForText(self._['school_role'], timeout=self.timeout)
			if self.args.school_dep == 'adm':
				self.click(self._['school_adm'])
			elif self.args.school_dep == 'edu':
				self.click(self._['school_edu'])
			elif self.args.school_dep == 'central':
				self.click(self._['school_central'])
			else:
				raise NotImplementedError()
			self.move_to_next_and_click()

	def bootmenu(self):  # type: () -> None
		if self.text_is_visible('Univention Corporate Server Installer', timeout=120):
			if self.args.ip:
				self.client.keyPress('down')
			self.client.keyPress('enter')

	def installation(self):  # type: () -> None
		if self.args.language == 'eng':
			self._ = english.strings
		elif self.args.language == 'fra':
			self._ = french.strings
		else:
			self._ = german.strings

		try:
			self.bootmenu()
			self.installer()
			self.lighttheme()
			self.setup()
			self.joinpass_ad()
			self.joinpass()
			self.hostname()
			self.ucsschool()
			self.finish()
			if not self.args.no_second_interface:
				# TODO activate `KVM_INTERFACE` so that ucs-kvm-create can connect to instance
				# this is done via login and setting interfaces/eth0/type, is there a better way?
				self.configure_kvm_network()
		except Exception:
			self.connect()
			self.screenshot('error.png')
			raise
