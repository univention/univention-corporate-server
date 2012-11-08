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

		physical_interfaces: [],

		gateway: "",
		nameserver: [],

		constructor: function() {
			lang.mixin(this, {
				columns: [{
					name: 'interface',
					label: _('Interface'),
					width: '15%'
				}, {
					name: 'interfaceType',
					label: _('Type'),
					width: '15%',
					formatter: function(value) {
						return types.interfaceTypes[value] || value;
					}
				}, {
					name: 'information',
					label: _('Information'),
					formatter: function(iface) {
						var back = '';
						// This value is a hack. We do not know about which identifier this row has so we added the whole information into iface.information
						if (iface.interfaceType === 'eth' || iface.interfaceType === 'vlan') {
							var formatIp = function(ips) {
								return array.map(ips, function(i) { return i[0] + '/' + types.convertNetmask(i[1]);}).join(', ');
							};
							back = _('IP addresses') + ': ';
							if (iface.ip4dynamic) {
								back += 'DHCP';
							} else if (iface.ip4.length){
								back += formatIp(iface.ip4);
							}
							if (iface.ip6dynamic) {
								back += ', <br>SLAAC';
							} else if (iface.ip6.length) {
								back += ', <br>' + formatIp(iface.ip6);
							}
						} else if (iface.interfaceType === 'br' || iface.interfaceType === 'bond') {
							back = _('Interfaces') + ': ' + iface.interfaces.join(', ');
						}
						return back;
					},
					width: '70%'
				}],
				actions: [{
				// TODO: decide if we show a DHCP query action for every row?!
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
					callback: lang.hitch(this, function(ids) {
						dialog.confirm(_('Please confirm the removal of the %d selected interfaces!', ids.length), [{
							label: _('Delete'),
							callback: lang.hitch(this, '_removeInterface', ids)
						}, {
							label: _('Cancel'),
							'default': true
						}]);
					})
				}]
			});
		},

		_getValueAttr: function() { return this.getAllItems(); },

		_setValueAttr: function(values) {
			// TODO: only on set initial value, i think there was something in the form which does that...
			tools.forIn(values, function(id, value) {
				this.moduleStore.add(lang.mixin({'interface': id}, value));
			}, this);
			// TODO: this method should delete the whole grid items and add the items from values
		},

		onChanged: function() {
			// event stub
		},

		updateValues: function(values, create) {
				delete values.dhcpquery;
				values.information = values;

				// if a DHCP query was done the values for gateway and nameserver are set
				// so we trigger on change event
				if (values.gateway !== '') {
					this.set('gateway', values.gateway);
				}
				if (values.nameserver.length) {
					// TODO: decide if the DHCP query can delete all nameservers by sending an empty nameserver?
					this.set('nameserver', values.nameserver);
				}

				if (values.interfaceType === 'eth') {

				} else if (values.interfaceType === 'vlan') {
					// The interface is build from interface:vlan_id
					values['interface'] = values['interface'] + ':' + String(values.vlan_id);

				} else if (values.interfaceType === 'bond') {
					// disable the interfaces which are used by this interface
					this.setDisabledItem(values.interfaces, true);
				} else if (values.interfaceType === 'br') {

				}

				if (!create) {
					this.moduleStore.put( values ); // FIXME: why does put not work? we have to manually remove and add it...
					this.moduleStore.remove(values['interface']);
					this.moduleStore.add( values );
				} else {
					try {
						this.moduleStore.add( values );
					} catch(error) {
						dialog.alert(_('Interface "%s" already exists', values['interface']));
						return;
					}
				}
				this.onChanged();
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
				this.updateValues(values, !props.interfaceType);
				_cleanup();
			});
	
			props = {
				values: props,
				'interface': props['interface'],
				interfaceType: props.interfaceType,
				physical_interfaces: this.physical_interfaces,
				available_interfaces: this.getAllItems(),
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
				var item = this.moduleStore.get(iid);
				if (item.interfaceType === 'bond') {
					// enable the interfaces which were blocked by this interface
					this.setDisabledItem(item.interfaces, false);
				}
				this.moduleStore.remove(iid);
			}, this);
			this.onChanged();
		}

	});
});
