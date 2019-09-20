/*
 * Copyright 2012-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define,console,setTimeout*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dijit/Dialog",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Grid",
	"umc/widgets/_FormWidgetMixin",
	"umc/modules/setup/InterfaceWizard",
	"umc/modules/setup/Interfaces",
	"umc/modules/setup/types",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, Memory, Observable, Dialog, dialog, tools, Grid, _FormWidgetMixin, InterfaceWizard, Interfaces, types, _) {
	return declare("umc.modules.setup.InterfaceGrid", [ Grid, _FormWidgetMixin ], {
		moduleStore: null,

		query: {},
		sortIndex: 1,

		gateway: "",
		nameserver: [],

		constructor: function() {
			this.moduleStore = new Observable(new Interfaces({idProperty: 'name'}));

			lang.mixin(this, {
				columns: [{
					name: 'name',
					label: _('Network interface'),
					width: '18%'
				}, {
					name: 'interfaceType',
					label: _('Type'),
					width: '15%',
					formatter: function(value) {
						return types.interfaceTypeLabels[value] || value;
					}
				}, {
					name: 'configuration',
					label: _('Configuration'),
					formatter: lang.hitch(this, function(val, row, scope) {
						var iface = this.getRowValues(row);
						return this.moduleStore.getInterface(iface.name).getConfigurationDescription();
					}),
					width: '67%'
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
					label: _('Add'),
					iconClass: 'umcIconAdd',
					isContextAction: false,
					callback: lang.hitch(this, '_addInterface')
				}, {
					name: 'delete',
					label: _('Delete'),
					iconClass: 'umcIconDelete',
					isMultiAction: true,
					isStandardAction: true,
					callback: lang.hitch(this, function(ids, items) {
						
						var unremoveableInterfaces = [];
						var removeableInterfaceIDs = [];
						array.forEach(items, lang.hitch(this, function(item) {
							if (!item.isVLAN()) {
								// interface is not removable if used as parent device in a VLAN
								var deletable = array.every(this.get('value'), function(iface) {
									if (!iface.isVLAN()) {
										// we do not have to check here because items != VLAN are disabled if used
										return true;
									}
									if (item.name !== iface.parent_device) {
										return true;
									}
									// if every subdevice will be deleted item is removable
									return ids.indexOf(iface.name) !== -1;
								});

								if (!deletable) {
									unremoveableInterfaces.push(item.name);
								} else {
									removeableInterfaceIDs.push(item.name);
								}
							} else {
								removeableInterfaceIDs.push(item.name);
							}
						}));

						var buttons = [{
							label: _('Cancel'),
							'default': true
						}, {
							// will be removed near line 142!
							label: _('Delete'),
							callback: lang.hitch(this, '_removeInterfaces', removeableInterfaceIDs)
						}];

						var msg = _('Please confirm to delete the following interfaces:');
						msg += '<ul><li>' + removeableInterfaceIDs.join('</li><li>') + '</li></ul>';

						if (unremoveableInterfaces.length) {
							var _msg = _('The following interfaces are already used by other interfaces and can not be deleted:');
							_msg += '<ul><li>' + unremoveableInterfaces.join('</li><li>') + '</li></ul>';

							if (ids.length <= unremoveableInterfaces.length) {
								// remove the delete button
								msg = _msg;
								buttons.pop();
							} else {
								msg = _msg + msg;
							}
						}

						dialog.confirm(msg, buttons);
					})
				}]
			});

			tools.ucr(['version/version']).then(lang.hitch(this, function(data) {
				this.ucsversion = data['version/version'];
			}));

		},

		_getValueAttr: function() {
			return this.moduleStore.query();
		},

		_setValueAttr: function(values) {
			// empty the grid
			var data = [];

			// set new values
			tools.forIn(values, function(iname, iface) {
				data.push(this.moduleStore.createDevice(iface));
			}, this);

			this.moduleStore.setData(data);

			this._cachedInterfaces = {};

			this._ready = false;
			array.forEach(this.moduleStore.query(), lang.hitch(this, function(iface) {
				this._consistence(iface, -1, 0);
			}));
			this._ready = true;
			this._disableUsedInterfaces();

			this.moduleStore.query().observe(lang.hitch(this, function(iface, removedFrom, insertedInto) {
				this._consistence(iface, removedFrom, insertedInto);
				setTimeout(lang.hitch(this, '_disableUsedInterfaces'), 250);
			}), true);

			setTimeout(lang.hitch(this._grid, '_refresh'), 0);

			this._set('value', this.get('value'));
		},

		_disableUsedInterfaces: function() {
			var to_disable = {};

			var items = this.get('value');
			array.forEach(items, function(iface) {
				if (!iface.isVLAN()) {
					array.forEach(iface.getSubdeviceNames(), function(name) {
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
			var deleted = insertedInto === -1;
			iface = this.moduleStore.createDevice(iface);

			if (!deleted) {

				if (iface.isBond() || iface.isBridge()) {
					// store original subdevices
					array.forEach(iface.getSubdeviceNames(), lang.hitch(this, function(ikey) {
						var iiface = this.moduleStore.getInterface(ikey);
						if (iiface === undefined) {
							// the interface is not configured in the grid but exists as physical interface
							this.moduleStore.put(this.moduleStore.createDevice({name: ikey, interfaceType: 'Ethernet'}));
							return;
						}
						this._cachedInterfaces[iiface.name] = this.moduleStore.createDevice(iiface);

						if (this._ready) {
							iiface.ip4 = [];
							iiface.ip6 = [];
							iiface.ip4dynamic = false;
							iiface.ip6dynamic = false;
							setTimeout(lang.hitch(this, function() {
								this.moduleStore.put(iiface);
							}), 0);
						}
					}));
				}
			} else {

				// restore original values
				array.forEach(iface.getSubdeviceNames(), lang.hitch(this, function(ikey) {
					var iiface = this.moduleStore.getInterface(ikey);
					if (iiface === undefined) {
						return; // the interface is not configured in the grid
					}
					if (this._cachedInterfaces[iiface.name]) {
						setTimeout(lang.hitch(this, function() {
							this.moduleStore.put(this._cachedInterfaces[iiface.name]);
						}), 0);
					}
				}));
			}

			this._set('value', this.get('value'));
		},

		updateInterface: function(data) {
			var iface = this.moduleStore.createDevice(data.values);

			// set gateway if got from DHCP request
			if (data.gateway) {
				this.set('gateway', data.gateway);
			}

			// set nameservers if got from DHCP request
			if (data.nameserver && data.nameserver.length) {
				this.set('nameserver', data.nameserver);
			}

			var renamed = false;
			if (!data.creation) {
				renamed = iface.name != data.original_name;
				if (!renamed) {
					this.moduleStore.put(iface);
					return;
				}
			}
			try {
				this.moduleStore.add(iface);
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
			this._showWizard(devices[0]);
		},

		_addInterface: function() {
			var possibleTypes = this.moduleStore.getPossibleTypes(null);
			if (!possibleTypes.length) {
				dialog.alert(_('There are no more physical interfaces to create.'));
				return;
			}

			// grid action
			this._showWizard(null);
		},

		_removeInterfaces: function(ids) {
			// grid action
			array.forEach(ids, function(iid) {
				this.moduleStore.remove(iid);
			}, this);
			this._set('value', this.get('value'));
		},

		_showWizard: function(device) {
			// show an InterfaceWizard for the given device
			// and insert data into the grid when saving the new values
			var wizard;
			var _cleanup = lang.hitch(this, function() {
				this.selectPage(null);
				this.removePage(wizard);
				wizard.destroyRecursive();
			});

			var _finished = lang.hitch(this, function(values) {
				var data = {};
				data.gateway = values.gateway;
				data.nameserver = values.nameserver;
				data.creation = values.creation;
				data.values = values;
				data.original_name = values.original_name;
				this.updateInterface(data);
				_cleanup();
			});

			wizard = new InterfaceWizard({
				interfaces: this.moduleStore,
				ucsversion: this.ucsversion,
				device: device,
				onCancel: _cleanup,
				headerButtons: [{
					name: 'close',
					label: _('Back to overview'),
					iconClass: 'umcCloseIconWhite',
					callback: _cleanup
				}],
				onFinished: _finished
			});

			this.own(wizard);
			this.addPage(wizard);
			this.selectPage(wizard);

			//	device ? _('Edit a network interface') : _('Add a network interface'),
		},

		onChange: function() {
			// event stub
		}
	});
});
