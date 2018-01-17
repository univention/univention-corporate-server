# Copyright 2018 Univention GmbH
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

import tty
import termios
from fcntl import ioctl
from univention.config_registry.interfaces import Interfaces

TERMINAL = "/dev/tty0"

class RawInput(object):
	def __enter__(self):
		self.tty_settings = termios.tcgetattr(self.fd_tty)
		self.fd_tty = open(TERMINAL, 'r')
		tty.setraw(self.fd_tty)
		return self.fd_tty

	def __exit__(self, exc_type, exc, exc_tb):
		termios.tcsetattr(self.fd_tty, termios.TCSADRAIN, self.tty_settings)
		self.fd_tty.close()

def wait_for_keypress():
	key_pressed = 0
	esc_key = chr(27)
	with RawInput() as fd_tty:
		while key_pressed != esc_key:
			key_pressed = fd_tty.read(1)[0]

def set_terminal_to_text_mode():
	# plymouth quit --retain-splash lets the terminal stay in graphics mode.
	# The terminal needs to be set into text mode again.
	# See also "man console_ioctl" keyword: KDSETMODE.
	with open(TERMINAL, 'r') as fd_tty:
		ioctl(fd_tty, 0x4B3A, 0x00)

def get_all_ip_addresses():
	ips = [interface[1]["address"] for interface in Interfaces().all_interfaces]
	return ips

def print_all_umc_addresses():
	protocol = 'https://'
	ips = get_all_ip_addresses()
	umc_addresses = ''
	for ip in ips:
		umc_addresses += protocol + ip
	print(umc_addresses)
