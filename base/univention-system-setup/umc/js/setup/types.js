/*
 * Copyright 2012-2013 Univention GmbH
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
			array.forEach(array.map(nm.split('.'), function(i) { return parseInt((parseInt(i, 10) + 1) / 32, 10); }), function(x) { num += x; });
			return num;
		},
		interfaceTypes: {
			'Ethernet': _('Ethernet'),
			'VLAN': _('Virtual LAN'),
			'Bond': _('Bonding'),
			'Bridge': _('Bridge')
		},
		interfaceTypeSorting: ['Ethernet', 'VLAN', 'Bridge', 'Bond'],
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

					if (item.isBridge() || item.isBond()) {
						// the interface is a bridge or bonding so it can contain subinterfaces
						var subdevs = item.getSubdevices();
						if(subdevs.length) {
							return array.every(subdevs, function(/*String*/_iface) {
								return _iface !== item.name;
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

	var Device = declare('umc.modules.setup.types.Device', null, {
		constructor: function(props) {
			this.interfaceType = props.interfaceType;
			this.name = props.name;
			this.ip4 = props.ip4 || [];
			this.ip6 = props.ip6 || [];
			this.ip4dynamic = props.ip4dynamic || false;
			this.ip6dynamic = props.ip6dynamic || false;
			this.primary = props.primary || false;
			this.options = props.options || [];
			this.label = self.interfaceTypes[this.interfaceType];
		},

		toObject: function() {
			return {
				interfaceType: this.interfaceType,
				name: this.name,
				ip4: this.ip4,
				ip6: this.ip6,
				ip4dynamic: this.ip4dynamic,
				ip6dynamic: this.ip6dynamic,
				primary: this.primary,
				options: this.options
			};
		},

		getSubdevices: function()  {
			return [];
		},

		isEthernet: function() { return this.interfaceType === 'Ethernet'; },
		isBridge: function() { return this.interfaceType === 'Bridge'; },
		isBond: function() { return this.interfaceType === 'Bond'; },
		isVLAN: function() { return this.interfaceType === 'VLAN'; },

		configuration_description: function() {
			var back = '';

			// display IP addresses
			var formatIPs = function(ips) {
				return array.map(array.filter(ips, function(i) { return i[0] && i[1]; }), function(i) { return i[0] + '/' + self.convertNetmask(i[1]);});
			};
			var ip4s = formatIPs(this.ip4);
			var ip6s = formatIPs(this.ip6);

			if (this.ip4dynamic) {
				back += _('Dynamic (DHCP)');
			}
			if (this.ip6dynamic) {
				if (back) {
					back += '<br>';
				}
				back += _('Autoconfiguration (SLAAC)');
			}

			if (ip4s.length && !this.ip4dynamic){
				if (back) {
					back += '<br>';
				}
				back += _('Static') + ': ';
				back += ip4s.join(', ');
			}
			if (ip6s.length && !this.ip6dynamic) {
				if (back) {
					back += '<br>';
				}
				back += _('Static (IPv6)') + ': ';
				back += ip6s.join(', ');
			}

			return back;
		}
	});
	self.Device = Device;
	Device.getPossibleDevices = function(all_interfaces, physical_interfaces, devicename) {

		var arr = self.interfaceValues();

		if (!self.Bond.getPossibleSubdevices(all_interfaces, physical_interfaces, devicename).length) {
			// == arr.pop('Bond')
			arr = array.filter(arr, function(i) { return i.id !== 'Bond'; });
		}

		if (!self.Ethernet.getPossibleSubdevices(all_interfaces, physical_interfaces, devicename).length) {
			arr = array.filter(arr, function(i) { return i.id !== 'Ethernet'; });
		}

		if (!self.Bridge.getPossibleSubdevices(all_interfaces, physical_interfaces, devicename).length) {
			arr = array.filter(arr, function(i) { return i.id !== 'Bridge'; });
		}

		if (!self.VLAN.getPossibleSubdevices(all_interfaces, physical_interfaces, devicename).length) {
			arr = array.filter(arr, function(i) { return i.id !== 'VLAN'; });
		}

		return arr;
	}
	self.Ethernet = declare('umc.modules.setup.types.Ethernet', [Device], {});
	self.Ethernet.getPossibleSubdevices = function(all_interfaces, physical_interfaces, devicename) {
		// all physical interfaces which are not already in the grid
		return array.filter(physical_interfaces, function(device) {
			return array.every(all_interfaces, function(idevice) { return idevice.name !== device; });
		});
	};
	self.VLAN = declare('umc.modules.setup.types.VLAN', [Device], {
		constructor: function(props) {
			this.vlan_id = props.vlan_id;
			this.parent_device = props.parent_device;
		},
		toObject: function() {
			return lang.mixin(this.inherited(arguments), {
				vlan_id: this.vlan_id,
				parent_device: this.parent_device
			});
		},
		getSubdevices: function()  {
			return [this.parent_device];
		}
	});
	self.VLAN.getPossibleSubdevices = function(all_interfaces, physical_interfaces, devicename) {
		// return all interfaces which are not vlans
		// NOTE: if the physical interface is not defined in the grid this could lead to errors, but the backend catches this

		var availableInterfaces = array.map(all_interfaces, function(item) {
			return item.name;
		});

		availableInterfaces = lang.clone(physical_interfaces).concat(availableInterfaces);

		// all interfaces which are not already in use
		var devices = [];
		array.forEach(availableInterfaces, function(device) {
			if (array.every(all_interfaces, function(idevice) {
				if (devicename != idevice.name) {
					if (idevice.isVLAN()) {
						return false;
					}
					return (-1 === idevice.getSubdevices().indexOf(device));
				}
				return true;
			})) {
				devices.push(device);
			}
		});
		return devices;
	};
	self.Bond = declare('umc.modules.setup.types.Bond', [Device], {
		constructor: function(props) {
			this.inherited(arguments);
			this.bond_slaves = props.bond_slaves || [];
			this.bond_primary = props.bond_primary || [];
			this.bond_mode = props.bond_mode || 0;
			this.miimon = props.miimon || null;
		},
		toObject: function() {
			return lang.mixin(this.inherited(arguments), {
				bond_slaves: this.bond_slaves,
				bond_primary: this.bond_primary,
				bond_mode: this.bond_mode,
				miimon: this.miimon
			});
		},
		getSubdevices: function()  {
			return this.bond_slaves;
		},
		configuration_description: function() {
			var back = this.inherited(arguments);
			if (back) {
				back += '<br>';
			}
			back += _('Bond slaves') + ': ' + this.bond_slaves.join(', ');
			return back;
		}
	
	});
	self.Bond.getPossibleSubdevices = function(all_interfaces, physical_interfaces, devicename) {
		// only physical interfaces which are not already in use
		var devices = [];
		array.forEach(physical_interfaces, function(device) {
			if (array.every(all_interfaces, function(idevice) {
				if (devicename != idevice.name) {
					return (-1 === idevice.getSubdevices().indexOf(device));
				}
				return true;
			})) {
				devices.push(device);
			}
		});
		return devices;
	};
	self.Bridge = declare('umc.modules.setup.types.Bridge', [Device], {
		constructor: function(props) {
			this.inherited(arguments);
			this.bridge_ports = props.bridge_ports || [];
			this.bridge_fd = props.bridge_fd || 0;
		},
		toObject: function() {
			return lang.mixin(this.inherited(arguments), {
				bridge_ports: this.bridge_ports,
				bridge_fd: this.bridge_fd
			});
		},
		getSubdevices: function()  {
			return this.bridge_ports;
		},
		configuration_description: function() {
			var back = this.inherited(arguments);
			if (back) {
				back += '<br>';
			}
			back += _('Bridge ports') + ': ' + this.bridge_ports.join(', ');
			return back;
		}
	});
	self.Bridge.getPossibleSubdevices = function(all_interfaces, physical_interfaces, devicename) {
		var availableInterfaces = array.map(all_interfaces, function(item) {
			return item.name;
		});

		availableInterfaces = lang.clone(physical_interfaces).concat(availableInterfaces);

		// all interfaces which are not already in use
		var devices = [];
		array.forEach(availableInterfaces, function(device) {
			if (array.every(all_interfaces, function(idevice) {
				if (devicename != idevice.name) {
					return (-1 === idevice.getSubdevices().indexOf(device));
				}
				return true;
			})) {
				devices.push(device);
			}
		});
		return devices;
	};

	self.getDevice = function(iface) {
		// get a Device from a object definition
		return self[iface.interfaceType](iface);
	};

	return self;
});
