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
	"dijit/Dialog",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Grid",
	"umc/modules/setup/InterfaceWizard",
	"umc/modules/setup/types",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, Dialog, dialog, tools, Grid, InterfaceWizard, types, _) {
	return declare("umc.modules.setup.InterfaceGrid", [ Grid ], {
		moduleStore: null,

		style: 'width: 100%; height: 200px;',
		query: {},
		sortIndex: null,

		available_interfaces: [],

		gateway: "",
		nameserver: [],

		constructor: function() {
			lang.mixin(this, {
				columns: [{
					name: 'interface',
					label: _('Interface'),
					width: '20%'
				}, {
					name: 'interfaceType',
					label: _('Type'),
					width: '20%',
					formatter: function(value) {
						return types.interfaceTypes[value] || value;
					}
				}, {
					name: 'ipaddresses',
					label: _('IP addresses'),
					formatter: function(values) {
						return values.join(', <br>');
					},
					width: '40%'
				}],
				actions: [{
				// TODO: decide if we show the DHCP query action for every row?!
		//					name: 'dhcp_query',
		//					label: 'DHCP query',
		//					callback: lang.hitch(this, function() {
		//						// TODO: interface name
		//				//		this._dhcpQuery();
		//					}),
		//					isMultiAction: false,
		//					isStandardAction: true,
		//					isContextAction: true
		//				}, {
					name: 'edit',
					label: _('Edit'),
					iconClass: 'umcIconEdit',
					isMultiAction: false,
					isStandardAction: true,
					isContextAction: true,
					callback: lang.hitch(this, '_editInterface')
				}, {
					name: 'add',
					label: _('Add interface'),
					iconClass: 'umcIconAdd',
					isMultiAction: false,
					isStandardAction: false,
					isContextAction: false,
					callback: lang.hitch(this, '_addInterface')
				}, {
					name: 'delete',
					label: _('Delete'),
					iconClass: 'umcIconDelete',
					isMultiAction: true,
					isStandardAction: true,
					callback: lang.hitch(this, '_removeInterface')
				}]
			});
		},

		_getValueAttr: function() { return this.getAllItems(); },

		_setValueAttr: function(values) { // TODO: only on set initial value
			tools.forIn(values, function(id, value) {
				this.moduleStore.add(lang.mixin({'interface': id}, value));
			}, this);
		},

		_addInterface: function() {
			this._modifyInterface({});
		},

		_editInterface: function(name, props) {
			return this._modifyInterface(props[0]);
		},

		_modifyInterface: function(props) {
			// Add or modify an interface
			var _dialog = null, wizard = null;

			var _cleanup = function() {
				_dialog.hide();
				_dialog.destroyRecursive();
			};

			var _finished = lang.hitch(this, function(values) {
				delete values.dhcpquery;
				values.ipaddresses = types.formatIPs(values.ip4, values.ip6);
				if (props.interfaceType) {
					this.moduleStore.put( values ); // FIXME
					this.moduleStore.remove(values['interface']);
					this.moduleStore.add( values );
				} else {
					try {
						this.moduleStore.add( values );
					} catch(error) {
						dialog.alert(String(error));
					}
				}
				_cleanup();
			});
	
			props = {
				values: props,
				'interface': props['interface'],
				interfaceType: props.interfaceType,
				available_interfaces: this.available_interfaces,
				onCancel: _cleanup,
				onFinished: _finished
			};
			wizard = new InterfaceWizard(props);

			_dialog = new Dialog({
				title: props.interfaceType ? _('Edit a network interface') : _('Add a network interface'),
				content: wizard
			});
			_dialog.own(wizard);
			this.own(_dialog);
			_dialog.show();
		},

		_removeInterface: function(ids) {
			array.forEach(ids, function(iid) {
				this.moduleStore.remove(iid);
			}, this);
		}

	});
});
