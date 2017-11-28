#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
UCS installation via vnc
"""

from argparse import ArgumentParser
from vncautomate import init_logger, VNCConnection
from vncautomate.config import OCRConfig
from vncdotool.api import VNCDoException

import time
import sys
import os

installer_translations = dict(
	language=dict(
		deu='German',
		eng='English',
		fra='French',
	),
	select_location=dict(
		deu='Auswahlen des Standorts',
		eng='Select your location',
	),
	location=dict(
		deu='Deutschland',
		eng='United States',
		fra='France',
	),
	select_keyboard=dict(
		deu='Tastatur konfigurieren',
		eng='Configure the keyboard',
	),
	# always use amrican keyboard layout to make ocr happy
	keyboard=dict(
		deu='Amerikanisches Englisch',
		eng='American English',
	),
	configure_network=dict(
		deu='Netzwerk einrichten',
		eng='Configure the network'
	),
	user_and_password=dict(
		deu='Benutzer und Passworter',
		eng='Set up users and passwords',
	),
	configure_clock=dict(
		deu=None,
		eng='Configure the clock',
	),
	clock=dict(
		deu=None,
		eng='Eastern',
	),
	partition_disks=dict(
		deu='Festplatten partitionieren',
		eng='Partition disks',
	),
	entire_disk=dict(
		deu='Festplatte verwenden',
		eng='use entire disk',
	),
	all_files_on_partition=dict(
		deu='Alle Datein auf eine Partition',
		eng='All files in one partition',
	),
	finish_partition=dict(
		deu='Partitionierung beenden und',
		eng='Finish partitioning and',
	),
	continue_partition=dict(
		deu='Wenn Sie fortfahren',
		eng='If you continue',
	),
)

setup_translations = dict(
	next=dict(
		deu='Weiter',
		eng='Next',
	),
	domain=dict(
		deu='Domaneneinstellungen',
		eng='Domain Setup',
	),
	new_domain=dict(
		deu='Erstellen einer neuen',
		eng='Create a new UCS domain',
	),
	no_dc_dns=dict(
		deu='Unter der Adresse des DNS-Servers',
		eng='No domain controller was found at',
	),
	no_dc_dns_adapt=dict(
		deu='Einstellungen anpassen',
		eng='Adapt settings',
	),
	preferred_dns=dict(
		deu='Bevorzugter DNS-Server',
		eng='Preferred DNS server',
	),
	join_domain=dict(
		deu='Einer bestehenden UCS-Domane beitreten',
		eng='Join into an existing UCS domain',
	),
	slave=dict(
		deu='Domanencontroller Slave',
		eng='Domain controller slave',
	),
	backup=dict(
		deu='Domanencontroller Backup',
		eng='Domain controller backup',
	),
	member=dict(
		deu='Member-Server',
		eng='Member server',
	),
	start_join=dict(
		deu='Domanenbeitritt am Ende',
		eng='Start join at the end',
	),
	system_name=dict(
		deu='Eingabe des Namens',
		eng='Specify the name',
	),
	account_information=dict(
		deu='Kontoinformationen',
		eng='Account information',
	),
	host_settings=dict(
		deu='Rechnereinstellungen',
		eng='Host settings',
	),
	software_configuration=dict(
		deu='Software-Konfiguration',
		eng='Software configuration',
	),
	software_configuration_non_master=dict(
		deu='Wahlen Sie UCS-Software',
		eng='Select UCS software',
	),
	confirm=dict(
		deu='Bestatigen der Einstellungen',
		eng='Confirm configuration',
	),
	confirm_non_master=dict(
		deu='Bitte bestätigen Sie',
		eng='Please confirm the',
	),
	setup_successful=dict(
		deu='UCS-Einrichtung erfolgreich',
		eng='UCS setup successful',
	),
	finish=dict(
		deu='Fertigstellen',
		eng='FINISH',
	),
)

components = dict(
	samba4=dict(
		deu='Active Directory-kompatibler Dom',
		eng='Active Directory-compatible Domain',
		steps=0,
	),
	samba=dict(
		deu='Memberserver',
		eng='Memberserver',
		steps=14,
	),
	adconnector=dict(
		deu='Active Directory-Verbindung',
		eng='Active Directory Connection',
		steps=0,
	),
	kde=dict(
		deu='Desktop-Umgebung',
		eng='Desktop Environment',
		steps=0,
	),
	dhcpserver=dict(
		deu='DHCP-Server',
		eng='DHCP server',
		steps=0,
	),
	cups=dict(
		deu='Druckserver (CUPS)',
		eng='Print server (CUPS)',
		steps=2,
	),
	printquota=dict(
		deu='Druckserver Quota',
		eng='Print server Quota',
		steps=2,
	),
	kvm=dict(
		deu='KVM Virtualisierungsserver',
		eng='KVM virtualization server',
		steps=4,
	),
	mailserver=dict(
		deu='Mailserver',
		eng='Mail server',
		steps=6,
	),
	nagios=dict(
		deu='Netzwerkuberwachung',
		eng='Network monitoring',
		steps=8,
	),
	squid=dict(
		deu='Proxyserver',
		eng='Proxy server',
		steps=10,
	),
	radius=dict(
		deu='RADIUS',
		eng='RADIUS',
		steps=10,
	),
	pkgdb=dict(
		deu='Software-Installationsmonitor',
		eng='Software installation monitor',
		steps=12,
	),
	uvmm=dict(
		deu='Manager',
		eng='Manager',
		steps=14,
	),
)


class UCSInstallation(object):

	def __init__(self, args):
		init_logger('info')
		self.args = args
		self.config = OCRConfig()
		self.config.update(lang=self.args.language)
		self.timeout = 40
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

	def installer(self):
		_t = dict()
		for string in installer_translations:
			_t[string] = installer_translations[string][self.args.language]
		# language
		self.client.waitForText('Select a language', timeout=self.timeout)
		self.client.enterText(_t['language'])
		self.click('Continue')
		self.client.waitForText(_t['select_location'], timeout=self.timeout)
		self.client.enterText(_t['location'])
		self.client.keyPress('enter')
		self.client.waitForText(_t['select_keyboard'], timeout=self.timeout)
		self.client.enterText(_t['keyboard'])
		self.client.keyPress('enter')
		# network
		time.sleep(30)
		self.client.waitForText(_t['configure_network'], timeout=self.timeout)
		self.client.enterText('eth0')
		self.client.keyPress('enter')
		time.sleep(30)
		# root
		self.client.waitForText(_t['user_and_password'], timeout=self.timeout)
		self.client.enterText(self.args.password)
		self.client.keyPress('tab')
		self.client.enterText(self.args.password)
		self.client.keyPress('enter')
		if self.args.language == 'eng':
			self.client.waitForText(_t['configure_clock'], timeout=self.timeout)
			self.client.enterText(_t['clock'])
			self.client.keyPress('enter')
		# hd
		time.sleep(30)
		self.client.waitForText(_t['partition_disks'], timeout=self.timeout)
		self.click(_t['entire_disk'])
		self.client.keyPress('enter')
		time.sleep(3)
		self.client.keyPress('enter')
		self.click(_t['all_files_on_partition'])
		self.client.keyPress('enter')
		self.click(_t['finish_partition'])
		self.client.keyPress('enter')
		self.client.waitForText(_t['continue_partition'], timeout=self.timeout)
		self.client.keyPress('down')
		self.client.keyPress('enter')
		time.sleep(600)

	def configure_eth1(self):
		if 'all' in self.args.components or 'kde' in self.args.components:
			time.sleep(10)
			self.client.keyDown('alt')
			self.client.keyDown('ctrl')
			self.client.keyPress('f1')
			self.client.keyUp('alt')
			self.client.keyUp('ctrl')
		else:
			self.client.waitForText('corporate server')
			self.client.keyPress('enter')
		time.sleep(3)
		self.client.enterText('root')
		self.client.keyPress('enter')
		time.sleep(5)
		self.client.enterText(self.args.password)
		self.client.keyPress('enter')
		self.client.enterText('ifconfig eth1 up')
		self.client.keyPress('enter')
		self.client.enterText('echo ')
		self.client.keyDown('shift')
		self.client.enterText('2')  # @
		self.client.keyUp('shift')
		self.client.enterText('reboot -sbin-ifconfig eth1 up ')
		self.client.keyDown('shift')
		self.client.enterText("'")  # |
		self.client.keyUp('shift')
		self.client.enterText(' crontab')
		self.client.keyPress('enter')

	def setup(self):
		_t = dict()
		for string in setup_translations:
			_t[string] = setup_translations[string][self.args.language]
		self.client.waitForText(_t['domain'], timeout=self.timeout)
		if self.args.role == 'master':
			self.click(_t['new_domain'])
			self.click(_t['next'])
			self.client.waitForText(_t['account_information'], timeout=self.timeout)
			self.client.enterText('home')
			self.click(_t['next'])
		elif self.args.role in ['slave', 'backup', 'member']:
			self.click(_t['join_domain'])
			self.click(_t['next'])
			self.client.waitForText(_t['no_dc_dns'])
			self.click(_t['no_dc_dns_adapt'])
			self.click(_t['preferred_dns'])
			self.client.enterText(self.args.dns)
			self.client.keyPress('enter')
			time.sleep(60)
			self.click(_t['join_domain'])
			self.click(_t['next'])
			self.click(_t[self.args.role])
			self.client.keyPress('enter')
			self.client.waitForText(_t['start_join'])
			self.client.keyPress('tab')
			self.client.keyPress('tab')
			self.client.enterText(self.args.join_user)
			self.client.keyPress('tab')
			self.client.enterText(self.args.join_password)
			self.client.keyPress('enter')
		else:
			raise NotImplemented

		if self.args.role == 'master':
			self.client.waitForText(_t['host_settings'], timeout=self.timeout)
		else:
			self.client.waitForText(_t['system_name'])
		self.client.keyPress('end')
		for i in range(1, 200):
			self.client.keyPress('bsp')
		self.client.enterText(self.args.fqdn)
		self.client.keyPress('tab')
		self.click(_t['next'])

		if self.args.role == 'master':
			self.client.waitForText(_t['software_configuration'], timeout=self.timeout)
		else:
			self.client.waitForText(_t['software_configuration_non_master'], timeout=self.timeout)
		self.select_components()
		self.click(_t['next'])

		time.sleep(5)
		self.client.keyPress('enter')
		time.sleep(1000)

		self.client.waitForText(_t['setup_successful'], timeout=1000)
		self.click(_t['finish'])
		time.sleep(200)

	def select_components(self):
		# this is needed to make the down button work
		if 'all' in self.args.components:
			self.client.mouseMove(320, 215)
			self.client.mousePress(1)
		else:
			self.client.mouseMove(420, 270)
			self.client.mousePress(1)
			self.client.mousePress(1)
			for name, com in components.iteritems():
				if name in self.args.components:
					# go to the top
					for steps in range(1, 20):
						self.client.keyPress('up')
						time.sleep(0.2)
					for steps in range(1, com['steps']):
						self.client.keyPress('down')
						time.sleep(0.2)
					self.click(com[self.args.language])

	def bootmenu(self):
		try:
			self.client.waitForText('Univention Corporate Server Installer', timeout=120)
			self.client.keyPress('enter')
		except VNCDoException:
			self.connect()

	def installation(self):
		try:
			self.bootmenu()
			self.installer()
			self.setup()
			# TODO activate eth1 so that ucs-kvm-create can connect to instance
			# this is done via login and setting interfaces/eth0/type, is there a better way?
			self.configure_eth1()
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
	parser.add_argument('--password', default='univention')
	parser.add_argument('--organisation', default='ucs')
	parser.add_argument('--screenshot-dir', default='../screenshots')
	parser.add_argument('--dns')
	parser.add_argument('--join-user')
	parser.add_argument('--join-password')
	parser.add_argument('--language', default='deu', choices=['deu', 'eng', 'fra'])
	parser.add_argument('--role', default='master', choices=['master', 'slave', 'member', 'backup'])
	parser.add_argument('--components', default=[], choices=components.keys() + ['all'], action='append')
	args = parser.parse_args()
	assert args.vnc is not None
	if args.role in ['slave', 'backup', 'member']:
		assert args.dns is not None
		assert args.join_user is not None
		assert args.join_password is not None
	inst = UCSInstallation(args=args)
	inst.installation()

if __name__ == '__main__':
	main()
