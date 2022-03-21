#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
setup via umc
"""

import os
import time
from argparse import ArgumentParser, Namespace  # noqa F401

from components.components import components_with_steps as components
from installation import UCSInstallation

from vncautomate import VNCConnection, init_logger
from vncautomate.config import OCRConfig
from vncdotool.api import VNCDoException


class UCSSetup(UCSInstallation):

	def __init__(self, args):  # type: (Namespace) -> None
		init_logger('info')
		self.args = args
		self.config = OCRConfig()
		self.config.update(lang='eng')
		self.timeout = 40
		self.connect()

	def click(self, text):  # type: (str) -> None
		self.client.waitForText(text, timeout=self.timeout)
		self.client.mouseClickOnText(text)

	def screenshot(self, filename):  # type: (str) -> None
		if not os.path.isdir(self.args.screenshot_dir):
			os.mkdir(self.args.screenshot_dir)
		screenshot_file = os.path.join(self.args.screenshot_dir, filename)
		self.client.captureScreen(screenshot_file)

	def __next__(self):  # type: () -> None
		self.client.waitForText('NEXT', timeout=self.timeout)
		self.client.mouseClickOnText('NEXT')

	next = __next__  # Python 2

	def tab_to_next_and_enter(self, tabs):
		for i in range(tabs):
			self.client.keyPress('tab')
			time.sleep(0.5)
		self.client.keyPress('enter')

	def enter(self):  # type: () -> None
		time.sleep(0.5)
		self.client.keyPress('enter')

	def language(self, language):  # type: (str) -> None
		if self.text_is_visible('Notification', timeout=self.timeout):
			self.screenshot('notification.png')
			self.client.mouseClickOnText('OK')
		try:
			self.client.waitForText('English', timeout=self.timeout, prevent_screen_saver=True)
		except VNCDoException:
			self.connect()
		self.screenshot('language-setup.png')
		#self.next()
		self.tab_to_next_and_enter(2)
		self.client.waitForText('Default system locale', timeout=self.timeout)
		#self.next()
		self.tab_to_next_and_enter(4)

	def network(self):  # type: () -> None
		try:
			self.client.waitForText('IP address', timeout=self.timeout)
		except VNCDoException:
			self.connect()
			self.client.waitForText('Domain and network', timeout=self.timeout)
		self.screenshot('network-setup.png')
		self.click('Preferred DNS')
		if self.args.role in ['admember', 'slave']:
			self.client.enterText(self.args.dns)
		self.enter()
		time.sleep(60)
		# check APIPA warning (automatic private address for eth0 if no dhcp answer)
		try:
			self.client.waitForText('APIPA', timeout=self.timeout)
			self.client.keyPress('enter')
			time.sleep(60)
		except VNCDoException:
			self.connect()
		try:
			self.client.waitForText('No gateway has been', timeout=self.timeout)
			self.client.keyPress('enter')
			time.sleep(60)
		except VNCDoException:
			self.connect()
		try:
			self.client.waitForText('continue without access', timeout=self.timeout)
			self.client.keyPress('enter')
			time.sleep(60)
		except VNCDoException:
			self.connect()
		time.sleep(120)

	def domain(self, role):  # type: (str) -> None
		text = 'Manage users and permissions'
		if self.args.ucs is True:
			text = 'Create a new UCS domain'
		if role == 'admember':
			text = 'Join into an existing Microsoft Active'
		elif role in ['join', 'slave']:
			text = 'Join into an existing UCS domain'
		elif role == 'fast':
			text = 'Fast demo'
		self.client.waitForText(text, timeout=self.timeout)
		self.client.mouseClickOnText(text, timeout=self.timeout)
		self.screenshot('domain-setup.png')
		#self.next()
		self.tab_to_next_and_enter(2)
		time.sleep(10)
		if role == 'slave':
			#self.client.keyPress('down')
			#self.next()
			self.client.waitForText('Replica Directory Node', timeout=self.timeout)
			self.client.mouseClickOnText('Replica Directory Node', timeout=self.timeout)
			self.tab_to_next_and_enter(2)
			self.click('Username')
			self.client.enterText(self.args.join_user)
			self.click('Password')
			self.client.enterText(self.args.join_password)
			#self.next()
			self.tab_to_next_and_enter(2)
		if role == 'admember':
			self.client.waitForText('Active Directory join', timeout=self.timeout)
			self.click('Username')
			self.client.enterText(self.args.join_user)
			self.click('Password')
			self.client.enterText(self.args.join_password)
			#self.next()
			self.tab_to_next_and_enter(2)

	def orga(self, orga, password):  # type: (str, str) -> None
		self.client.waitForText('Account information', timeout=self.timeout)
		self.screenshot('organisation-setup.png')
		self.client.enterText('home')
		self.client.keyPress('tab')
		self.client.keyPress('tab')
		self.client.keyPress('tab')
		self.client.enterText(password)
		self.client.keyPress('tab')
		self.client.enterText(password)
		#self.next()
		self.tab_to_next_and_enter(2)

	def hostname(self):  # type: () -> None
		self.client.waitForText('Host settings', timeout=self.timeout)
		self.screenshot('hostname-setup.png')
		# delete the pre-filled hostname
		self.client.keyPress('end')
		for i in range(1, 200):
			self.client.keyPress('bsp')
		time.sleep(3)
		self.client.enterText(self.args.fqdn)
		self.client.keyPress('tab')
		if self.args.role in ['admember', 'slave']:
			self.client.enterText(self.args.password)
			self.client.keyPress('tab')
			self.client.enterText(self.args.password)
		#self.next()
		self.tab_to_next_and_enter(2)

	def start(self):  # type: () -> None
		self.client.waitForText('confirm configuration', timeout=self.timeout)
		self.screenshot('start-setup.png')
		found = False
		for i in range(3):
			self.client.keyPress('down')
		try:
			self.client.mouseClickOnText('configuresystem')
			found = True
		except VNCDoException:
			self.connect()
		if not found:
			self.client.mouseClickOnText('configure system')

	def finish(self):  # type: () -> None
		time.sleep(600)
		self.client.waitForText('UCS setup successful', timeout=3000, prevent_screen_saver=True)
		self.screenshot('finished-setup.png')
		self.client.keyPress('tab')
		self.client.keyPress('enter')
		# except welcome screen
		found = False
		try:
			self.client.waitForText('www', timeout=self.timeout)
			found = True
		except VNCDoException:
			self.connect()
		if not found:
			self.client.waitForText('press any key', timeout=self.timeout)
		self.screenshot('welcome-screen.png')

	def connect(self):  # type: () -> None
		self.conn = VNCConnection(self.args.vnc)
		self.client = self.conn.__enter__()
		self.client.updateOCRConfig(self.config)

	def setup(self):  # type: () -> None
		try:
			self.language('English')
			self.network()
			self.domain(self.args.role)
			if self.args.role == 'master':
				self.orga(self.args.organisation, self.args.password)
			if not self.args.role == 'fast':
				self.hostname()
			self.start()
			self.finish()
		except Exception:
			self.connect()
			self.screenshot('error.png')
			raise


def main():  # type: () -> None
	parser = ArgumentParser(description=__doc__)
	parser.add_argument('--screenshot-dir', default='./screenshots', help="Directory for storing screenshots")
	parser.add_argument('--ucs', help='UCS appliance', action='store_true')
	group = parser.add_argument_group("Virtual machine settings")
	group.add_argument('--vnc', required=True, help="VNC screen to connect to")
	group = parser.add_argument_group("Host settings")
	group.add_argument('--fqdn', default='master.ucs.local', help="Fully qualified host name to use")
	group.add_argument('--password', default='univention', help="Password to setup for user 'root' and/or 'Administrator'")
	group.add_argument('--organisation', default='ucs', help="Oranisation name to setup")
	group.add_argument('--role', default='master', choices=['master', 'admember', 'fast', 'slave'], help="UCS system role")
	group.add_argument('--components', default=[], choices=list(components) + ['all'], action='append', help="UCS components to install")
	group = parser.add_argument_group("Join settings")
	group.add_argument('--dns', help="DNS server of UCS domain")
	group.add_argument('--join-user', help="User name for UCS domain join")
	group.add_argument('--join-password', help="Password for UCS domain join")
	args = parser.parse_args()

	if args.role in ['admember', 'slave']:
		assert args.dns is not None
		assert args.join_user is not None
		assert args.join_password is not None

	setup = UCSSetup(args=args)
	setup.setup()


if __name__ == '__main__':
	main()
