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
	"dojo/string",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Wizard",
	'umc/widgets/MultiInput',
	'umc/widgets/ComboBox',
	'umc/widgets/TextBox',
	'umc/widgets/Text',
	'umc/widgets/MultiSelect',
	'umc/widgets/CheckBox',
	'umc/widgets/NumberSpinner',
	'umc/widgets/ProgressBar',
	"./types",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, string, tools, dialog, Wizard, MultiInput, ComboBox, TextBox, Text, MultiSelect, CheckBox, NumberSpinner, ProgressBar, types, _) {

	return declare("umc.modules.setup.InterfaceWizard", [ Wizard ], {

		autoValidate: true,

		ucsversion: null,
		interfaces: null,
		device: null,
		creation: null,

		umcpCommand: lang.hitch(tools, 'umcpCommand'),
		umcpProgressCommand: lang.hitch(tools, 'umcpProgressCommand'),

		getDeviceName: function() {
			try {
				return this.getWidget('name').get('value');
			} catch (to_early) {
				return '';
			}
		},

		getInterfaceType: function() {
			try {
				return this.getWidget('interfaceType').get('value') || 'Ethernet';
			} catch (to_early) {
				return 'Ethernet';
			}
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			this.creation = !this.device;

			var device = this.device || {};

			lang.mixin(this, {
				pages: [{
					name: 'interfaceType',
					headerText: _('Choose interface type'),
					helpText: _('Several network types can be chosen.') +
						'<ul><li>' + _('<i>Ethernet</i> is a standard physical interface.') +
						'</li><li>' +  _('<i>VLAN</i> interfaces can be used to separate network traffic logically while using only one or more physical network interfaces.') +
						'</li><li>' + _('<i>Bridge</i> interfaces allows a physical network interface to be shared to connect one or more network segments.') +
						'</li><li>' + _('<i>Bond</i> interfaces allows two or more physical network interfaces to be coupled.') + '</li></ul>' +
						_('Further information can be found in the <a href="https://docs.software-univention.de/manual-%s.html#computers:networkcomplex" target="_blank">UCS documentation</a>.', this.ucsversion),
					widgets: [{
						// required to rename
						name: 'original_name',
						type: TextBox,
						value: device.name,
						visible: false
					}, {
						name: 'interfaceType',
						type: ComboBox,
						label: _('Interface type'),
						disabled: !this.creation,
						sortDynamicValues: false,
						dynamicValues: lang.hitch(this, function() {
							var typenames = this.interfaces.getPossibleTypes(this.getDeviceName());
							if (this.device) {
								typenames.push({id: this.device.interfaceType, label: this.device.interfaceType});
							}
							return typenames;
						}),
						onChange: lang.hitch(this, function(interfaceType) {
							// adapt the visibility
							var visibility = {
								'Ethernet': {name_eth: true, name_b: false, vlan_id: false, parent_device: false},
								'VLAN': {name_eth: false, name_b: false, vlan_id: true, parent_device: true},
								'Bridge': {name_eth: false, name_b: true, vlan_id: false, parent_device: false},
								'Bond': {name_eth: false, name_b: true, vlan_id: false, parent_device: false}
							}[interfaceType];
							tools.forIn(visibility, lang.hitch(this, function(widget, visible) {
								this.getWidget(widget).set('visible', visible);
							}));

							// require devicename
							this.getWidget('name_b').set('required', interfaceType == 'Bridge' || interfaceType == 'Bond');

							// adapt visibility of DHCP button
							this._pages.network._form._buttons.dhcpquery.set('visible', interfaceType === 'Ethernet');

							// trigger reset of interface name to make sure that the 'name' widget contains the correct value
							var name = this.getWidget({
								'Ethernet': 'name_eth',
								'Bridge': 'name_b',
								'Bond': 'name_b',
								'VLAN': 'vlan_id'
							}[interfaceType]);
							if (name) {
								var value = name.get('value');
								name.set('value', null);
								name.set('value', value);
							}

//							var descriptions = {
//								'Ethernet': '',
//								'VLAN': '',
//								'Bridge': '',
//								'Bond': ''
//							};
//							this.getWidget('description').set('content', descriptions[interfaceType] + '<br/>');
//
							var name_b = this.getWidget('name_b');
							if (interfaceType === 'Bridge') {
								name_b.set('label', _('Name of new bridge interface'));
							} else if (interfaceType === 'Bond') {
								name_b.set('label', _('Name of new bonding interface'));
							}
						})
					}, {
						name: 'description',
						type: Text,
						content: ''
					}, {
						name: 'name',
						type: TextBox,
						validator: function(value) {
							if (value.length > 15 || value === '.' || value === '..') {
								return false;
							}
							return /^(?![.]{1,2}$)[^/ \t\n\r\f]{1,15}(\.[0-9]+)?$/.test(value);
						},
						visible: false
					}, {
						name: 'name_b',
						label: _('Name of new interface'),
						value: device.name,
						size: 'Half',
						type: TextBox,
						validator: lang.hitch(this, function(value) {
							if (this.getInterfaceType() === 'Bond' || this.getInterfaceType() === 'Bridge') {
								return /^(?![.]{1,2}$)[^/ \t\n\r\f]{1,15}$/.test(value);
							}
							return true;
						}),
						visible: false,
						onChange: lang.hitch(this, function(name) {
							if (!this.getWidget('name_b').get('visible')) { return; }
							if (!this.creation) { return; }
							this.getWidget('name').set('value', name);
						})
					}, {
						name: 'name_eth',
						label: _('Interface'),
						value: device.name,
						type: ComboBox,
						dynamicValues: lang.hitch(this, function() {
							return this.interfaces.getPossibleEthernetDevices(this.getDeviceName());
						}),
						visible: false,
						onChange: lang.hitch(this, function(name) {
							if (!this.getWidget('name_eth').get('visible')) { return; }
							if (!this.creation) { return; }
							this.getWidget('name').set('value', name);
						})
					}, {
						name: 'parent_device',
						label: _('Parent interface'),
						type: ComboBox,
						visible: false,
						dynamicValues: lang.hitch(this, function() {
							return this.interfaces.getPossibleVLANParentdevices(this.getDeviceName());
						}),
						onChange: lang.hitch(this, function(parent_device) {
							if (!this.getWidget('parent_device').get('visible')) { return; }
							if (!this.creation) { return; }

							var vlanSubDevices = array.filter(this.interfaces.getAllInterfaces(), lang.hitch(this, function(iface) {
								return iface.isVLAN() && iface.parent_device == parent_device;
							}));
							var vlan_id = 2; // some machines do not support 1, so we use 2 as default value
							vlan_id += vlanSubDevices.length;

							this.getWidget('vlan_id').set('value', vlan_id);

							this.getWidget('name').set('value', parent_device + '.' + String(this.getWidget('vlan_id').get('value')));
						})
					}, {
						name: 'vlan_id',
						label: _('VLAN ID'),
						type: NumberSpinner,
						size: 'Half',
						value: 2,
						constraints: { min: 1, max: 4096 },
						validator: lang.hitch(this, function(value) {
							if (this.getInterfaceType() === 'VLAN' && this.creation) {
								var name = this.getDeviceName();
								return array.every(this.interfaces.getAllInterfaces(), function(iface) { return iface.name !== name; });
							}
							return true;
						}),
						visible: false,
						onChange: lang.hitch(this, function(vlan_id) {
							if (!this.getWidget('vlan_id').get('visible')) { return; }
							if (!this.creation) { return; }
							this.getWidget('name').set('value', this.getWidget('parent_device').get('value') + '.' + String(vlan_id));
						})
					}]
				}, {
					name: 'network',
					headerText: _('Network interface configuration'),
					helpText: _('Configuration of IPv4 and IPv6 addresses'),
					widgets: [{
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
						value: this.creation,
						disabled: true,
						visible: false
					}],
					buttons: [{
						name: 'dhcpquery',
						label: _('DHCP-Query'),
						callback: lang.hitch(this, '_dhcpQuery')
					}],
					layout: [{
						label: _('IPv4 network interface configuration'),
						layout: [ 'ip4dynamic', 'dhcpquery', 'ip4' ]
					}, {
						label: _('IPv6 network interface configuration'),
						layout: ['ip6dynamic', 'ip6']
					}]
				}, {
					// A network bridge (software side switch)
					name: 'Bridge',
					headerText: _('Bridge configuration'),
					helpText: _('<i>Bridge</i> interfaces allows a physical network interface to be shared to connect one or more network segments.'),
					widgets: [{
						name: 'bridge_ports',
						label: _('Bridge ports'),
						description: _('Please specify the ports which will be added to the bridge.'),
						type: MultiSelect,
						dynamicValues: lang.hitch(this, function() {
							return this.interfaces.getPossibleBridgeSubdevices(this.getDeviceName());
						})
					}, {
						name: 'bridge_fd',
						label: _('Forwarding delay'),
						type: NumberSpinner,
						constraints: { min: 0 },
						value: 0
					}, {
						type: MultiInput,
						name: 'bridge_options',
						label: _('Additional bridge options'),
						description: _('Additional options for this network interface'),
						value: device.options,
						subtypes: [{ type: TextBox }],
						onChange: lang.hitch(this, function(value) {
							if (this.getInterfaceType() === 'Bridge') {
								this.getWidget('options').set('value', value);
							}
						})
					}],
					layout: [{
						label: _('Bridge interface configuration'),
						layout: ['bridge_ports', 'bridge_fd', 'bridge_options']
					}]
				}, {
					name: 'Bond',
					headerText: _('Bond configuration'),
					helpText: _('<i>Bond</i> interfaces allows two or more physical network interfaces to be coupled.'),
					widgets: [{
						name: 'bond_slaves',
						label: _('Bond slaves'),
						type: MultiSelect,
						dynamicValues: lang.hitch(this, function() {
							return this.interfaces.getPossibleBondSubdevices(this.getDeviceName());
						}),
						validator: lang.hitch(this, function(value) {
							if (this.getInterfaceType() === 'Bond') {
								return value.length >= 1;
							}
							return true;
						})
					}, {
						name: 'bond_primary',
						label: _('Bond primary'),
						type: MultiSelect,
						depends: ['bond_slaves'],
						dynamicValues: lang.hitch(this, function(vals) {
							return vals.bond_slaves;
						})
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
						name: 'bond_miimon',
						label: _('MII link monitoring frequency'),
						type: NumberSpinner,
						constraints: { min: 0 },
						value: 100
					}, {
						type: MultiInput,
						name: 'bond_options',
						label: _('Additional bonding options'),
						description: _('Additional options for this network interface'),
						value: device.options,
						subtypes: [{ type: TextBox }],
						onChange: lang.hitch(this, function(value) {
							if (this.getInterfaceType() === 'Bond') {
								this.getWidget('options').set('value', value);
							}
						})
					}],
					layout: [{
						label: _('Bond interface configuration'),
						layout: [['bond_slaves', 'bond_primary']]
					}, {
						label: _('Advanced configuration'),
						layout: ['bond_mode', 'bond_miimon', 'bond_options']
					}]
				}]
			});
		},

		buildRendering: function() {
			this.inherited(arguments);

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
			if (this.device) {
				this.setValues(this.device);
			} else {
				var itype = this.getInterfaceType();
				var parent_device = this.getWidget('parent_device').get('value');

				this.getWidget('interfaceType').set('value', null);
				this.getWidget('parent_device').set('value', null);

				this.setValues({
					interfaceType: itype,
					parent_device: parent_device
				});
			}
		},

		canFinish: function(values) {

//			if (this.getInterfaceType() === 'Ethernet') {
//				if (!(values.ip4.length || values.ip4dynamic || values.ip6.length || values.ip6dynamic)) {
//					dialog.alert(_('At least one ip address have to be specified or DHCP or SLAAC have to be enabled.'));
//					return false;
//				}
//			}

			// TODO: move into MultiInput.validate: Bug #33016
			if (array.filter(values.ip6, function(ip6) {
				return (!ip6[2] && (ip6[0] || ip6[1]));
			}).length) {
				dialog.alert(_('Each IPv6 interface must have an identifier'));
				return false;
			}
			return true;
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
			return (this.pageMap[this.creation ? 'true' : 'false'][this.getInterfaceType()][currentPage ? currentPage : 'null'] || [undefined, undefined])[1];
		},

		hasPrevious: function(currentPage) {
			return !!this.previous(currentPage);
		},

		previous: function(currentPage) {
			return (this.pageMap[this.creation ? 'true' : 'false'][this.getInterfaceType()][currentPage ? currentPage : 'null'] || [undefined, undefined])[0];
		},

		_dhcpQuery: function() {
			// TODO: show a progressbar and success message?

			var interfaceName = this.getDeviceName();
			// make sure we have an interface selected
			if (!interfaceName) {
				dialog.alert(_('Please choose a network interface before querying a DHCP address.'));
				return;
			}
			// workaround: use umcpProgressCommand() to make the setup/net/dhclient threaded
			var dummyProgressBar = new ProgressBar({});
			var dhcpDeferred = this.umcpProgressCommand(dummyProgressBar, 'setup/net/dhclient', {
				'interface': interfaceName
			}, false, 'network').then(lang.hitch(this, function(result) {

				var netmask = result[interfaceName + '_netmask'];
				var address = result[interfaceName + '_ip'];
				if (!address && !netmask) {
					dialog.alert(_('DHCP query failed.'));
					return;
				}

				this.setValues({
					ip4dynamic: false, // set "Dynamic (DHCP)" to false
					ip4: [[address, netmask]]
				});

				if (result.gateway || result.nameserver_1) {
					var nameservers = array.filter([result.nameserver_1, result.nameserver_2, result.nameserver_3], function(n) { return n;}).join(', ');
					var description = string.substitute('<ul><li>${0}: ${1}</li><li>${2}: ${3}</li></ul>', [_('Gateway'), result.gateway || _('None'), _('Nameserver'), nameservers]);

					dialog.confirm(_('Should the nameserver and gateway be set: %s', description), [
						{label: _("don't set"), name: 'no'},
						{label: _('set'), name: 'yes', 'default': true}
					]).then(lang.hitch(this, function(answer) {
						if (answer === 'yes') {
							this.setValues({
								gateway: result.gateway || '',
								nameserver: [[result.nameserver_1], [result.nameserver_2], [result.nameserver_3]]
							});
						}
					}));
				}
			}), lang.hitch(this, function(error) {
				dialog.alert(_('DHCP query failed.'));
			}));
			this.standbyDuring(dhcpDeferred);
		}
	});
});
