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
	"umc/modules/setup/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, when, tools, dialog, Wizard, Form, MultiInput, ComboBox, TextBox, Button, MultiSelect, CheckBox, types, _) {

	return declare("umc.modules.setup.InterfaceWizard", [ Wizard ], {

		'interface': null,

		interfaceType: null, // pre-defined interfaceType will cause a start on configuration page

		values: {},

		umcpCommand: tools.umcpCommand,

		style: 'width: 650px; height:650px;',
		available_interfaces: [],

		// do we modify or create an interface
		_create: false,

		constructor: function(props) {
			props = props || {};
			this.values = props.values || {};

			this._create = !props.interfaceType;

			if (this._create) {
				this.watch('interface', function(name, old, iface) {
					tools.forIn(this._pages, function(pname, page) {
						if (page._form._widgets['interface']) {
							page._form._widgets['interface'].set('value', iface);
						}
					}, this);
				});
				this.watch('interfaceType', function(name, old, interfaceType) {
					tools.forIn(this._pages, function(pname, page) {
						if (page._form._widgets.interfaceType) {
							page._form._widgets.interfaceType.set('value', interfaceType);
						}
					}, this);
				});
			}

			this['interface'] = props['interface'] || null;
			this.interfaceType = props.interfaceType || null;
			this.available_interfaces = props.available_interfaces || [];

			lang.mixin(this, {
				pages: [{
					name: 'interfaceType',
					headerText: _('Add interface'),
					helpText: _('What type of interface should be created?'),
					widgets: [{
						name: 'interfaceType',
						type: ComboBox,
						value: 'eth',
						staticValues: types.interfaceValues,
						onChange: lang.hitch(this, '_updateInterfaceWidgets')
					}, {
						name: 'interface',
						type: ComboBox,
						dynamicValues: lang.hitch(this, function() {
							return array.map(this.available_interfaces, function(idev) {
								return {id: idev, label: idev};
							});
						}),
						onChange: lang.hitch(this, '_updateInterface')
					}, {
						// required for DHCP query
						name: 'gateway',
						type: TextBox,
						visible: false
					}, {
						name: 'nameserver',
						type: MultiInput,
						subtypes: [{ type: TextBox }],
						max: 3,
						visible: false
					}]
				}, {
					// TODO: create a page for each interface type?
					name: 'interface',
					headerText: _('Configure a network interface'),
					helpText: _('Configure the given interface'),
					widgets: [{
						name: 'interface',
						type: ComboBox,
						disabled: true,
						value: props['interface'],
						size: 'Half',
						dynamicValues: lang.hitch(this, function() {
							return array.map(this.available_interfaces, function(idev) {
								return {id: idev, label: idev};
							});
						}),
						label: _('Interface')
					}, {
						name: 'interfaceType',
						type: ComboBox,
						disabled: true,
						value: props.interfaceType,
						size: 'Half',
						staticValues: types.interfaceValues,
						onChange: lang.hitch(this, '_updateInterfaceWidgets'),
						label: _('Interface type')
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
							this._pages['interface']._form._widgets.ip4.set('disabled', value);
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
							this._pages['interface']._form._widgets.ip6.set('disabled', value);
						}),
						label: _('Autoconfiguration (SLAAC)')
					}, {
						type: Button,
						name: 'dhcpquery',
						label: 'DHCP-Query', // FIXME: do not display the label two times
						canExecute: function() { // TODO: depends, not canExecute
							return true;
						}, // TODO: only eth interfaces are allowed to do a DHCP query
						callback: lang.hitch(this, function() { this._dhcpQuery(this['interface']); })
					}, {
						// TODO: implement
						type: CheckBox,
						name: 'vlan',
						label: _('Virtual LAN')
					}],
					layout: [{
						label: _('Interface'),
						layout: [ ['interface', 'interfaceType'] ]
					}, {
						label: _('IPv4 network devices'),
						layout: [ ['ip4dynamic', 'dhcpquery'], 'ip4' ]
					}, {
						label: _('IPv6 network devices'),
						layout: ['ip6dynamic', 'ip6']
					}, {
//						label: _('Global network settings'),
//						layout: [ 'vlan' ]
					}]
				}]
			});
		},

		setValues: function(values) {
			// set values and trigger onChange event
			tools.forIn(this._pages, function(pagename, page) {
				tools.forIn(values, function(iname, ivalue) {
					if (page._form._widgets[iname]) {
						page._form._widgets[iname].set('value', ivalue);
						page._form._widgets[iname]._set('value', ivalue); // FIXME: how to trigger onChange events
					}
				}, this);
			}, this);
		},

		postCreate: function() { // TODO: maybe startup?
			this.inherited(arguments);
			this.setValues(this.values);
		},

		canFinish: function(values) {
			var valid = true;

			if (!(values.ip4.length || values.ip4dynamic || values.ip6.length || values.ip6dynamic)) {
				dialog.alert(_('You have to specify at least one ip address or enable DHCP or SLACC.'));
				return false;
			}

			tools.forIn(this._pages['interface']._form._widgets, function(iname, iwidget) {
				valid = valid && (!iwidget.get('visible') || (!iwidget.isValid || false !== iwidget.isValid()));
				return valid;
			}, this);
			if (!valid) {
				dialog.alert(_('The entered data is not valid. Please correct your input.'));
			}
			return valid;
		},

		_dhcpQuery: function(interfaceName) {
			// TODO: show a notice that this will change gateway and nameserver
			// TODO: show a progressbar or success message?
			// make sure we have an interface selected
			if (!interfaceName) {
				dialog.alert(_('Please choose a network device before querying a DHCP address.'));
				return;
			}
			tools.umcpCommand('setup/net/dhclient', {
				'interface': interfaceName
			}).then(lang.hitch(this, function(data) {

				var result = data.result;
				var netmask = result[interfaceName + '_netmask'];
				var address = result[interfaceName + '_ip'];
				if (!address && !netmask) {
					dialog.alert(_('DHCP query failed.'));
					return;
				}

				this.setValues({
					ip4dynamic: false, // first set "Dynamic (DHCP)" to be false if it was not set
//				});
//				this.setValues({
//					ip4address: address,
//					ip4netmask: netmask,
					ip4: [[address, netmask]],
					gateway: result.gateway,
					nameserver: [[result.nameserver_1], [result.nameserver_2], [result.nameserver_3]]
				});
			}));
		},

		next: function(pageName) {
			return !this.interfaceType ? 'interfaceType': 'interface'/* this.inherited(arguments)*/ /*this.interfaceType*/;
		},

		hasPrevious: function() {
			return this._create ? this.inherited(arguments) : false;
		},

		_updateInterface: function(iface) {
			this['interface'] = iface;
			// TODO: watch on this.interface
			tools.forIn(this._pages, function(name, page) {
				if (page._form._widgets['interface']) {
					page._form._widgets['interface'].set('value', iface);
				}
			}, this);
		},

		_updateInterfaceWidgets: function(interfaceType) {
			this.interfaceType = interfaceType;
			if (interfaceType) {
				// update visibility
				tools.forIn(this._pages['interface']._form._widgets, function(iname, iwidget) {
					tools.forIn(types.interfaceTypes, function(typename) {
						// hide every widget which startswith one of the interface types but is not the setted interface type
						if (iname.indexOf(typename + '_') === 0) {
							iwidget.set('visible', typename === interfaceType);
						}
					}, this);
				}, this);
				// set interface type on second page
				this._pages['interface']._form._widgets.interfaceType.set('value', interfaceType);
				// set interface name based on the interface type
//				this._pages['interface']._form._widgets['interface'].set('value', '') // TODO
			}
		}
	});
});
