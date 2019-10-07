#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
UCS installation via vnc
"""

from vncautomate import init_logger, VNCConnection
from vncautomate.config import OCRConfig
from vncdotool.api import VNCDoException

from components.components import components_with_steps as components
from languages import english
from languages import french
from languages import german

import time
import sys
import os


class UCSInstallation(object):

	def __init__(self, args):
		init_logger('info')
		self.args = args
		self.config = OCRConfig()
		self.config.update(lang=self.args.language)
		self.timeout = 60
		self.connect()

	def screenshot(self, filename):
		if not os.path.isdir(self.args.screenshot_dir):
			os.mkdir(self.args.screenshot_dir)
		screenshot_file = os.path.join(self.args.screenshot_dir, filename)
		self.client.captureScreen(screenshot_file)

	def click(self, text):
		self.client.waitForText(text, timeout=self.timeout)
		self.client.mouseClickOnText(text)

	def connect(self):
		self.conn = VNCConnection(self.args.vnc)
		self.client = self.conn.__enter__()
		self.client.updateOCRConfig(self.config)

	def text_is_visible(self, text, timeout=30):
		try:
			self.client.waitForText(text, timeout=timeout)
			return True
		except VNCDoException:
			self.connect()
			return False

	def installer(self):
		# language
		self.client.waitForText('Select a language', timeout=self.timeout + 120, prevent_screen_saver=True)
		self.client.enterText(self._['english_language_name'])
		self.click('Continue')
		self.client.waitForText(self._['select_location'], timeout=self.timeout)
		self.client.enterText(self._['location'])
		self.client.keyPress('enter')
		self.client.waitForText(self._['select_keyboard'], timeout=self.timeout)
		self.client.enterText(self._['us_keyboard_layout'])
		self.client.keyPress('enter')

		if not self.network_setup():
			self.client.mouseMove(100, 320)
			self.client.mousePress(1)
			time.sleep(1)

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
			self.client.keyPress('enter')
		# hd
		time.sleep(60)
		self.client.waitForText(self._['partition_disks'], timeout=self.timeout)
		if self.args.role == 'applianceLVM':
			self.click(self._['entire_disk_with_lvm'])
			self.client.keyPress('enter')
			time.sleep(3)
			self.client.keyPress('enter')
			self.click(self._['all_files_on_partition'])
			self.client.keyPress('enter')
			time.sleep(3)
			self.client.keyPress('down')
			self.client.keyPress('enter')
			self.click(self._['finish_partition'])
			self.client.keyPress('enter')
			self.client.waitForText(self._['continue_partition'], timeout=self.timeout)
			self.client.keyPress('down')
			self.client.keyPress('enter')
		elif self.args.role == 'applianceEC2':
			# Manuel
			self.click(self._['manual'])
			self.client.keyPress('enter')
			time.sleep(3)
			# Virtuelle Festplatte 1
			self.click(self._['virtual_disk_1'])
			time.sleep(3)
			self.client.keyPress('enter')
			time.sleep(3)
			self.client.keyPress('down')
			time.sleep(3)
			self.client.keyPress('enter')
			time.sleep(3)
			self.click(self._['free_space'])
			self.client.keyPress('enter')
			time.sleep(3)
			# neue partition erstellen
			self.client.keyPress('enter')
			time.sleep(3)
			# enter: ganze festplattengröße ist eingetragen
			self.client.keyPress('enter')
			time.sleep(3)
			# enter: primär
			self.client.keyPress('enter')
			time.sleep(3)
			self.click(self._['boot_flag'])
			# enter: boot-flag aktivieren
			self.client.keyPress('enter')
			time.sleep(3)
			self.click(self._['finish_create_partition'])
			self.client.keyPress('enter')
			time.sleep(3)
			self.click(self._['finish_partition'])
			self.client.keyPress('enter')
			time.sleep(3)
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
			time.sleep(3)
			self.client.keyPress('enter')
			self.click(self._['all_files_on_partition'])
			self.client.keyPress('enter')
			self.click(self._['finish_partition'])
			self.client.keyPress('enter')
			self.client.waitForText(self._['continue_partition'], timeout=self.timeout)
			self.client.keyPress('down')
			self.client.keyPress('enter')

	def network_setup(self):
		time.sleep(60)
		# we may not see this because the only interface is configured via dhcp
		if not self.text_is_visible(self._['configure_network'], timeout=120):
			return False
		self.client.waitForText(self._['configure_network'], timeout=self.timeout)
		# always use first interface
		self.click(self._['continue'])
		time.sleep(60)
		if self.args.ip:
			self.client.waitForText(self._['not_using_dhcp'], timeout=self.timeout)
			self.client.keyPress('enter')

			self.client.waitForText(self._['manual_network_config'], timeout=self.timeout)
			self.client.mouseClickOnText(self._['manual_network_config'])
			self.client.keyPress('enter')
			self.client.waitForText(self._['ip_address'], timeout=self.timeout)
			self.client.enterText(self.args.ip)
			self.client.keyPress('enter')

			self.client.waitForText(self._['netmask'], timeout=self.timeout)
			self.client.keyPress('enter')

			self.client.waitForText(self._['gateway'], timeout=self.timeout)
			self.client.keyPress('enter')

			self.client.waitForText(self._['name_server'], timeout=self.timeout)
			if self.args.dns:
				self.client.enterText(self.args.dns)
			self.client.keyPress('enter')
		return True

	def configure_kvm_network(self):
		if 'all' in self.args.components or 'kde' in self.args.components:
			time.sleep(10)
			self.client.keyDown('alt')
			self.client.keyDown('ctrl')
			self.client.keyPress('f1')
			self.client.keyUp('alt')
			self.client.keyUp('ctrl')
		elif self.args.role == 'basesystem':
			time.sleep(3)
		else:
			self.client.waitForText('corporate server')
			self.client.keyPress('enter')
		time.sleep(3)
		self.client.enterText('root')
		self.client.keyPress('enter')
		time.sleep(5)
		self.client.enterText(self.args.password)
		self.client.keyPress('enter')
		self.client.enterText('ucr set interfaces-ens6-tzpe`manual')
		self.client.keyPress('enter')
		time.sleep(30)
		self.client.enterText('ifconfig ens6 up')
		self.client.keyPress('enter')
		self.client.enterText('echo ')
		self.client.keyDown('shift')
		self.client.enterText('2')  # @
		self.client.keyUp('shift')
		self.client.enterText('reboot -sbin-ifconfig ens6 up ')
		self.client.keyDown('shift')
		self.client.enterText("'")  # |
		self.client.keyUp('shift')
		self.client.enterText(' crontab')
		self.client.keyPress('enter')

	def setup(self):
		self.client.waitForText(self._['domain_setup'], timeout=self.timeout + 900)
		if self.args.role == 'master':
			self.click(self._['new_domain'])
			self.click(self._['next'])
			self.client.waitForText(self._['account_information'], timeout=self.timeout)
			self.client.enterText('home')
			self.click(self._['next'])
		elif self.args.role in ['slave', 'backup', 'member']:
			self.click(self._['join_domain'])
			self.click(self._['next'])
			self.client.waitForText(self._['no_dc_dns'])
			#self.click(self._['no_dc_dns_adapt'])
			self.client.keyPress('tab')
			self.client.keyPress('enter')
			self.click(self._['preferred_dns'])
			self.client.enterText(self.args.dns)
			self.client.keyPress('enter')
			time.sleep(120)
			if self.text_is_visible(self._['repositories_not_reachable']):
				self.client.keyPress('enter')
				time.sleep(30)
			self.click(self._['join_domain'])
			self.click(self._['next'])
			time.sleep(10)
			if self.args.role == 'backup':
				self.click(self._['next'])
			if self.args.role == 'slave':
				self.client.keyPress('down')
				self.click(self._['next'])
			if self.args.role == 'member':
				self.client.keyPress('down')
				self.client.keyPress('down')
				self.click(self._['next'])
			self.client.waitForText(self._['start_join'], timeout=self.timeout)
			self.client.keyPress('tab')
			self.client.keyPress('tab')
			self.client.enterText(self.args.join_user)
			self.client.keyPress('tab')
			self.client.enterText(self.args.join_password)
			self.client.keyPress('enter')
		elif self.args.role == 'admember':
			self.click(self._['ad_domain'])
			self.click(self._['next'])
			self.client.waitForText(self._['no_dc_dns'], timeout=self.timeout)
			self.client.keyPress('enter')
			self.click(self._['preferred_dns'])
			self.client.enterText(self.args.dns)
			self.client.keyPress('enter')
			time.sleep(120)
			if self.text_is_visible(self._['repositories_not_reachable']):
				self.client.keyPress('enter')
				time.sleep(30)
			if self.text_is_visible('APIPA', timeout=self.timeout):
				self.client.keyPress('enter')
				time.sleep(60)
			self.click(self._['next'])
			self.client.waitForText(self._['ad_account_information'], timeout=self.timeout)
			self.client.keyPress('tab')
			self.client.enterText(self.args.join_user)
			self.client.keyPress('tab')
			self.client.enterText(self.args.join_password)
			self.click(self._['next'])
		elif self.args.role == 'basesystem':
			self.click(self._['no_domain'])
			self.click(self._['next'])
			self.client.waitForText(self._['warning_no_domain'], timeout=self.timeout)
			self.click(self._['next'])
		elif self.args.role == 'applianceEC2' or self.args.role == 'applianceLVM':
			self.client.keyDown('ctrl')
			self.client.keyPress('q')
			self.client.keyUp('ctrl')
			time.sleep(300)
			self.client.waitForText(self._['appliance_modus'], timeout=self.timeout)
			self.click(self._['continue'])
			time.sleep(60)
			sys.exit(0)
		else:
			raise NotImplemented

	def hostname(self):
		# name hostname
		if self.args.role == 'master':
			self.client.waitForText(self._['host_settings'], timeout=self.timeout)
		else:
			self.client.waitForText(self._['system_name'])
		self.client.keyPress('end')
		for i in range(1, 200):
			self.client.keyPress('bsp')
		self.client.enterText(self.args.fqdn)
		self.client.keyPress('tab')
		self.click(self._['next'])

	def finish(self):
		self.client.waitForText(self._['setup_successful'], timeout=3200)
		#self.click(self._['finish'])
		self.client.keyPress('tab')
		self.client.keyPress('enter')
		time.sleep(200)

	def software_configuration(self):
		# software configuration
		if self.args.role != 'basesystem':
			if self.args.role == 'master':
				self.client.waitForText(self._['software_configuration'], timeout=self.timeout)
			else:
				self.client.waitForText(self._['software_configuration_non_master'], timeout=self.timeout)
			self.select_components()
			self.click(self._['next'])
		time.sleep(5)
		self.client.keyPress('enter')

	def select_components(self):
		# this is needed to make the down button work
		if 'all' in self.args.components:
			self.client.mouseMove(325, 200)
			self.client.mousePress(1)
		else:
			print('move mouse')
			self.client.mouseMove(325, 300)
			self.client.mousePress(1)
			time.sleep(1)
			self.client.mousePress(1)
			for name, steps in components.iteritems():
				if name in self.args.components:
					# go to the top
					print('go up')
					for step in range(1, 20):
						self.client.keyPress('up')
						time.sleep(0.2)
					for step in range(1, steps):
						print('go down')
						self.client.keyPress('down')
						time.sleep(0.2)
					self.click(self._[name])

	def ucsschool(self):
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
				raise NotImplemented()
			self.click(self._['next'])

	def bootmenu(self):
		if self.text_is_visible('Univention Corporate Server Installer', timeout=120):
			self.client.keyPress('enter')

	def installation(self):
		if self.args.language == 'eng':
			self._ = english.strings
		elif self.args.language == 'fra':
			self._ = french.strings
		else:
			self._ = german.strings

		try:
			self.bootmenu()
			self.installer()
			self.setup()
			self.hostname()
			self.ucsschool()
			self.software_configuration()
			self.finish()
			# TODO activate ens6 so that ucs-kvm-create can connect to instance
			# this is done via login and setting interfaces/eth0/type, is there a better way?
			self.configure_kvm_network()
		except Exception:
			self.connect()
			self.screenshot('error.png')
			raise
