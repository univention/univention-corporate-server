/*
 * Copyright 2012-2014 Univention GmbH
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

		autoValidate: true,

		wizard_mode: null,
		interfaces: null,
		device: null,

		umcpCommand: tools.umcpCommand,
		style: 'width: 650px; height: 650px;',

		getDeviceName: function() {
			return this.device.name;
		},

		getInterfaceType: function() {
			return this.device.interfaceType;
		},

		getDeviceOptions: function() {
			return this.device.options;
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			var interfaceType = this.getInterfaceType();
			var pages = [];

			if (interfaceType == 'Bond') {
				pages.push(this.getBondPage());
			} else if (interfaceType == 'Bridge') {
				pages.push(this.getBridgePage());
			}
			
			pages.push(this.getNetworkPage());

			lang.mixin(this, {
				pages: pages
			});
		},

		getNetworkPage: function() {
			var interfaceType = this.getInterfaceType();

			var buttons = [];
			if (interfaceType === 'Ethernet') {
				buttons.push({
					name: 'dhcpquery',
					label: _('DHCP-Query'),
					callback: lang.hitch(this, '_dhcpQuery')
				});
			}

			// a restriction in UCR enforces that Bridge, VLAN and Bond interfaces can not have multiple IP addresses (Bug #31767)
			var maxIP4Adresses = Infinity;
			if (interfaceType !== 'Ethernet') {
				maxIP4Adresses = 1;
			}

			return {
				name: 'network',
				headerText: _('Network interface configuration'),
				helpText: _('Configuration of IPv4 and IPv6 adresses'),
				widgets: [{
					name: 'name',
					type: TextBox,
					value: this.getDeviceName(),
					visible: false
				}, {
					name: 'interfaceType',
					type: 'TextBox'
				}, {
					type: MultiInput,
					name: 'ip4',
					label: '',
					umcpCommand: this.umcpCommand,
					min: 3,
					max: maxIP4Adresses,
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
				}],
				buttons: buttons,
				layout: [{
					label: _('IPv4 network interface configuration'),
					layout: [ 'ip4dynamic', 'dhcpquery', 'ip4' ]
				}, {
					label: _('IPv6 network interface configuration'),
					layout: ['ip6dynamic', 'ip6']
				}]
			};
		},

		getBridgePage: function() {
			return {
				// A network bridge (software side switch)
				name: 'Bridge',
				headerText: _('Bridge configuration'),
				helpText: _('<i>Bridge</i> interfaces allows a physical network interface to be shared to connect one or more network segments. '),
				widgets: [{
					name: 'bridge_ports',
					label: _('Bridge ports'),
					description: _('Specifies the ports which will be added to the bridge.'),
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
					value: this.getDeviceOptions(),
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
			};
		},

		getBondPage: function() {
			return {
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
					name: 'miimon',
					label: _('MII link monitoring frequency'),
					type: NumberSpinner,
					constraints: { min: 0 },
					value: 100
				}, {
					type: MultiInput,
					name: 'bond_options',
					label: _('Additional bonding options'),
					description: _('Additional options for this network interface'),
					value: this.getDeviceOptions(),
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
					layout: ['bond_mode', 'miimon', 'bond_options']
				}]
			};
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

		postCreate: function() {
			this.inherited(arguments);
			this.setValues(this.device);
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

		canFinish: function(values) {

//			if (this.getInterfaceType() === 'Ethernet') {
//				if (!(values.ip4.length || values.ip4dynamic || values.ip6.length || values.ip6dynamic)) {
//					dialog.alert(_('At least one ip address have to be specified or DHCP or SLACC have to be enabled.'));
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

		_dhcpQuery: function() {
			// TODO: show a progressbar and success message?

			var interfaceName = this.getDeviceName();
			// make sure we have an interface selected
			if (!interfaceName) {
				dialog.alert(_('Please choose a network interface before querying a DHCP address.'));
				return;
			}
			this.standbyDuring(tools.umcpCommand('setup/net/dhclient', {
				'interface': interfaceName
			})).then(lang.hitch(this, function(data) {

				var result = data.result;
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
						{label: _('set'), name: 'yes', 'default': true},
						{label: _("don't set"), name: 'no'}
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
		}
	});
});
