#!/usr/bin/python3
#
# Univention Updater
#  collect statistics
#
# Copyright 2016-2021 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

from typing import Any, Callable, List, NoReturn, Optional, Tuple

from univention.admin.license import _license
from univention.admin.uldap import access, getAdminConnection, position
from univention.config_registry import ConfigRegistry
from univention.config_registry.frontend import ucr_update


def encode_number(number: int, significant_digits: int = 3) -> str:
	assert 0 <= number <= int('9' * 26)
	assert 1 < significant_digits
	string = str(number)
	return string[:significant_digits] + ' abcdefghijklmnopqrstuvwxyz'[len(string)]


def encode_users(users: int) -> str:
	return encode_number(users)


def encode_role(role: str) -> str:
	if role == 'domaincontroller_master':
		return 'M'
	if role == 'domaincontroller_backup':
		return 'B'
	if role == 'domaincontroller_slave':
		return 'S'
	if role == 'memberserver':
		return 'm'
	if role == 'basesystem':
		return 'b'
	raise ValueError('Invalid role %r' % (role, ))


def encode_additional_info(users: Optional[int] = None, role: Optional[str] = None) -> str:
	data: List[Tuple[str, Callable[[Any], str], Any]] = [
		('U', encode_users, users),
		('R', encode_role, role),
	]
	return ",".join(
		"%s:%s" % (key, encoder(datum))
		for key, encoder, datum in data
		if datum is not None
	)


def getReadonlyAdminConnection() -> Tuple[access, position]:
	def do_nothing(*a: Any, **kw: Any) -> NoReturn:
		raise AssertionError('readonly connection')

	lo, position = getAdminConnection()
	lo.add = lo.modify = lo.rename = lo.delete = do_nothing
	return lo, position


def main() -> None:
	def get_role() -> Optional[str]:
		return configRegistry.get('server/role', None)

	def get_users() -> Optional[int]:
		if get_role() != 'domaincontroller_master':
			return None
		lo, _ = getReadonlyAdminConnection()
		filter = _license.filters['2'][_license.USERS]
		return len(lo.searchDn(filter=filter))

	configRegistry = ConfigRegistry()
	configRegistry.load()
	ucr_update(
		configRegistry,
		{
			'updater/statistics': encode_additional_info(users=get_users(), role=get_role()),
		}
	)


if __name__ == "__main__":
	main()
