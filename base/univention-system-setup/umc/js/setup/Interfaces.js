/*
 * Copyright 2013-2019 Univention GmbH
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
	"dojo/store/Memory",
	"dojo/Stateful",
	"dojox/html/entities",
	"umc/tools",
	"umc/modules/setup/types",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, Memory, Stateful, entities, tools, types, _) {

	var Device = declare('umc.modules.setup.types.Device', null, {
		constructor: function(props, interfaces) {
			this.interfaces = interfaces;
			this.fromObject(props);
			this.label = types.interfaceTypeLabels[this.interfaceType];
		},

		_getDefaultValues: function() {
			return {
				name: null,
				interfaceType: null,
				ip4: [],
				ip6: [],
				ip4dynamic: false,
				ip6dynamic: false,
				options: []
			};
		},

		fromObject: function(obj) {
			// lang.mixin(this, this._getDefaultValues(), props); FIXME: only use allowed values
			tools.forIn(this._getDefaultValues(), function(key, val) {
				if (key in obj) {
					this[key] = obj[key];
				} else {
					this[key] = val;
				}
			}, this);
		},

		toObject: function() {
			var obj = {};
			tools.forIn(this._getDefaultValues(), function(key) {
				obj[key] = this[key];
			}, this);
			return obj;
		},

		getSubdeviceNames: function() {
			return [];
		},

		getSubdevices: function() {
			return array.map(this.getSubdeviceNames(), lang.hitch(this, function(devicename) {
				return this.interfaces.getInterface(devicename);
			}));
		},

		inUse: function() {
			return array.some(this.interfaces.getAllInterfaces(), lang.hitch(this, function(idevice) {
				return (-1 !== idevice.getSubdeviceNames().indexOf(this.name));
			}));
		},

		isPhysical: function() {
			return (-1 !== this.interfaces.physical_interfaces.indexOf(this.name));
		},

		isEthernet: function() { return this.interfaceType === 'Ethernet'; },
		isBridge: function() { return this.interfaceType === 'Bridge'; },
		isBond: function() { return this.interfaceType === 'Bond'; },
		isVLAN: function() { return this.interfaceType === 'VLAN'; },

		getConfigurationDescription: function() {
			var back = [];

			// display IP addresses
			var formatIPs = function(ips) {
				return array.map(array.filter(ips, function(i) { return i[0] && i[1]; }), function(i) { return i[0] + '/' + types.convertNetmask(i[1]);});
			};
			var ip4s = formatIPs(this.ip4);
			var ip6s = formatIPs(this.ip6);

			if (this.ip4dynamic) {
				back.push(entities.encode(_('Dynamic (DHCP)')));
			}
			if (this.ip6dynamic) {
				back.push(entities.encode(_('Autoconfiguration (SLAAC)')));
			}

			if (ip4s.length && !this.ip4dynamic){
				back.push(entities.encode(_('Static') + ': ' + ip4s.join(', ')));
			}
			if (ip6s.length && !this.ip6dynamic) {
				back.push(entities.encode(_('Static (IPv6)') + ': ' + ip6s.join(', ')));
			}

			return back.join('<br/>');
		},
		getSummary: function() {
			var description = this.getConfigurationDescription();
			if (description) {
				return description;
			}
			return entities.encode(_('Unconfigured'));
		}
	});
	var Ethernet = declare('umc.modules.setup.interfaces.Ethernet', [Device], {});
	var VLAN = declare('umc.modules.setup.interfaces.VLAN', [Device], {
		_getDefaultValues: function() {
			return lang.mixin(this.inherited(arguments), { vlan_id: null, parent_device: null });
		}//,
//		getSubdeviceNames: function() {
//			return [this.parent_device];
//		}
	});

	var Bond = declare('umc.modules.setup.interfaces.Bond', [Device], {
		_getDefaultValues: function() {
			return lang.mixin(this.inherited(arguments), {
				bond_slaves: [],
				bond_primary: [],
				bond_mode: 0,
				bond_miimon: null
			});
		},
		getSubdeviceNames: function() {
			return this.bond_slaves;
		},
		getConfigurationDescription: function() {
			var descr = this.inherited(arguments);
			var back = [];
			if (descr) {
				back.push(descr);
			}
			back.push(entities.encode(_('Bond slaves') + ': ' + this.bond_slaves.join(', ')));

			return back.join('<br/>');
		}
	});

	var Bridge = declare('umc.modules.setup.interfaces.Bridge', [Device], {
		_getDefaultValues: function() {
			return lang.mixin(this.inherited(arguments), {
				bridge_ports: [],
				bridge_fd: 0
			});
		},
		getSubdeviceNames: function() {
			return this.bridge_ports;
		},
		getConfigurationDescription: function() {
			var descr = this.inherited(arguments);
			var back = [];
			if (descr) {
				back.push(descr);
			}
			back.push(entities.encode(_('Bridge ports') + ': ' + this.bridge_ports.join(', ')));

			return back.join('<br/>');
		}
	});

	var DeviceToIdLabel = function(func) {
		return function(devicename) {
			return array.map(lang.hitch(this, func)(devicename), function(device) {
				return {id: device.name, label: device.name};
			});
		};
	};

	return declare("umc.modules.setup.Interfaces", [Stateful, Memory], {
		physical_interfaces: null, /* String[] */
		interfaceTypeSorting: ['Ethernet', 'VLAN', 'Bridge', 'Bond'],
		getAllTypes: function() {
			return array.map(this.interfaceTypeSorting, function(id) {
				return {
					id: id,
					label: types.interfaceTypeLabels[id]
				};
			});
		},
		getPossibleTypes: function(devicename) {
			var typesAvailable = {};

			tools.forIn({
				'Bond': this.getPossibleBondSubdevices(devicename),
				'Ethernet': this.getPossibleEthernetDevices(devicename),
				'Bridge': this.getPossibleBridgeSubdevices(devicename),
				'VLAN': this.getPossibleVLANParentdevices(devicename)
			}, function(itype, subdevices) {
				var typeAvailable = 0 < subdevices.length;
				typesAvailable[itype] = typeAvailable;
			});

			return array.filter(this.getAllTypes(), function(ientry) {
				return typesAvailable[ientry.id];
			});
		},
		getInterface: function(devicename) {
			return this.query({name: devicename})[0];
		},
		getAllInterfaces: function() {
			return this.query();
		},
		getPhysicalInterfaces: function() {
			return array.map(this.physical_interfaces, lang.hitch(this, function(devicename) {
				return this.getInterface(devicename) || this.createDevice({name: devicename, interfaceType: 'Ethernet'});
			}));
		},
		getAllAndPhysicalInterfaces: function() {
			var allInterfaces = this.getAllInterfaces();
			array.forEach(this.getPhysicalInterfaces(), function(device) {
				if (array.every(allInterfaces, function(idevice) { return idevice.name !== device.name; })) {
					allInterfaces.push(device);
				}
			});
			return allInterfaces;
		},
		getUnusedInterfaces: function() {
			return array.filter(this.getAllAndPhysicalInterfaces(), function(device) {
				return !device.inUse();
			});
		},
		getUsedInterfaces: function() {
			return array.filter(this.getAllAndPhysicalInterfaces(), function(device) {
				return device.inUse();
			});
		},
		getSubdevices: function(devicename) {
			var device = this.getInterface(devicename);
			if (device) {
				return device.getSubdevices();
			}
			return [];
		},
		getPossibleEthernetDevices: DeviceToIdLabel(function(devicename) {
			// all physical interfaces which are not already in the grid
			return array.filter(this.getPhysicalInterfaces(), lang.hitch(this, function(device) {
				return !this.getInterface(device.name);
			}));
		}),
		getPossibleVLANParentdevices: DeviceToIdLabel(function(devicename) {
			// return all interfaces which are not vlans
			var unusedInterfaces = this.getUnusedInterfaces();
			return array.filter(unusedInterfaces, function(device) {
				return !device.isVLAN();
			}).concat(this.getSubdevices(devicename));
			// FIXME: .concat(map(is_used_only_in_vlan, getUsedInterfaces()) ?
		}),
		getPossibleBondSubdevices: DeviceToIdLabel(function(devicename) {
			// only physical interfaces which are not already in use
			var unusedInterfaces = this.getUnusedInterfaces();
			return array.filter(unusedInterfaces, function(device) {
				return device.isPhysical();
			}).concat(this.getSubdevices(devicename));
		}),
		getPossibleBridgeSubdevices: DeviceToIdLabel(function(devicename) {
			// all interfaces which are not already in use and are not Bridges itself
			var unusedInterfaces = this.getUnusedInterfaces();
			return array.filter(unusedInterfaces, function(device) {
				return !device.isBridge();
			}).concat(this.getSubdevices(devicename));
		}),
		add: function(device) {
			device = this.createDevice(device);
			this.inherited(arguments, [device]);
		},
		put: function(device) {
			var device2 = this.createDevice(device);
			this.inherited(arguments, [device2]);
		},
		setData: function(data) {
			this.inherited(arguments, [array.map(data, lang.hitch(this, function(iface) { return this.createDevice(iface); }))]);
		},
		createDevice: function(device) {
			// get a Device from a object definition
			return ({
				'Ethernet': Ethernet,
				'VLAN': VLAN,
				'Bridge': Bridge,
				'Bond': Bond
			})[device.interfaceType](device, this);
		}
	});
});
