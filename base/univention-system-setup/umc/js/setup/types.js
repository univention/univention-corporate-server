/*
 * Copyright 2012-2019 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, _) {
	var self = {
		convertNetmask: function(nm) {
			// 255.255.255.0 -> 24
			if (/^[0-9]+$/.test(nm)) {
				return parseInt(nm, 10);
			}
			var num = 0;
			array.forEach(nm.split('.'), function(i) {
				i = parseInt(i, 10);
				for (;i> 0; i = (i <<1) % 256) {
					num++;
				}
			});

			return num;
		},
		interfaceTypeLabels: {
			'Ethernet': _('Ethernet'),
			'VLAN': _('Virtual LAN'),
			'Bond': _('Bonding'),
			'Bridge': _('Bridge')
		}
	};

	return self;
});
