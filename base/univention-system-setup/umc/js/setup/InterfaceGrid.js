/*
 * Copyright 2012-2013 Univention GmbH
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
	"umc/widgets/_FormWidgetMixin",
	"umc/modules/setup/InterfaceWizard",
	"umc/modules/setup/types",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, on, Memory, Observable, Dialog, dialog, tools, Grid, _FormWidgetMixin, InterfaceWizard, types, _) {
	return declare("umc.modules.setup.InterfaceGrid", [ Grid, _FormWidgetMixin ], {
		moduleStore: null,

		style: 'width: 100%; height: 350px;',
		query: {},
		sortIndex: null,

		physical_interfaces: [],

		gateway: "",
		nameserver: [],
		'interfaces/primary': null,

		constructor: function() {
			this.moduleStore = new Observable(new Memory({idProperty: 'name'}));

			lang.mixin(this, {
				columns: [{
					name: 'name',
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
					formatter: lang.hitch(this, function(val, row, scope) {
						var iface = this.getRowValues(row);
						return this.getItem(iface.name).getConfigurationDescription();
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
					callback: lang.hitch(this, '_editInterfaces')
				}, {
					name: 'add',
					label: _('Add device'),
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
							callback: lang.hitch(this, '_removeInterfaces', ids)
						}, {
							label: _('Cancel'),
							'default': true
						}]);
					}),
					canExecute: lang.hitch(this, function(item) {
						if (!item.isVLAN()) {
							// interface is not removeable if used as parent device in a VLAN
							return array.every(this.get('value'), function(iface) {
								return !iface.isVLAN() || item.name !== iface.parent_device;
							});
						}
						return true;
					})
				}]
			});
		},

		_getValueAttr: function() {
			return this.moduleStore.query();
		},

		_setValueAttr: function(values) {
			// empty the grid
			var data = [];

			// set new values
			tools.forIn(values, function(id, value) {
				data.push(value);
			}, this);

			this.moduleStore.setData(data);

			this._cachedInterfaces = {};

			array.forEach(this.moduleStore.query(), lang.hitch(this, function(iface) {
				this._consistence(iface, -1, 0);
			}));

			this.moduleStore.query().observe(lang.hitch(this, '_consistence'), true);

			setTimeout(lang.hitch(this._grid, '_refresh'), 0);

			this._set('value', this.get('value'));
		},

		disableUsedInterfaces: function() {
			var to_disable = {};

			var items = array.filter(this.getAllItems(), function(item) { return item !== null; });
			array.forEach(items, function(iface) {
				if (!iface.isVLAN()) {
					array.forEach(iface.getSubdevices(), function(name) {
						to_disable[name] = true;
					});
				}
			});

			array.forEach(items, lang.hitch(this, function(iface) {
				// enable and disable all items
				this.setDisabledItem(iface.name, true === to_disable[iface.name]);
			}));
		},

		_consistence: function(iface, removedFrom, insertedInto) {
			var create = removedFrom === -1;
			var deleted = insertedInto === -1;
			var key;

			if (!deleted) {

				if (iface.isBond() || iface.isBridge()) {
					// store original subdevices
					array.forEach(iface.getSubdevices(), lang.hitch(this, function(ikey) {
						var iiface = this.moduleStore.get(ikey);
						if (iiface === undefined) {
							// the interface is not configured in the grid but exists as physical interface
							return;
						}
						var filtered = {}; tools.forIn(iiface, function(k, v) { if (array.indexOf(k, "_") !== 0) { filtered[k] = v; } });
						this._cachedInterfaces[iiface.name] = lang.clone(filtered);
					}));
				}
			} else {

				if (iface.name === this['interfaces/primary']) {
					this.set('interfaces/primary', '');
				}

				// restore original values
				array.forEach(iface.getSubdevices(), lang.hitch(this, function(ikey) {
					var iiface = this.moduleStore.get(ikey);
					if (iiface === undefined) {
						return; // the interface is not configured in the grid
					}
					if (this._cachedInterfaces[iiface.name]) {
						setTimeout(lang.hitch(this, function() {
							this.moduleStore.put(types.getDevice(this._cachedInterfaces[iiface.name]));
						}), 0);
					}
				}));
			}

			on.once(this, 'filterDone', lang.hitch(this, 'disableUsedInterfaces'));

			this._set('value', this.get('value'));
		},

		updateInterface: function(data) {
			var iface = data.device;

			// set gateway if got from DHCP request
			if (data.gateway) {
				this.set('gateway', data.gateway);
			}

			// set nameservers if got from DHCP request
			if (data.nameserver && data.nameserver.length) {
				this.set('nameserver', data.nameserver);
			}

			// set or remove interfaces/primary if device was (de)selected as primary
			if (iface.primary) {
				this.set('interfaces/primary', iface.name);
			} else if (this.get('interfaces/primary') === iface.name) {
				this.set('interfaces/primary', '');
			}

			var renamed = false;
			if (!data.creation) {
				renamed = iface.name != data.original_name;
				if (!renamed) {
					//this.moduleStore.put( iface ); // FIXME: put does not work
					this.moduleStore.remove(iface.name);
					this.moduleStore.add( iface );
					return;
				}
			}
			try {
				this.moduleStore.add( iface );
			} catch(error) {
				console.log(error);
				dialog.alert(_('Interface "%s" already exists.', iface.name));
				return;
			}

			if (renamed) {
				// remove old interface after the new has been added
				setTimeout(lang.hitch(this, function() { this.moduleStore.remove(data.original_name); }), 0);
			}
		},

		_editInterfaces: function(name, devices) {
			// grid action
			this._showWizard({device: devices[0], creation: false});
		},

		_addInterface: function() {
			// grid action
			this._showWizard({device: { interfaceType: 'Ethernet', name: ''}, creation: true});
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
				var data = {};
				data.gateway = values.gateway;
				data.nameserver = values.nameserver;
				data.creation = values.creation;
				data.device = types.getDevice(values);
				data.original_name = values.original_name;
				this.updateInterface(data);
				_cleanup();
			});
	
			var propvals = {
				original_name: props.device.name,
				device: types.getDevice(props.device),
				name: props.device.name,
				interfaceType: props.device.interfaceType,
				physical_interfaces: this.physical_interfaces,
				available_interfaces: this.get('value'),
				creation: props.creation,
				onCancel: _cleanup,
				onFinished: _finished
			};
			wizard = new InterfaceWizard(propvals);

			_dialog = new Dialog({
				title: props.creation ? _('Add a network device') : _('Edit a network device'),
				content: wizard
			});
			_dialog.own(wizard);
			this.own(_dialog);
			_dialog.show();
		},

		_removeInterfaces: function(ids) {
			// grid action
			// remove the interfaces from grid
			array.forEach(ids, function(iid) {
				this.moduleStore.remove(iid);
			}, this);
			this._set('value', this.get('value'));
		},

		onChange: function() {
			// event stub
		}
	});
});
