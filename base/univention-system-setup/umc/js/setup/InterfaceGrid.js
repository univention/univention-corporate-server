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
	"dojo/aspect",
	"dijit/Dialog",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Grid",
	"umc/widgets/Form",
	"umc/widgets/ComboBox",
	"umc/widgets/TextBox",
	"umc/modules/setup/InterfaceWizard",
	"umc/modules/setup/types",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, aspect, Dialog, dialog, tools, Grid, Form, ComboBox, TextBox, InterfaceWizard, types, _) {
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
						// This value 'iface' is a hack. We do not know about which identifier this row has so we added the whole information into iface.information
						var back = '';
						if (((iface.interfaceType === 'eth' || iface.interfaceType === 'vlan') && iface.type !== 'manual') || (iface.interfaceType === 'bond' || iface.interfaceType === 'br')) {
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
						}
						if (iface.interfaceType === 'br' || iface.interfaceType === 'bond') {
							back += '<br>' + _('Interfaces') + ': ' + iface[iface.interfaceType === 'br' ? 'bridge_ports' : 'bond-slaves'].join(', ');
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
			// TODO: this method should delete the whole grid items and add the items from values
		},

		setInitialValue: function(values) {
			tools.forIn(values, function(id, value) {
				try {
					this.moduleStore.add(lang.mixin({'interface': id}, value));
				} catch(e) {}
			}, this);
		},

		onChanged: function() {
			// event stub
		},

		updateValues: function(values, create) {
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
					// The interface is build from interface.vlan_id
					values['interface'] = values['interface'] + '.' + String(values.vlan_id);

				} else if (values.interfaceType === 'bond' || values.interfaceType === 'br') {
					values.start = true;
					// disable the interfaces which are used by this interface
					var key = values.interfaceType === 'bond' ? 'bond-slaves' : 'bridge_ports';
					this.setDisabledItem(values[key], true);
					// set original values
					array.forEach(values[key], lang.hitch(this, function(ikey) {
						var item = this.moduleStore.get(ikey);
//						item.original = lang.clone(item); // FIXME: RangeError: Maximum call stack size exceeded
						item.original = item;

						// set values to deactivate the interface values
						item.ip4 = [];
						item.ip6 = [];
						item.ip4dynamic = false;
						item.ip6dynamic = false;
						item.type = 'manual';
						item.start = false;

						// FIXME: put does not overwrite
						this.moduleStore.put(item);
						this.moduleStore.remove(item['interface']);
						this.moduleStore.add(item);
					}));
				}

				values.information = values;

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
			if (props.interfaceType) {
				// only edit the existing interace
				props.create = false;
				this._showWizard(props);
				return;
			}

			var form = null;
			var dynamicInterfaceTypeValues = lang.hitch(this, function() {
				// TODO: lookup if interfaces are already in use
				var d = types.interfaceValuesDict();
				if (this.physical_interfaces.length < 2) {
					// We can not use a bonding interface if we don't have two physical interfaces
					delete d.bond;
				}
				if (array.every(this.physical_interfaces, lang.hitch(this, function(iface) {
					var ifaces = this.get('value');
					return ifaces.length !== 0 ? array.some(ifaces, function(val) { return iface === val['interface']; }) : false;
				}))) {
					// if all physical interfaces are configured we can not configure another
					delete d.eth;
				}
				var arr = [];
				tools.forIn(d, function(k, v) {
					arr.push(v);
				});
				return arr;
			});

			var hack = {foo: dynamicInterfaceTypeValues};
			aspect.after(hack, 'foo', function(ret) { 
				if (array.every(ret, function(item) { return item.id !== 'eth'; })) {
					form._widgets.interfaceType.set('value', 'vlan');
				}
			});

			form = new Form({
				widgets: [{
					name: 'interfaceType',
					label: _('Interface type'),
					type: ComboBox,
					value: 'eth', // FIXME: if eth is not possible use vlan
					onChange: lang.hitch(this, function(interfaceType) {
						if (interfaceType) {
							var name = (interfaceType !== 'vlan' ? interfaceType : 'eth');
							var num = 0;
							while(array.some(array.map(this.get('value'), function(item) { return item['interface']; }), function(iface) { return iface == name + String(num); })) {
								num++;
							}
							form.getWidget('interface').set('interface', name + String(num));
						}
					}),
					dynamicValues: hack.foo
				}, {
					name: 'interface',
					label: _('Interface'),
					type: ComboBox,
					depends: ['interfaceType'],
					dynamicValues: lang.hitch(this, function() {
						var interfaceType = form.getWidget('interfaceType').get('value');
						if (interfaceType === 'eth') {
							var available = this.get('value');
							return array.filter(this.physical_interfaces, function(_iface) { return array.every(available, function(item) { return item['interface'] !== _iface; }); });
						} else if (interfaceType === 'vlan') {
							return this.physical_interfaces;
						} else if(interfaceType === 'br' || interfaceType === 'bond' ) {
							var num = 0;
							while(array.some(array.map(this.get('value'), function(item) { return item['interface']; }), function(_iface) { return _iface == interfaceType + String(num); })) {
								num++;
							}
							return [ interfaceType + String(num) ];
						}
					})
//					type: TextBox,
/*					validator: lang.hitch(this, function(value) {
						if(!form) { return true; }
						var interfaceType = form.getWidget('interfaceType').get('value');
						var name = (interfaceType !== 'vlan' ? interfaceType : 'eth');
						if (interfaceType === 'eth' && !array.some(this.physical_interfaces, function(iface) { return iface === value; })) {
							dialog.alert(_('The interface must be one of the physical interfaces: ') + this.physical_interfaces.join(', '));
							return false;
						} else if(interfaceType === 'bond' && 2 > this.physical_interfaces.length) {
							dialog.alert(_('There must be at least two physical interfaces to use a bonding interface'));
							return false;
						}
						return new RegExp('^' + name + '[0-9]+$').test(value);
					})
*/				}],
//				layout: [{
//					label: _('Select an interface type'),
//					layout: ['interfaceType', 'interface']
//				}],
				layout: ['interfaceType', 'interface']
			});

			dialog.confirmForm({
				form: form,
				title: _('Select an interface type'),
				submit: _('Add interface')
			}).then(lang.hitch(this, function(formvals) {
				props = lang.mixin({create: true}, props, formvals);
				this._showWizard(props);
			}));
		},

		_showWizard: function(props) {
			var _dialog = null, wizard = null;

			var _cleanup = function() {
				_dialog.hide();
				_dialog.destroyRecursive();
			};

			var _finished = lang.hitch(this, function(values) {
				this.updateValues(values, props.create);
				_cleanup();
			});
	
			var propvals = {
				values: props,
				'interface': props['interface'],
				interfaceType: props.interfaceType,
				physical_interfaces: this.physical_interfaces,
				available_interfaces: this.get('value'),
				create: props.create,
				onCancel: _cleanup,
				onFinished: _finished
			};
			wizard = new InterfaceWizard(propvals);

			_dialog = new Dialog({
				title: props.create ? _('Add a network interface') : _('Edit a network interface'),
				content: wizard
			});
			_dialog.own(wizard);
			this.own(_dialog);
			_dialog.show();
		},

		_removeInterface: function(ids) {
			array.forEach(ids, function(iid) {
				var item = this.moduleStore.get(iid);
				if (item.interfaceType === 'bond' || item.interfaceType === 'br') {
					// enable the interfaces which were blocked by this interface
					var key = item.interfaceType === 'bond' ? 'bond-slaves' : 'bridge_ports';
					this.setDisabledItem(item[key], false);
					// re set original values
					array.forEach(item[key], lang.hitch(this, function(key) {
						var item = this.moduleStore.get(key);
						if (item.original) {
							this.moduleStore.put(item.original);
						}
					}));
				}

				this.moduleStore.remove(iid);
			}, this);
			this.onChanged();
		}

	});
});
