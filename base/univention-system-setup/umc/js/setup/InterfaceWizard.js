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
	"dojo/string",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Wizard",
	'umc/widgets/MultiInput',
	'umc/widgets/ComboBox',
	'umc/widgets/TextBox',
	'umc/widgets/MultiSelect',
	'umc/widgets/CheckBox',
	'umc/widgets/NumberSpinner',
	"umc/modules/setup/types",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, string, tools, dialog, Wizard, MultiInput, ComboBox, TextBox, MultiSelect, CheckBox, NumberSpinner, types, _) {

	return declare("umc.modules.setup.InterfaceWizard", [ Wizard ], {

		name: null,
		interfaceType: null, // pre-defined interfaceType will cause a start on configuration page
		values: null,
		creation: null,

		physical_interfaces: null, // String[] physical interfaces
		available_interfaces: null, // object[] the grid items

		umcpCommand: tools.umcpCommand,
		style: 'width: 650px; height: 650px;',

		constructor: function(props) {
			var device = props.device;
			this.creation = props.creation;
			this.values = device;
			this.name = device.name;
			this.interfaceType = device.interfaceType;

			this.physical_interfaces = props.physical_interfaces || [];
			this.available_interfaces = props.available_interfaces || [];

			if (this.creation) {
				// WORKAROUND: the interfaceType widget must have an initial value, we set the first available by hand here
				try {
					this.values.interfaceType = types.Device.getPossibleDevices(this.available_interfaces, this.physical_interfaces, this.name)[0].id;
				} catch (AttributeError) {}
			}

			lang.mixin(this, {
				pages: [{
					name: 'interfaceType',
					headerText: _('Choose device type'),
					helpText: _('Several network types can be chosen. <i>Ethernet</i> is a standard physical device. ...'),
					widgets: [{
						// required to rename
						name: 'original_name',
						type: TextBox,
						value: props.original_name,
						visible: false
					}, {
						name: 'interfaceType',
						type: ComboBox,
						label: _('Interface type'),
						value: device.interfaceType,
						sortDynamicValues: false,
						dynamicValues: lang.hitch(this, function() {
							return types.Device.getPossibleDevices(this.available_interfaces, this.physical_interfaces, this.name);
						}),
						onChange: lang.hitch(this, function(interfaceType) {
							// adapt the visibility
							var visibility = {};
							switch(interfaceType) {
								case 'Ethernet':
									visibility = {name_eth: true, name_b: false, vlan_id: false, parent_device: false};
									break;
								case 'VLAN':
									visibility = {name_eth: false, name_b: false, vlan_id: true, parent_device: true};
									// TODO: re set vlan_id by count up to next available
									break;
								case 'Bridge':
								case 'Bond':
									visibility = {name_eth: false, name_b: true, vlan_id: false, parent_device: false};
									break;
							}
							tools.forIn(visibility, lang.hitch(this, function(widget, visible) {
								this.getWidget(widget).set('visible', visible);
							}));
							this.getWidget('name').set('value', this.name);
							this.getWidget('name_b').set('required', interfaceType == 'Bridge' || interfaceType == 'Bond');

							// A restriction in UCR enforces that Bridge, VLAN and Bond interfaces can not have multiple IP addresses (Bug #31767)
							if (interfaceType !== 'Ethernet') {
								this.getWidget('ip4').set('max', 1);
							}
						})
					}, {
						name: 'name',
						value: device.name,
						type: TextBox,
						validator: function(value) {
							return (/^[a-z]+[0-9]+(\.[0-9]+)?$/).test(value);
						},
						visible: false
					}, {
						name: 'name_b',
						label: _('Device'),
						value: device.name,
						size: 'Half',
						type: TextBox,
						validator: lang.hitch(this, function(value) {
							if (this.interfaceType === 'Bond' || this.interfaceType === 'Bridge') {
								return (/^[a-zA-Z]+[0-9]+$/).test(value);
							}
							return true;
						}),
						onChange: lang.hitch(this, function(name) {
							if (!this.getWidget('name_b').get('visible')) { return; }
							this.getWidget('name').set('value', name);
						})
					}, {
						name: 'name_eth',
						label: _('Device'),
						type: ComboBox,
						dynamicValues: lang.hitch(this, function() {
							return types.Ethernet.getPossibleSubdevices(this.available_interfaces, this.physical_interfaces, this.name);
						}),
						onChange: lang.hitch(this, function(name) {
							if (!this.getWidget('name_eth').get('visible')) { return; }
							this.getWidget('name').set('value', name);
						})
					}, {
						name: 'parent_device',
						label: _('Parent device'),
						type: ComboBox,
						dynamicValues: lang.hitch(this, function() {
							return types.VLAN.getPossibleSubdevices(this.available_interfaces, this.physical_interfaces, this.name);
						}),
						onChange: lang.hitch(this, function(parent_device) {
							if (!this.getWidget('parent_device').get('visible')) { return; }
							this.getWidget('name').set('value', parent_device + '.' + String(this.getWidget('vlan_id').get('value')));
						})
					}, {
						name: 'vlan_id',
						label: _('Virtual device ID'),
						type: NumberSpinner,
						size: 'Half',
						value: lang.hitch(this, function() {
							var vlan_id = 2; // some machines do not support 1, so we use 2 as default value
							// count up vlan_id to the next unused id
							while (array.some(this.available_interfaces, function(iface) { return iface.isVLAN() && iface.name == this.name && iface.vlan_id == vlan_id; })) {
								vlan_id++;
							}
							return vlan_id;
						})(),
						constraints: { min: 1, max: 4096 },
						validator: lang.hitch(this, function(value) {
							var name = this.name;
							return array.every(this.available_interfaces, function(iface) { return iface.name !== name; });
						}),
						onChange: lang.hitch(this, function(vlan_id) {
							if (!this.getWidget('vlan_id').get('visible')) { return; }
							this.getWidget('name').set('value', this.getWidget('parent_device').get('value') + '.' + String(vlan_id));
						})
					}]
				}, {
					name: 'network',
					headerText: _('Network device configuration'),
					helpText: _('Configure the %s network device %s', device.label, device.name),
					widgets: [{
						name: 'primary',
						label: _('Configure as primary network device'),
						type: CheckBox,
						value: !props.creation && this.name === props['interfaces/primary']
					}, {
						type: MultiInput,
						name: 'ip4',
						label: '',
						umcpCommand: this.umcpCommand,
						min: 3,
						subtypes: [{
							type: TextBox,
							label: _('IPv4 address'),
							validator: function(ip) {
								return !ip || /^[0-9.]+$/.test(ip);
							},
							sizeClass: 'Half'
						}, {
							type: TextBox,
							label: _('Netmask'),
							value: '255.255.255.0',
							validator: function(netm) {
								var nm = types.convertNetmask(netm);
								return !netm || !isNaN(nm) && nm < 33;
							},
							sizeClass: 'Half'
						}]
					}, {
						name: 'ip4dynamic',
						type: CheckBox,
						onChange: lang.hitch(this, function(value) {
							this.getWidget('ip4').set('disabled', !!value);
						}),
						label: _('Dynamic (DHCP)')
					}, {
						type: MultiInput,
						name: 'ip6',
						label: '',
						umcpCommand: this.umcpCommand,
						subtypes: [{
							type: TextBox,
							label: _('IPv6 address'),
							validator: function(ip) {
								return !ip || /^[0-9A-Fa-f:]+$/.test(ip);
							},
							sizeClass: 'One'
						}, {
							type: TextBox,
							label: _('IPv6 prefix'),
							validator: function(netm) {
								var nm = types.convertNetmask(netm);
								return !netm || !isNaN(nm) && nm < 129;
							},
							sizeClass: 'OneThird'
						}, {
							type: TextBox,
							label: _('Identifier'),
							sizeClass: 'OneThird'
						}]
					}, {
						type: CheckBox,
						name: 'ip6dynamic',
						onChange: lang.hitch(this, function(value) {
							this.getWidget('ip6').set('disabled', value);
						}),
						label: _('Autoconfiguration (SLAAC)')
					}, {
						type: MultiInput,
						name: 'options',
						value: device.options,
						subtypes: [{ type: TextBox }]
					}, {
						// required for DHCP query
						name: 'gateway',
						type: TextBox,
						visible: false
					}, {
						// required for DHCP query
						name: 'nameserver',
						type: MultiInput,
						subtypes: [{ type: TextBox }],
						max: 3,
						visible: false
					}, {
						// shall the interface be created in the grid do we edit a existing interface?
						name: 'creation',
						type: CheckBox,
						value: props.creation,
						disabled: true,
						visible: false
					}],
					buttons: lang.hitch(this, function() {
						if (device.isEthernet() && this.physical_interfaces.indexOf(device.name) !== -1) {
							// add DHCP button for physical Ethernet devices
							return [{
								name: 'dhcpquery',
								label: _('DHCP-Query'),
								callback: lang.hitch(this, function() { this._dhcpQuery(this.name); })
							}];
						}
						return [];
					})(),
					layout: lang.hitch(this, function() {
						var layout = [{
							label: _('network device'),
							layout: ['name', 'primary']
						}, {
							label: _('IPv4 network devices'),
							layout: [ 'ip4dynamic', 'dhcpquery', 'ip4' ]
						}, {
							label: _('IPv6 network devices'),
							layout: ['ip6dynamic', 'ip6']
						}];

						if (!device.isEthernet()) {
							// remove DHCP query from layout
							delete layout[1].layout[array.indexOf(layout[1].layout, 'dhcpquery')];
							layout[1].layout = array.filter(layout[1].layout, function(i) { return i !== undefined; });
						}
						return layout;
					})()
				}, {
					// A network bridge (software side switch)
					name: 'Bridge',
					headerText: _('Bridge configuration'),
					helpText: _('Configure the %s network device %s', device.label, device.name),
					widgets: [{
						name: 'bridge_ports',
						label: _('bridge ports'),
						type: MultiSelect,
						dynamicValues: lang.hitch(this, function() {
							return types.Bridge.getPossibleSubdevices(this.available_interfaces, this.physical_interfaces, this.name);
						})
					}, {
						name: 'bridge_fd',
						label: _('forwarding delay'),
						type: NumberSpinner,
						value: 0
					}, {
						type: MultiInput,
						name: 'bridge_options',
						label: _('UCR options'),
						value: device.options,
						subtypes: [{ type: TextBox }],
						onChange: lang.hitch(this, function(value) {
							if (this.interfaceType === 'Bridge') {
								this.getWidget('options').set('value', value);
							}
						})
					}],
					layout: [{
						label: _('Bridge device configuration'),
						layout: ['bridge_ports', 'bridge_fd', 'bridge_options']
					}]
				}, {
					name: 'Bond',
					headerText: _('Bond configuration'),
					helpText: _('Configure the %s network device %s', device.label, device.name),
					widgets: [{
						name: 'bond_slaves',
						label: _('Bond slaves'),
						type: MultiSelect,
						dynamicValues: lang.hitch(this, function() {
							return types.Bond.getPossibleSubdevices(this.available_interfaces, this.physical_interfaces, this.name);
						}),
						validator: lang.hitch(this, function(value) {
							if (this.interfaceType === 'Bond') {
								return value.length >= 1;
							}
							return true;
						})
					}, {
						name: 'bond_primary',
						label: _('Bond primary'),
						type: MultiInput,
						subtypes: [{
							type: ComboBox,
							depends: ['bond_slaves'],
							dynamicValues: lang.hitch(this, function(vals) {
								return vals['bond_slaves'];
							})
						}]
					}, {
						name: 'bond_mode',
						label: _('Mode'),
						type: ComboBox,
						staticValues: [{
							id: 0,
							label: 'balance-rr (0)'
						}, {
							id: 1,
							label: 'active-backup (1)'
						}, {
							id: 2,
							label: 'balance-xor (2)'
						}, {
							id: 3,
							label: 'broadcast (3)'
						}, {
							id: 4,
							label: '802.3ad (4)'
						}, {
							id: 5,
							label: 'balance-tlb (5)'
						}, {
							id: 6,
							label: 'balance-alb (6)'
						}]
					}, {
						name: 'miimon',
						label: _('MII link monitoring frequency'),
						type: NumberSpinner,
						constraints: { min: 0 },
						value: 100
					}, {
						type: MultiInput,
						name: 'bond_options',
						label: _('UCR options'),
						value: device.options,
						subtypes: [{ type: TextBox }],
						onChange: lang.hitch(this, function(value) {
							if (this.interfaceType === 'Bond') {
								this.getWidget('options').set('value', value);
							}
						})
					}],
					layout: [{
						label: _('Bond device configuration'),
						layout: ['bond_slaves', 'bond_primary']
					}, {
						label: _('Advanced configuration'),
						layout: ['bond_mode', 'miimon', 'bond_options']
					}]
				}]
			});

			return this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this.getWidget('name').watch('value', lang.hitch(this, function(name, old, value) {
				if (value) {
					this.set('name', value);
				}
			}));

			this.getWidget('interfaceType').watch('value', lang.hitch(this, function(name, old, value) {
				if (value) {
					this.set('interfaceType', value);
				}
			}));

			this.own(this.getWidget('ip4').watch('value', lang.hitch(this, function(attr, oldMultiValue, newMultiValue) {
				// auto-set netmask to 255.255.255.0
				var changeRequired = false;
				array.forEach(newMultiValue, function(newValue) {
					if (newValue[0] !== '' && newValue[1] === '') {
							newValue[1] = '255.255.255.0';
							changeRequired = true;
					}
				});
				if (changeRequired) {
					this.getWidget('ip4').set('value', newMultiValue);
				}
			})));

		},

		getValues: function() {
			var values = this.inherited(arguments);
			values.name = this.name;
			values.interfaceType = this.interfaceType;
			return values;
		},

		setValues: function(values) {
			// set values and trigger onChange event
			tools.forIn(values, function(iname, ivalue) {
				var iwidget = this.getWidget(iname);
				if (iwidget) {
					if (iwidget.setInitialValue) {
						iwidget.setInitialValue(ivalue);
					} else {
						iwidget.set('value', ivalue);
					}
				}
			}, this);
		},

		postCreate: function() {
			this.inherited(arguments);
			this.setValues(this.values);
		},

		canFinish: function(values) {

			var valid = values.interfaceType && values.name; // both must be set
			if (!valid) {
				dialog.alert(_('A valid device and device type have to be specified. Please correct your input.'));
			}

			if (this.interfaceType === 'Ethernet') {
				if (!(values.ip4.length || values.ip4dynamic || values.ip6.length || values.ip6dynamic)) {
					dialog.alert(_('At least one ip address have to be specified or DHCP or SLACC have to be enabled.'));
					return false;
				}
			}

			if (array.filter(values.ip6, function(ip6) {
				return (!ip6[2] && (ip6[0] || ip6[1]));
			}).length) {
				dialog.alert(_('Each IPv6 device must have an identifier'));
			}

			var pages = ['network'];
			if (this.creation) {
				pages.push('interfaceType');
			}
			array.forEach(['Bond', 'Bridge'], lang.hitch(this, function(type) {
				if (this.interfaceType === type) {
					pages.push(type);
				}
			}));

			array.forEach(pages, lang.hitch(this, function(page) {
				tools.forIn(this._pages[page]._form._widgets, function(iname, iwidget) {
					valid = valid && (!iwidget.get('visible') || (!iwidget.isValid || false !== iwidget.isValid()));
					valid = valid && (!iwidget.get('visible') || (!iwidget.validate || false !== iwidget.validate()));
					return valid;
				}, this);
			}));

			if (!valid) {
				dialog.alert(_('The entered data is not valid. Please correct the input.'));
			}
			return valid;
		},

		pageMap: { 'true': {
			// interfaceType
			Ethernet: {
				// currentPage: [ previous, next]
				'null': [null, 'interfaceType'],
				interfaceType: [null, 'network'],
				network: ['interfaceType', null]
			},
			VLAN: {
				'null': [null, 'interfaceType'],
				interfaceType: [null, 'network'],
				network: ['interfaceType', null]
			},
			Bridge: {
				'null': [null, 'interfaceType'],
				interfaceType: [null, 'Bridge'],
				Bridge: ['interfaceType', 'network'],
				network: ['Bridge', null]
			},
			Bond: {
				'null': [null, 'interfaceType'],
				interfaceType: [null, 'Bond'],
				Bond: ['interfaceType', 'network'],
				network: ['Bond', null]
			}
		}, 'false': {
			Ethernet: {
				'null': [null, 'network'],
				'network': [null, null]
			},
			VLAN: {
				'null': [null, 'network'],
				'network': [null, null]
			},
			Bridge: {
				'null': [null, 'Bridge'],
				Bridge: [null, 'network'],
				network: ['Bridge', null]
			},
			Bond: {
				'null': [null, 'Bond'],
				Bond: [null, 'network'],
				network: ['Bond', null]
			}
		}},

		hasNext: function(currentPage) {
			return !!this.next(currentPage);
		},

		next: function(currentPage) {
			return (this.pageMap[this.creation ? 'true' : 'false'][this.interfaceType][currentPage ? currentPage : 'null'] || [undefined, undefined])[1];
		},

		hasPrevious: function(currentPage) {
			return !!this.previous(currentPage);
		},

		previous: function(currentPage) {
			return (this.pageMap[this.creation ? 'true' : 'false'][this.interfaceType][currentPage ? currentPage : 'null'] || [undefined, undefined])[0];
		},

		_dhcpQuery: function(interfaceName) {
			// TODO: show a progressbar and success message?

			// make sure we have an interface selected
			if (!interfaceName) {
				dialog.alert(_('Please choose a network device before querying a DHCP address.'));
				return;
			}
			this.standby(true);
			tools.umcpCommand('setup/net/dhclient', {
				'interface': interfaceName
			}).then(lang.hitch(this, function(data) {
				this.standby(false);

				var result = data.result;
				var netmask = result[interfaceName + '_netmask'];
				var address = result[interfaceName + '_ip'];
				if (!address && !netmask) {
					dialog.alert(_('DHCP query failed.'));
					return;
				}

				var values = {
					ip4dynamic: false, // set "Dynamic (DHCP)" to false
					ip4: [[address, netmask]]
				};

				if (result.gateway || result.nameserver_1 && result.gateway != this.getWidget('gateway').get('value')) {
					var gw_string = '';
					if (result.gateway && result.gateway != this.getWidget('gateway').get('value')) {
						gw_string = string.substitute('<li>${0}: ${1}</li>', [_('gateway'), result.gateway]);
					}
					var ns_string = '';
					if (result.nameserver_1) {
						ns_string = string.substitute('<li>${0}: ${1:nameservers}</li>',
						                              [_('nameserver'), array.filter([result.nameserver_1, result.nameserver_2, result.nameserver_3], function(arg) { return arg;})], null,
						                              { nameservers: function(value, key) { return value.join(', '); }});
					}
					var gw_ns_string = '<ul>' + gw_string  + ns_string + '</ul>';
					dialog.confirm(_('Should the nameserver and gateway be set: %s', gw_ns_string), [{label: _('set'), name: 'yes'}, {label: _("don't set"), name: 'no'}]).then(lang.hitch(this, function(answer) {
	
						if (answer === 'yes') {
							values.gateway = result.gateway;
							values.nameserver = [[result.nameserver_1], [result.nameserver_2], [result.nameserver_3]];
						}
	
						this.setValues(values);
					}));
				} else {
					this.setValues(values);
				}
			}), lang.hitch(this, function(error) {
				this.standby(false);
				dialog.alert(_('DHCP query failed.'));
			}));
		}
	});
});
