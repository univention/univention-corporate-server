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
/*global define console setTimeout*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dijit/Dialog",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Grid",
	"umc/widgets/Form",
	"umc/widgets/_FormWidgetMixin",
	"umc/widgets/ComboBox",
	"umc/modules/setup/InterfaceWizard",
	"umc/modules/setup/types",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, on, Memory, Observable, Dialog, dialog, tools, Grid, Form, _FormWidgetMixin, ComboBox, InterfaceWizard, types, _) {
	return declare("umc.modules.setup.InterfaceGrid", [ Grid, _FormWidgetMixin ], {
		moduleStore: null,

		style: 'width: 100%; height: 230px;',
		query: {},
		sortIndex: null,

		physical_interfaces: [],

		gateway: "",
		nameserver: [],
		'interfaces/primary': null,

		constructor: function() {
			this.moduleStore = new Observable(new Memory({idProperty: 'interface'}));

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
					name: 'configuration',
					label: _('Configuration'),
					formatter: lang.hitch(this, function(__nothing__, row, scope) {
						var iface = this.getRowValues(row);
						var back = '';

						if (((iface.interfaceType === 'eth' || iface.interfaceType === 'vlan') && iface.type !== 'manual') || (iface.interfaceType === 'bond' || iface.interfaceType === 'br')) {
							// display IP addresses
							var formatIPs = function(ips) {
								return array.map(array.filter(ips, function(i) { return i[0] && i[1]; }), function(i) { return i[0] + '/' + types.convertNetmask(i[1]);});
							};
							var ip4s = formatIPs(iface.ip4);
							var ip6s = formatIPs(iface.ip6);

							if (iface.ip4dynamic) {
								back += _('Dynamic (DHCP)') + '<br>';
							}
							if (iface.ip6dynamic) {
								back += _('Autoconfiguration (SLAAC)') + '<br>';
							}

							if (ip4s.length && !iface.ip4dynamic){
								back += _('Static') + ': ';
								back += ip4s.join(', ');
								if (ip6s.length && !iface.ip6dynamic) {
									back += '<br>';
								}
							}
							if (ip6s.length && !iface.ip6dynamic) {
								back += _('Static (IPv6)') + ': ';
								back += ip6s.join(', ');
							}
						}

						if (iface.interfaceType === 'br') {
							back += '<br>' + _('Bridge ports') + ': ' + iface['bridge_ports'].join(', ');
						} else if(iface.interfaceType === 'bond') {
							back += '<br>' + _('Bonding primaries') + ': ' + iface['bond-primary'].join(', ');
							// TODO: also show slaves?
						}

						return back;
					}),
					width: '70%'
				}],
				actions: [{
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

		_getValueAttr: function() { return this.moduleStore.query(); },

		_setValueAttr: function(values) {
			// empty the grid
			this.moduleStore.setData([]);
			this.moduleStore.query().observe(lang.hitch(this, '_consistence'), true);

			// FIXME: the consistence check depends on other interfaces, we have to insert all interfaces and trigger than for every interface the notification
			// we need to fix this when supporting bridges, vlans and bondings

			// set new values
			tools.forIn(values, function(id, value) {
				this.moduleStore.add(lang.mixin({'interface': id}, value));
			}, this);

			this._set('value', this.get('value'));
		},

		onChange: function() {
			// event stub
		},

		_consistence: function(iface, removedFrom, insertedInto) {
			var create = removedFrom === -1;
			var deleted = insertedInto === -1;
			var key;

			// update disabled items when grid update is through
			on.once(this, 'filterDone', lang.hitch(this, function() {
				var disabledIDs = [];
				this.moduleStore.query().forEach(lang.hitch(this, function(iiface) {
					// disable all bond, bridge and vlan interfaces
					if (iiface.interfaceType !== 'eth') {
						disabledIDs.push(iiface['interface']);
					}
				}));
				this.setDisabledItem(disabledIDs, true);
			}));

			if (!deleted) {
				iface.primary = iface['interface'] === this['interfaces/primary'];
				// TODO: insert
			}
			return;

			if (!deleted) {

				if (iface.interfaceType === 'vlan') {
					// build the interface name from interface "." vlan_id
					var ifacename = iface['interface'];
					iface['interface'] = iface['interface'].split('.', 1) + '.' + String(iface.vlan_id);
					if (ifacename !== iface['interface']) {
						// if the interface id was renamed the identifier changed... so delete the old row
						setTimeout(lang.hitch(this, function() { this.moduleStore.remove(ifacename); }), 0);
					}
				}

				if (iface.interfaceType === 'bond' || iface.interfaceType === 'br') {
					iface.start = true;

					// disable the interfaces which are used by this interface
					key = iface.interfaceType === 'bond' ? 'bond-slaves' : 'bridge_ports';
					this.setDisabledItem(iface[key], true);

					// set original iface
					array.forEach(iface[key], lang.hitch(this, function(ikey) {
						var iiface = this.moduleStore.get(ikey);
						if (iiface === undefined) {
							// the interface is not configured in the grid but exists as physical interface
							return;
						}
						var filtered = {}; tools.forIn(iiface, function(k, v) { if (array.indexOf(k, "_") !== 0) { filtered[k] = v; } });
						iiface.original = lang.clone(filtered);

						iiface.type = 'manual';
						iiface.start = false;
						setTimeout(lang.hitch(this, function() {
							// FIXME: put does not work
							//this.moduleStore.put(iiface);
							this.moduleStore.remove(iiface['interface']);
							this.moduleStore.add(iiface);
						}), 0);
					}));
				}

				if (deleted) {
					if (iface['interface'] === this['interfaces/primary']) {
						this.set('interfaces/primary', '');
					}
					if (iface.interfaceType === 'bond' || iface.interfaceType === 'br') {
						// enable the interfaces which were blocked by this interface
						key = iface.interfaceType === 'bond' ? 'bond-slaves' : 'bridge_ports';

						// enable the blocked devices
						this.setDisabledItem(iface[key], false);

						// re set original values
						array.forEach(iface[key], lang.hitch(this, function(ikey) {
							var iiface = this.moduleStore.get(ikey);
							if (iiface === undefined) {
								return; // the interface is not configured in the grid
							}
							if (iiface.original) {
								setTimeout(lang.hitch(this, function() { this.moduleStore.put(iiface.original); }), 0);
							}
						}));
					}
				}
			}
			this._set('value', this.get('value'));
		},

		updateInterface: function(iface) {
			// set gateway if got from DHCP request
			iface.gateway && this.set('gateway', iface.gateway);
			// set nameservers if got from DHCP request
			iface.nameserver && iface.nameserver.length && this.set('nameserver', iface.nameserver);
			// set this interface as primary interface if it was selected
			if (iface.primary) {
				this.set('interfaces/primary', iface['interface']);
			} else {
				this.set('interfaces/primary', '');
			}

			// delete values which does not belong to the interface data in the grid
			var update = !iface.create;
			delete iface.create;
			delete iface.gateway;
			delete iface.nameserver;

			if (update) {
				var filtered = {}; tools.forIn(iface, function(k, v) { if (array.indexOf(k, "_") !== 0) { filtered[k] = v; } }); iface = filtered; // don't use the reference
				//this.moduleStore.put( iface ); // FIXME: put does not work
				this.moduleStore.remove(iface['interface']);
				this.moduleStore.add( iface );
			} else {
				try {
					this.moduleStore.add( iface );
				} catch(error) {
					// TODO: this happened when renaming an vlan interface but is fixed. can we remove it?
					console.log(error);
					dialog.alert(_('Interface "%s" already exists', iface['interface']));
				}
			}
		},

		_addInterface: function() {
			// --------don't support vlan, br, bond----------
			if (!array.some(this.physical_interfaces, lang.hitch(this, function(iface) { return -1 === array.indexOf(array.map(array.filter(this.get('value'), function(item) { return item.interfaceType === 'eth';}), function(iiface) { return iiface['interface']; }), iface); }))) {
				dialog.alert(_('There are no interfaces to configure'));
				return;
			}
			//------------
			// grid action
			this._modifyInterface({});
		},

		_editInterface: function(name, props) {
			// --------don't support vlan, br, bond----------
			if (this.moduleStore.get(props[0]).interfaceType !== 'eth') {
				dialog.alert('Currently only ethernet interfaces can be modified.');
				return;
			}
			// ------
			// grid action
			return this._modifyInterface(props[0]);
		},

		_modifyInterface: function(props) {
			// ---------- no bridge, bond, vlan support
			props.create = !props.interfaceType;
			if (!props.interfaceType) { props.interfaceType = 'eth'; }
			this._showWizard(props);
			return;
			// -----------

			// Add or modify an interface
			if (props.interfaceType) {
				// only edit the existing interface
				props.create = false;
				this._showWizard(props);
				return;
			}

			var form; form = new Form({
				widgets: [{
					name: 'interfaceType',
					label: _('Interface type'),
					type: ComboBox,
					sortDynamicValues: false,
					onChange: lang.hitch(this, function(interfaceType) {
						// recalculate the possible device number
						if (interfaceType) {
							var name = (interfaceType !== 'vlan' ? interfaceType : 'eth');
							var num = 0;
							while(array.some(array.map(this.get('value'), function(item) { return item['interface']; }), function(iface) { return iface == name + String(num); })) {
								num++;
							}
							form.getWidget('interface').set('interface', name + String(num));
						}
					}),
					dynamicValues: lang.hitch(this, function() {
						// TODO: lookup if interfaces are already in use
						
						var arr = types.interfaceValues();
						if (this.physical_interfaces.length < 2) {
							// we can not use a bonding interface if we don't have at least two physical interfaces
							arr = array.filter(arr, function(i) { return i.id !== 'bond'; });
						}
						if (array.every(this.physical_interfaces, lang.hitch(this, function(iface) {
							var ifaces = this.get('value');
							return ifaces.length !== 0 ? array.some(ifaces, function(val) { return iface === val['interface']; }) : false;
						}))) {
							// if all physical interfaces are configured we can not configure another one
							arr = array.filter(arr, function(i) { return i.id !== 'eth'; });
						}
						return arr;
					})
				}, {
					name: 'interface',
					label: _('Interface'),
					type: ComboBox,
					depends: ['interfaceType'],
					dynamicValues: lang.hitch(this, function(deps) {
						var interfaceType = deps.interfaceType;

						if (interfaceType === 'eth') {
							// return all available physical interfaces which are not already in the grid
							var available = this.get('value');
							return array.filter(this.physical_interfaces, function(_iface) { return array.every(available, function(item) { return item['interface'] !== _iface; }); });
						} else if (interfaceType === 'vlan') {
							// return all interfaces which are not vlans
//							// FIXME: if the physical interface is not defined in the grid this could lead to errors
//							return this.physical_interfaces.concat(array.filter(this.get('value'), function(item) { return item.interfaceType !== 'vlan'; }));
							return array.map(array.filter(this.get('value'), function(item) { return item.interfaceType !== 'vlan'; }), function(item) { return item['interface']; });
						} else if(interfaceType === 'br' || interfaceType === 'bond' ) {
							// get the next possible device
							var num = 0;
							while(array.some(array.map(this.get('value'), function(item) { return item['interface']; }), function(_iface) { return _iface == interfaceType + String(num); })) {
								num++;
							}
							return [ interfaceType + String(num) ];
						}
					})//,
					// FIXME: allow to add various device names for bondings, etc., but we have to restrict eth names to the physical interface names (which is in the logic from dynamicValues)
//					validate: function(value) {
//						if (form._widgets.interfaceType.get('value') !== 'eth') {
//							// every interface name is valid
//							return /^[a-z]+[0-9]+$/.test(value);
//						}
//						return form._widgets.interfaceType.__proto__.validator(value);
//					}
				}],
				layout: ['interfaceType', 'interface']
			});

			dialog.confirmForm({
				form: form,
				title: _('Select an interface type'),
				submit: _('Add interface')
			}).then(lang.hitch(this, function(formvals) {
				this._showWizard(lang.mixin({create: true}, props, formvals));
			}));
		},

		_showWizard: function(props) {
			// show an InterfaceWizard for the given props
			// and insert data into the grid when saving the new values
			var _dialog = null, wizard = null;

			var _cleanup = function() {
				_dialog.hide();
				_dialog.destroyRecursive();
			};

			var _finished = lang.hitch(this, function(values) {
				this.updateInterface(values);
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
			// grid action
			// remove the interfaces from grid
			array.forEach(ids, function(iid) {
				this.moduleStore.remove(iid);
			}, this);
			this._set('value', this.get('value'));
		}

	});
});
