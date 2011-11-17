/*
 * Copyright 2011 Univention GmbH
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
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._uvmm.InterfaceWizard");

dojo.require("umc.widgets.Wizard");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.TitlePane");
dojo.require("umc.modules._uvmm.types");

dojo.declare("umc.modules._uvmm.InterfaceWizard", [ umc.widgets.Wizard, umc.i18n.Mixin ], {
	
	i18nClass: 'umc.modules.uvmm',
	domain_type: null,
	values: {},

	constructor: function() {
		var types = umc.modules._uvmm.types;

		// mixin the page structure
		dojo.mixin(this, {
			pages: [{
				name: 'interface',
				headerText: this._('Add network interface'),
				helpText: this._('Two types of network interfaces are support. The first one is <i>Bridge</i> that requires a static network connection on the physical server that is configurated to be used for bridging. By default the network interface called eth0 is setup for such a case on each UVMM node. If a virtual instance should have more than one bridging network interface, additional network interfaces on the physical server must be configured first. The second type is <i>NAT</i> provides a private network for virtual instances on the physical server and permits access to the external network. This network typ is useful for computers with varying network connections like notebooks. For such an interface the network configuration of the UVMM node needs to be modified. This is done automatically by the UVMM service when starting the virtual instance. Further details about the network configuration can be found in <a target="_blank" href="http://sdb.univention.de/1172">this article</a>.'),
				widgets: [{
					name: 'type',
					type: 'ComboBox',
					label: this._('Type'),
					staticValues: types.interfaceTypes,
					value: this.values.type || 'bridge'
				}, {
					name: 'model',
					type: 'ComboBox',
					label: this._('Driver'),
					dynamicOptions: dojo.hitch(this, function() {
						return {
							domain_type: this.domain_type
						};
					}),
					dynamicValues: types.getInterfaceModels,
					sortDynamicValues: false,
					value: this.values.model || 'rtl8139'
				}, {
					name: 'source',
					type: 'TextBox',
					label: this._('Source'),
					description: this._('The source is the name of the network interface on the phyiscal server that is configured for bridging. By default it is eth0.'),
					value: this.values.source || 'eth0',
					required: true
				}, {
					name: 'mac_address',
					type: 'TextBox',
					regExp: '^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$',
					invalidMessage: this._('Invalid MAC address. The address should have the form, e.g., "01:23:45:67:89:AB".'),
					label: this._('MAC addresss'),
					value: this.values.mac_address || ''
				}]
			}]
		});
	},

	canFinish: function(values) {
		return this.getWidget('source').isValid() && this.getWidget('mac_address').isValid();
	}
});





