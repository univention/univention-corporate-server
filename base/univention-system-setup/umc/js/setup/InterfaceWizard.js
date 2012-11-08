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
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/when",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Wizard",
	'umc/widgets/Form',
	'umc/widgets/MultiInput',
	'umc/widgets/ComboBox',
	'umc/widgets/TextBox',
	'umc/widgets/Button',
	'umc/widgets/MultiSelect',
	'umc/widgets/CheckBox',
	'umc/widgets/NumberSpinner',
	"umc/modules/setup/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, when, tools, dialog, Wizard, Form, MultiInput, ComboBox, TextBox, Button, MultiSelect, CheckBox, NumberSpinner, types, _) {

	return declare("umc.modules.setup.InterfaceWizard", [ Wizard ], {

		'interface': null,

		interfaceType: null, // pre-defined interfaceType will cause a start on configuration page

		values: {},

		umcpCommand: tools.umcpCommand,

		style: 'width: 650px; height: 650px;',
		physical_interfaces: [], // String[] physical interfaces
		available_interfaces: [], // object[] the grid items

//		// do we modify or create an interface
//		_create: false,

		constructor: function(props) {
			props = props || {};
			this.values = props.values || {};

//			this._create = props.create;

			this['interface'] = props['interface'];
			this.interfaceType = props.interfaceType;
			this.physical_interfaces = props.physical_interfaces || [];
			this.available_interfaces = props.available_interfaces || [];

			var name = (this.interfaceType !== 'vlan' ? this.interfaceType : 'eth');
			if (!name || !this['interface'] || this['interface'].substr(0, name.length) !== name ) {
				// name is illegal
				// TODO: error handling
			}

			lang.mixin(this, {
				pages: [{
					// A "normal" ethernet interface
					name: 'eth',
					headerText: _('Configure a network interface'),
					helpText: _('Configure the given interface'),
					widgets: [{
						name: 'interface',
						type: TextBox,
						disabled: true,
						value: props['interface'],
						size: 'Half',
						label: _('Interface')
					}, {
						type: MultiInput,
						name: 'ip4',
						label: '',
						umcpCommand: this.umcpCommand,
						min: 3,
						subtypes: [{
							type: TextBox,
							label: _('IPv4 address'),
							sizeClass: 'Half'
						}, {
							type: TextBox,
							label: _('Netmask'),
							sizeClass: 'Half'
						}]
					}, {
						name: 'ip4dynamic',
						type: CheckBox,
						onChange: lang.hitch(this, function(value) {
							this._pages.eth._form._widgets.ip4.set('disabled', value);
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
							sizeClass: 'One'
						}, {
							type: TextBox,
							label: _('IPv6 prefix'),
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
							this._pages.eth._form._widgets.ip6.set('disabled', value);
						}),
						label: _('Autoconfiguration (SLAAC)')
					}, {
						type: Button,
						name: 'dhcpquery',
						label: 'DHCP-Query', // FIXME: do not display the label two times
						callback: lang.hitch(this, function() { this._dhcpQuery(this['interface']); })
					}, {
						type: CheckBox,
						name: 'eth_vlan',
						value: false,
						label: _('enable Virtual LAN')
					}, {
						type: NumberSpinner,
						name: 'vlan_id',
						size: 'Half',
						value: 2, // some machines does not support 1 // TODO: count up if exists
						constraints: { min: 1, max: 4096 },
						label: _('Virtual interface ID')
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
					layout: [{
						label: _('Interface'),
						layout: [ ['interface', 'vlan_id'], 'eth_vlan' ]
					}, {
						label: _('IPv4 network devices'),
						layout: [ ['ip4dynamic', 'dhcpquery'], 'ip4' ]
					}, {
						label: _('IPv6 network devices'),
						layout: ['ip6dynamic', 'ip6']
//					}, {
//						label: _('Global network settings'),
//						layout: [ 'vlan' ]
					}]
				}, {
					// A network bridge (software side switch)
					name: 'br',
					headerText: _('Bridge configuration'),
					widgets: [{
						// defines which interfaces should be "bridged" together.
						// This can also be 0 to create an interface which does not have an connection to "the outside" (e.g. wanted in virtualisation)
						// There can exists an unlimited amount of interfaces
						name: 'interfaces',
						type: MultiSelect,
						dynamicValues: lang.hitch(this, function() {
							// mixin of physical interfaces and non physical
							return lang.mixin(this.getAvailableInterfaces(true), this.getPhysicalInterfaces(true)); // TODO: does this work? remove beneath code
//							return array.map(this.physical_interfaces.concat(this.getAvailableInterfaces(false)), function(iface) {
//								return {
//									id: iface,
//									label: iface
//								};
//							}, this);
						})
					}, {
						name: 'forwarding_delay',
						type: NumberSpinner,
						value: 0
					}],
					layout: [{
						label: _('configure the bridge interface'),
						layout: ['interfaces', 'forwarding_delay']
					}]
				}, {
					// A bonding interface (fallback if one interface falls out)
					// bond multiple interfaces into one. The used interfaces are not configurable anymore
					name: 'bond',
					headerText: _('Bond configuration'),
					widgets: [{
						name: 'interfaces',
						label: _('physical interfaces used for the bond interface'),
						type: MultiSelect,
						dynamicValues: lang.hitch(this, function() {
							// We can only use physical interfaces for this
							return this.getPhysicalInterfaces(true);
						})
					}, {
						name: 'primary',
						label: 'primary interface',
						type: ComboBox,
						depends: ['interfaces'],
						dynamicValues: lang.hitch(this, function() {
							return this.getPhysicalInterfaces(true);
						})
					}, {
						name: 'mode',
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
					}],
					layout: [{
						label: _('configure the bond interface'),
						layout: ['interfaces', 'primary', 'mode']
					}]
				}]
			});
		},

		buildRendering: function() {
			this.inherited(arguments);

			// update visibility of widgets
			tools.forIn(this._pages, function(iname, ipage) {
				tools.forIn(ipage._form._widgets, function(iname, iwidget) {
					tools.forIn(types.interfaceTypes, function(typename) {
						// hide every widget which startswith one of the interface types but is not the setted interface type
						if (iname.indexOf(typename + '_') === 0) {
							iwidget.set('visible', typename === this.interfaceType);
						}
					}, this);
				}, this);
			}, this);
		},

		getAvailableInterfaces: function(format) {
			return array.map(this.available_interfaces, function(item) {
				var iface = item['interface'];
				if (format) {
					return {
						id: iface,
						label: iface
					};
				}
				return iface;
			});
		},

		getPhysicalInterfaces: function(format) {
			if (format) {
				return array.map(this.physical_interfaces, function(idev) {
					return {id: idev, label: idev};
				});
			}
			return lang.clone(this.physical_interfaces);
		},

		setValues: function(values) {
			// set values and trigger onChange event
			tools.forIn(this._pages, function(pagename, page) {
				tools.forIn(values, function(iname, ivalue) {
					if (page._form._widgets[iname]) {
						page._form._widgets[iname].set('value', ivalue);
						page._form._widgets[iname]._set('value', ivalue); // FIXME: how to trigger onChange events // required?
					}
				}, this);
			}, this);
		},

		postCreate: function() {
			this.inherited(arguments);
			this.setValues(this.values);
		},

		startup: function() {
			this.inherited(arguments);
			// hack a bug
			this._pages.br._form._widgets.interfaces.startup();
			this._pages.bond._form._widgets.interfaces.startup();
		},

		canFinish: function(values) {
			var valid = this.interfaceType && this['interface']; // both must be set
			if (!valid) {
				dialog.alert(_('You have to specify a valid interface and interfaceType. Please correct your input.'));
			}

			var interfaceType = this.interfaceType === 'vlan' ? 'eth' : this.interfaceType; // The pagename for vlan interfaces is eth

			if (interfaceType === 'eth') {
				if (!(values.ip4.length || values.ip4dynamic || values.ip6.length || values.ip6dynamic)) {
					dialog.alert(_('You have to specify at least one ip address or enable DHCP or SLACC.'));
					return false;
				}
			}

			tools.forIn(this._pages[interfaceType]._form._widgets, function(iname, iwidget) {
				valid = valid && (!iwidget.get('visible') || (!iwidget.isValid || false !== iwidget.isValid()));
				return valid;
			}, this);

			if (!valid) {
				dialog.alert(_('The entered data is not valid. Please correct your input.'));
			}
			return valid;
		},

		next: function(pageName) {
//			if (!this.interfaceType) {
//				// if no interface type is set it have to be set
//				return 'interfaceType';
//			}
			if (this.interfaceType === 'vlan') {
				// The page for vlan interfaces is the same as normal eth interfaces
				return 'eth';
			}
			return this.interfaceType;
		},

//		previous: function(pageName) {
//			return 'interfaceType';
////			return this.interfaceType ? 'interfaceType' /*should be impossible*/ : 'interfaceType';
//		},

		hasPrevious: function(currentPage) {
			return false;
//			return this._create ? currentPage !== 'interfaceType' : false;
		},

		hasNext: function(currentPage) {
			return false;
//			return this._create ? currentPage == 'interfaceType': false;
		},

		_dhcpQuery: function(interfaceName) {
			// TODO: show a notice that this will change gateway and nameserver
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

				this.setValues({
					ip4dynamic: false, // set "Dynamic (DHCP)" to be false if it was not set
					ip4: [[address, netmask]],
					gateway: result.gateway,
					nameserver: [[result.nameserver_1], [result.nameserver_2], [result.nameserver_3]]
				});
			}), lang.hitch(this, function(error) {
				this.standby(false);
				dialog.alert(_('DHCP query failed.'));
			}));
		}
	});
});
