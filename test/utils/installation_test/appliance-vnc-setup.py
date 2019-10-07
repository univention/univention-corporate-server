#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
setup via umc
"""

from argparse import ArgumentParser
from vncautomate import init_logger, VNCConnection
from vncautomate.config import OCRConfig
from vncdotool.api import VNCDoException

from installation import UCSInstallation
from components.components import components_with_steps as components

import time
import sys
import os


class UCSSetup(UCSInstallation):

	def __init__(self, args):
		init_logger('info')
		self.args = args
		self.config = OCRConfig()
		self.config.update(lang='eng')
		self.timeout = 40
		self.connect()

	def click(self, text):
		self.client.waitForText(text, timeout=self.timeout)
		self.client.mouseClickOnText(text)

	def screenshot(self, filename):
		if not os.path.isdir(self.args.screenshot_dir):
			os.mkdir(self.args.screenshot_dir)
		screenshot_file = os.path.join(self.args.screenshot_dir, filename)
		self.client.captureScreen(screenshot_file)

	def next(self):
		self.client.waitForText('NEXT', timeout=self.timeout)
		self.client.mouseClickOnText('NEXT')

	def language(self, language):
		if self.text_is_visible('Notification', timeout=self.timeout):
			self.screenshot('notification.png')
			self.mouseClickOnText('OK')
		self.client.waitForText('English', timeout=self.timeout, prevent_screen_saver=True)
		self.screenshot('language-setup.png')
		self.next()
		self.client.waitForText('Default system locale', timeout=self.timeout)
		self.next()

	def network(self):
		try:
			self.client.waitForText('IP address', timeout=self.timeout)
		except VNCDoException:
			self.connect()
			self.client.waitForText('Domain and network', timeout=self.timeout)
		self.screenshot('network-setup.png')
		if self.args.role in ['admember', 'slave']:
			self.click('Preferred DNS')
			self.client.enterText(self.args.dns)
		self.next()
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

	def domain(self, role):
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
		self.next()
		time.sleep(10)
		if role == 'slave':
			self.client.keyPress('down')
			self.next()
			self.click('Username')
			self.client.enterText(self.args.join_user)
			self.click('Password')
			self.client.enterText(self.args.join_password)
			self.next()
		if role == 'admember':
			self.client.waitForText('Active Directory join', timeout=self.timeout)
			self.click('Username')
			self.client.enterText(self.args.join_user)
			self.click('Password')
			self.client.enterText(self.args.join_password)
			self.next()

	def orga(self, orga, password):
		self.client.waitForText('Account information', timeout=self.timeout)
		self.screenshot('organisation-setup.png')
		self.client.enterText('home')
		self.client.keyPress('tab')
		self.client.keyPress('tab')
		self.client.keyPress('tab')
		self.client.enterText(password)
		self.client.keyPress('tab')
		self.client.enterText(password)
		self.next()

	def hostname(self, hostname):
		self.client.waitForText('Host settings', timeout=self.timeout)
		self.screenshot('hostname-setup.png')
		# delete the pre-filled hostname
		self.client.keyPress('end')
		for i in range(1, 200):
			self.client.keyPress('bsp')
		time.sleep(3)
		self.client.enterText(hostname)
		self.client.keyPress('tab')
		if self.args.role in ['admember', 'slave']:
			self.client.keyPress('tab')
			self.client.enterText(self.args.password)
			self.client.keyPress('tab')
			self.client.enterText(self.args.password)
		self.next()

	def start(self):
		self.client.waitForText('confirm configuration', timeout=self.timeout)
		self.screenshot('start-setup.png')
		found = False
		try:
			self.client.mouseClickOnText('configuresystem')
			found = True
		except VNCDoException:
			self.connect()
		if not found:
			self.client.mouseClickOnText('configure system')

	def finish(self):
		self.client.waitForText('Setup successful', timeout=3600, prevent_screen_saver=True)
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

	def connect(self):
		self.conn = VNCConnection(self.args.vnc)
		self.client = self.conn.__enter__()
		self.client.updateOCRConfig(self.config)

	def setup(self):
		try:
			self.language('English')
			self.network()
			self.domain(self.args.role)
			if self.args.role == 'master':
				self.orga(self.args.organisation, self.args.password)
			if not self.args.role == 'fast':
				self.hostname(self.args.fqdn)
			try:
				self.client.waitForText('Software configuration', timeout=self.timeout)
				self.next()
			except VNCDoException:
				self.connect()
			self.start()
			self.finish()
		except Exception:
			self.connect()
			self.screenshot('error.png')
			raise


def main():
	''' python %prog% --vnc 'utby:1' '''
	description = sys.modules[__name__].__doc__
	parser = ArgumentParser(description=description)
	parser.add_argument('--vnc')
	parser.add_argument('--fqdn', default='master.ucs.local')
	parser.add_argument('--dns')
	parser.add_argument('--join-user')
	parser.add_argument('--join-password')
	parser.add_argument('--password', default='univention')
	parser.add_argument('--organisation', default='ucs')
	parser.add_argument('--screenshot-dir', default='../screenshots')
	parser.add_argument('--role', default='master', choices=['master', 'admember', 'fast', 'slave'])
	parser.add_argument('--ucs', help='ucs appliance', action='store_true')
	parser.add_argument('--components', default=[], choices=components.keys() + ['all'], action='append')
	args = parser.parse_args()
	if args.role in ['admember', 'slave']:
		assert args.dns is not None
		assert args.join_user is not None
		assert args.join_password is not None
	assert args.vnc is not None
	setup = UCSSetup(args=args)
	setup.setup()


if __name__ == '__main__':
	main()
