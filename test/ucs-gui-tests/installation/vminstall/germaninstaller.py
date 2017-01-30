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

from vncautomate import connect_vnc

from baseinstaller import Installer


class GermanInstaller(Installer):
	def __init__(self, vm_config):
		super(GermanInstaller, self).__init__(vm_config)

	def select_german_language(self):
		self.client.waitForText('select a language')

		# Reconnect due to screen resize. FIXME: This seems dirty. The
		# api.shutdown() is missing (vnc connection won't be closed).
		self.client = connect_vnc(self.host)
		self.client.updateOCRConfig(self.ocr_config)

		self.client.mouseClickOnText('English')
		self.client.enterText('German')
		self.client.keyPress('enter')

		self.set_ocr_lang('deu')

	def set_country_and_keyboard_layout(self):
		self.client.waitForText('Der hier ausgewählte Standort', timeout=30)
		self.client.keyPress('enter')

		self.client.waitForText('Tastatur konfigurieren', timeout=30)
		self.client.keyPress('enter')

	def network_setup(self):
		self.client.waitForText('Konfigurieren des Netzwerks mit DHCP', timeout=120)
		self.client.mouseClickOnText('Abbrechen')

		self.client.waitForText('Ihr Netzwerk benutzt möglicherweise nicht', timeout=30)
		self.client.keyPress('enter')

		self.client.waitForText('Netzwerk manuell einrichten', timeout=30)
		self.client.mouseClickOnText('Netzwerk manuell einrichten')
		self.client.keyPress('enter')
		self.client.waitForText('Die IP-Adresse ist für ihren Rechner eindeutig und kann zwei verschiedene Formate haben')
		self.client.enterText(self.vm_config.ip)
		self.client.keyPress('enter')

		# Skip network mask.
		self.client.waitForText('Durch die Netzmaske kann bestimmt', timeout=30)
		self.client.keyPress('enter')

		# Skip gateway server.
		self.client.waitForText('Geben Sie hier die IP-Adresse', timeout=30)
		self.client.keyPress('enter')

		# Skip DNS server.
		self.client.waitForText('um Rechnernamen im Internet aufzulösen', timeout=30)
		self.client.keyPress('enter')

	def account_setup(self):
		self.client.waitForText('Benutzer und Passwörter einrichten', timeout=30)
		self.client.enterText('univention')
		self.client.keyPress('tab')
		self.client.enterText('univention')
		self.client.keyPress('enter')

	def hdd_setup(self):
		self.client.waitForText('Der Installer kann Sie durch die Partitionierung einer Festplatte', timeout=60)
		self.client.keyPress('enter')
		self.client.waitForText('Beachten Sie, dass alle Daten auf der', timeout=30)
		self.client.keyPress('enter')
		self.client.waitForText('Es gibt verschiedene Möglichkeiten', timeout=30)
		self.client.keyPress('enter')

		# Remove logical volume data? This dialog only appears when the
		# hdd is not empty.
		#self.client.waitForText('dass durch diese Aktion auch alle Daten', timeout=30)
		#self.client.keyPress('down')
		#self.client.keyPress('enter')

		# write changes to devices and setup LVM?
		self.client.waitForText('Bevor der Logical Volume Manager konfiguriert werden kann', timeout=30)
		self.client.keyPress('down')
		self.client.keyPress('enter')

		# apply changes
		self.client.waitForText('Partitionierung beenden und Änderungen übernehmen', timeout=30)
		self.client.keyPress('enter')

		# write changes to disk?
		self.client.waitForText('Wenn Sie fortfahren, werden alle unten aufgeführten', timeout=30)
		self.client.keyPress('down')
		self.client.keyPress('enter')

	def setup_ucs(self):
		self.client.waitForText('Domäneneinstellungen', timeout=1200)
		self.client.mouseClickOnText('Erstellen einer euen UCS-Domäne')
		self.client.keyPress('enter')

		self.client.waitForText('Kontoinformationen', timeout=30)
		self.client.enterText('Univention GmbH')
		self.client.keyPress('enter')

		self.client.waitForText('Rechnereinstellungen', timeout=30)
		self.client.keyPress('enter')

		self.client.waitForText('Wählen Sie UCS-Software-Komponenten', timeout=30)
		self.client.mouseClickOnText('Weiter')
		self.client.waitForText('Bestätigen der Einstellungen', timeout=30)
		if not self.vm_config.update_ucs_after_install:
			self.client.mouseClickOnText('System nach der Einrichtung aktualisieren')
		self.client.keyPress('enter')

		self.client.waitForText('UCS-Einrichtung erfolgreich', timeout=2400)
		self.client.mouseClickOnText('Fertigstellen')

		# FIXME: The waitForText() function sends key-presses, while waiting.
		# This switches from the greeting-screen to console. So I'm looking
		# for a text, that appears in the console (as well).
		self.client.waitForText(self.vm_config.ip, timeout=360)
