/*
 * Copyright 2012 Univention GmbH
 *
 * http://www.univention.de/
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
 * <http://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/array",
	"umc/i18n!umc/modules/setup"
], function(array, _) {
	var self = {
		convertNetmask: function(nm) {
			if (/^[0-9]+$/.test(nm)) {
				return parseInt(nm, 10);
			}
			var num = 0;
			array.forEach(array.map(nm.split('.'), function(i) { return parseInt((parseInt(i, 10) + 1) / 32, 10); }), function(x) { num += x; });
			return num;
		},
		interfaceTypes: {
			'eth': _('Ethernet'),
			'vlan': _('Virtual LAN'),
			'bond': _('Bonding'),
			'br': _('Bridge')
		},
		interfaceTypeSorting: ['eth', 'vlan', 'br', 'bond'],
		interfaceValues: function() {
			return array.map(self.interfaceTypeSorting, function(id) {
				return {
					id: id,
					label: self.interfaceTypes[id]
				};
			});
		},
		filterInterfaces: function(/*String[]*/ interfaces, /*Object[]*/ available_interfaces) {
			// filter interfaces, which are available for use (because no interface already uses one of the interface)
			return array.filter(array.map(interfaces, function(/*String*/iface) {
				if (available_interfaces.length && !array.every(available_interfaces, function(/*Object*/item) {

					if (item.interfaceType === 'br' || item.interfaceType === 'bond') {
						// the interface is a bridge or bonding so it can contain subinterfaces
						var key = item.interfaceType === 'br' ? 'bridge_ports' : 'bond_slaves';
						if(item[key] && item[key].length) {
							return array.every(item[key], function(/*String*/_iface) {
								return _iface !== item['interface'];
							});
						}
						return true; // no subtypes (bridge)
					}

					return true; // interface without subinterfaces
				})) {
					return null;
				}
				return {
					id: iface,
					label: iface
				};
			}), function(v) { return v !== null; });
		}
	};

	return self;
});
