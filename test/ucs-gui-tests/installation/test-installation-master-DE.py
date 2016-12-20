#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Python VNC automate
#
# Copyright 2016 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.
#

import argparse
from time import sleep
from vncautomate import VNCConnection, init_logger, connect_vnc
from vncautomate.cli import add_config_options_to_parser, get_config_from_args


def test(host, config):
	with VNCConnection(host) as client:
		client.updateOCRConfig(config)

		client.waitForText('start with default settings')
		client.keyPress('enter')
		client.waitForText('select a language')

		# reconnect due to screen resize
		client = connect_vnc(host)
		client.mouseClickOnText('German')
		client.mouseClickOnText('Continue')

		# switch to OCR with German dictionary!
		config.update(lang='deu')
		client.updateOCRConfig(config)

		# locale settings
		client.mouseClickOnText('Weiter')
		client.mouseClickOnText('Weiter', defer=2)

		# cancel DHCP setup
		client.waitForText('Konfigurieren des Netzwerks mit DHCP', timeout=120)
		client.mouseClickOnText('Abbrechen')

		# manual network setting
		client.mouseClickOnText('Weiter')
		client.mouseClickOnText('Netzwerk manuell einrichten')
		client.mouseClickOnText('Weiter')
		client.waitForText('Die IP-Adresse ist für ihren Rechner eindeutig und kann zwei verschiedene Formate haben')
		client.enterText('10.200.26.150')
		client.mouseClickOnText('Weiter')
		client.mouseClickOnText('Weiter', defer=2)
		client.mouseClickOnText('Weiter', defer=2)
		client.mouseClickOnText('Weiter', defer=2)
		client.waitForText('Benutzer und Passwörter einrichten')
		client.enterText('univention')
		client.keyPress('tab')
		client.enterText('univention')
		client.mouseClickOnText('Weiter')

		# manual hard disk partioning
		client.waitForText('Der Installer kann Sie durch die Partitionierung einer Festplatte', timeout=60)
		client.mouseClickOnText('Weiter')
		client.mouseClickOnText('Weiter', defer=2)
		client.mouseClickOnText('Weiter', defer=2)

		# remove logical volume data?
		sleep(2)
		client.keyPress('down')
		client.mouseClickOnText('Weiter', defer=2)

		# write changes to devices and setup LVM?
		sleep(2)
		client.keyPress('down')
		client.mouseClickOnText('Weiter', defer=2)

		# apply changes
		client.mouseClickOnText('Weiter', defer=2)

		# write changes to disk?
		sleep(2)
		client.keyPress('down')
		client.mouseClickOnText('Weiter', defer=2)

		# progressbar
		client.waitForText('Zusätzliche Software installieren', timeout=600)
		client.waitForText('Univention Corporate Server Setup', timeout=300)

		# UMC system setup
		client.waitForText('Domäneneinstellungen', timeout=120)
		client.mouseClickOnText('Erstellen einer euen UCS-Domäne')
		client.mouseClickOnText('Weiter')
		client.mouseClickOnText('Name der Organisation', defer=2)
		client.enterText('Univention GmbH')
		client.mouseClickOnText('Weiter')
		client.mouseClickOnText('Weiter', defer=2)
		client.mouseClickOnText('Weiter', defer=2)
		client.mouseClickOnText('System konfigurieren', defer=2)

		# progressbar
		client.waitForText('Domäneneinstellungen', timeout=300)
		client.waitForText('Einrichten der Systemrolle', timeout=300)
		client.waitForText('Domäneneinrichtung (dies kann einige Zeit dauern)', timeout=300)
		client.waitForText('Aktualisiere das System', timeout=600)
		client.waitForText('UCS-Einrichtung erfolgreich', timeout=600)

		# finish setup
		client.mouseClickOnText('Fertigstellen')

		# progressbar
		client.waitForText('Installation abschließen', timeout=60)

		# welcome screen
		client.waitForText('Willkommen auf Univention Corporate Server', timeout=300)


def parse_args():
	parser = argparse.ArgumentParser(description='VNC example test')
	parser.add_argument('host', metavar='vnc_host', help='Host with VNC port to connect to')
	add_config_options_to_parser(parser)
	args = parser.parse_args()
	config = get_config_from_args(args)
	return args, config


if __name__ == '__main__':
	init_logger('info')
	args, config = parse_args()
	test(args.host, config)
