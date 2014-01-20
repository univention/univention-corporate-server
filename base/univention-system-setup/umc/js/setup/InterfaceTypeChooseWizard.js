/*
 * Copyright 2014 Univention GmbH
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
	"umc/tools",
	"umc/widgets/Wizard",
	'umc/widgets/ComboBox',
	'umc/widgets/TextBox',
	'umc/widgets/NumberSpinner',
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, tools, Wizard, ComboBox, TextBox, NumberSpinner, _) {

	return declare("umc.modules.setup.InterfaceTypeChooseWizard", [ Wizard ], {

		style: 'width: 650px; height: 650px;',
		autoValidate: true,

		ucsversion: null,
		wizard_mode: null,
		interfaces: null,

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

			var typePage = {
				name: 'interfaceType',
				headerText: _('Choose interface type'),
				helpText: this.getHelpText(),
				widgets: [{
					name: 'interfaceType',
					type: ComboBox,
					label: _('Interface type'),
					sortDynamicValues: false,
					dynamicValues: lang.hitch(this, 'getPossibleTypes'),
					onChange: lang.hitch(this, 'onInterfaceTypeChanged')
				}, {
					name: 'name',
					type: TextBox,
					validator: function(value) {
						return (/^[a-z]+[0-9]+(\.[0-9]+)?$/).test(value);
					},
					visible: false
				}, {
					name: 'name_b',
					label: _('Name of new interface'),
					size: 'Half',
					type: TextBox,
					validator: lang.hitch(this, function(value) {
						if (this.getInterfaceType() === 'Bond' || this.getInterfaceType() === 'Bridge') {
							return (/^[a-zA-Z]+[0-9]+$/).test(value);
						}
						return true;
					}),
					visible: false,
					onChange: lang.hitch(this, function(name) {
						if (!this.getWidget('name_b').get('visible')) { return; }
						this.getWidget('name').set('value', name);
					})
				}, {
					name: 'name_eth',
					label: _('Interface'),
					type: ComboBox,
					dynamicValues: lang.hitch(this, function() {
						return this.interfaces.getPossibleEthernetDevices(this.getDeviceName());
					}),
					visible: false,
					onChange: lang.hitch(this, function(name) {
						if (!this.getWidget('name_eth').get('visible')) { return; }
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
						if (this.getInterfaceType() === 'VLAN') {
							var name = this.getDeviceName();
							return array.every(this.interfaces.getAllInterfaces(), function(iface) { return iface.name !== name; });
						}
						return true;
					}),
					visible: false,
					onChange: lang.hitch(this, function(vlan_id) {
						if (!this.getWidget('vlan_id').get('visible')) { return; }
						this.getWidget('name').set('value', this.getWidget('parent_device').get('value') + '.' + String(vlan_id));
					})
				}]
			};

			lang.mixin(this, {
				pages: [typePage]
			});
		},

		getFooterButtons: function() {
			var buttons = this.inherited(arguments);
			array.forEach(buttons, function(button) {
				if (button.name == 'finish') {
					button.label = _('Next ');
				}
			});
			return buttons;
		},

		getHelpText: function() {
			if (this.wizard_mode) {
				return '';
			}
			return _('Several network types can be chosen.') +
				'<ul><li>' + _('<i>Ethernet</i> is a standard physical interface. ') +
				'</li><li>' +  _('<i>VLAN</i> interfaces can be used to separate network traffic logically while using only one or more physical network interfaces. ') +
				'</li><li>' + _('<i>Bridge</i> interfaces allows a physical network interface to be shared to connect one or more network segments. ') +
				'</li><li>' + _('<i>Bond</i> interfaces allows two or more physical network interfaces to be coupled.') + '</li></ul>' +
				_('Further information can be found in the <a href="http://docs.univention.de/manual-%s.html#computers:networkcomplex" target="_blank">UCS documentation</a>.', this.ucsversion);
		},

		getPossibleTypes: function() {
			if (this.wizard_mode) {
				return [{id: 'Ethernet', label: 'Ethernet'}];
			}
			return this.interfaces.getPossibleTypes(this.getDeviceName());
		},

		onInterfaceTypeChanged: function(interfaceType) {
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

			// trigger reset of interface name to make sure that the 'name' widget contains the correct value
			var name = this.getWidget({
				'Ethernet': 'name_eth',
				'Bridge': 'name_b',
				'Bond': 'name_b',
				'VLAN': 'vlan_id'
			}[interfaceType]);
			if (name === false) {
				return;
			}
			var value = name.get('value');
			name.set('value', null);
			name.set('value', value);

			var name_b = this.getWidget('name_b');
			if (interfaceType === 'Bridge') {
				name_b.set('label', _('Name of new bridge interface'));
			} else if (interfaceType === 'Bond') {
				name_b.set('label', _('Name of new bonding interface'));
			}
		},

		postCreate: function() {
			this.inherited(arguments);
			var itype = this.getInterfaceType();
			var parent_device = this.getWidget('parent_device').get('value');

			this.getWidget('interfaceType').set('value', null);
			this.getWidget('parent_device').set('value', null);

			this.setValues({
				interfaceType: itype,
				parent_device: parent_device
			});
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
		}

	});
});
