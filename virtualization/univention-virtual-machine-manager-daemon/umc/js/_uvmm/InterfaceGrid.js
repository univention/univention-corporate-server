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

dojo.provide("umc.modules._uvmm.InterfaceGrid");

dojo.require("dijit.Dialog");

dojo.require("umc.tools");
dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Form");
dojo.require("umc.modules._uvmm.InterfaceWizard");

dojo.declare("umc.modules._uvmm.InterfaceGrid", [ umc.widgets.Grid, umc.i18n.Mixin ], {
	moduleStore: null,

	domain: null,

	i18nClass: 'umc.modules.uvmm',

	query: {},

	sortIndex: null,

	style: 'width: 100%; height: 200px;',

	constructor: function() {
		dojo.mixin(this, {
			columns: [{
				name: 'type',
				label: this._('Type')
			}, {
				name: 'source',
				label: this._('Source')
			}, {
				name: 'model',
				label: this._('Driver'),
				formatter: dojo.hitch(this, function(model) {
					return umc.modules._uvmm.types.interfaceModels[model] || this._('unknown');
				})
			}, {
				name: 'mac_address',
				label: this._('MAC address'),
				formatter: dojo.hitch(this, function(mac) {
					if (!mac) {
						return this._('automatic');
					}
					return mac;
				})
			}],
			actions: [{
				name: 'edit',
				label: this._('Edit'),
				isMultiAction: false,
				isContextAction: true,
				isStandardAction: true,
				iconClass: 'umcIconEdit',
				callback: dojo.hitch(this, '_editInterface')
			}, {
				name: 'remove',
				label: this._('Remove'),
				isMultiAction: false,
				isStandardAction: true,
				iconClass: 'umcIconDelete',
				callback: dojo.hitch(this, '_removeInterface')
			}, {
				name: 'add',
				label: this._('Add network interface'),
				isMultiAction: false,
				isContextAction: false,
				iconClass: 'umcIconAdd',
				callback: dojo.hitch(this, '_editInterface')
			}]
		});
	},

	_removeInterface: function(ids) {
		var msg = this._('Should the network interface be removed?');
		if (ids.length > 1) {
			msg = this._('Should the %d network interfaces be removed?', ids.length);
		}
		umc.dialog.confirm(msg, [{
			name: 'remove',
			label: this._('Remove')
		}, {
			name: 'cancel',
			'default': true,
			label: this._('Cancel')
		}]).then(dojo.hitch(this, function(response) {
			if (response == 'cancel') {
				return;
			}

			dojo.forEach(ids, function(iid) {
				this.moduleStore.remove(iid);
			}, this);
		}));
	},

	_editInterface: function(ids, items) {
		if (ids.length > 1) {
			// should not happen
			return;
		}
		var id = ids.length ? ids[0] : null;
		var item = items.length ? items[0] : {};

		var dialog = null, wizard = null;

		var _cleanup = function() {
			dialog.hide();
			dialog.destroyRecursive();
			wizard.destroyRecursive();
		};

		var _finished = dojo.hitch(this, function(values) {
			if (id !== null) {
				// replace existing id
				this.moduleStore.put(dojo.mixin({
					$id$: id
				}, values));
			}
			else {
				// generate a new pseudo ID
				id = this.moduleStore.data.length + 1;

				// add the new interface to the store
				this.moduleStore.add(dojo.mixin({
					$id$: id
				}, values));
			}
			_cleanup();
		});

		wizard = new umc.modules._uvmm.InterfaceWizard({
			style: 'width: 500px; height:510px;',
			domain_type: this.domain.domain_type,
			values: item || {},
			onFinished: _finished,
			onCancel: _cleanup
		});
		dialog = new dijit.Dialog({
			title: this._('Add network interface'),
			content: wizard
		});
		dialog.show();
		
	},

	filter: function() {
		this.inherited(arguments, [{}]);
	},

	onUpdateProgress: function(i, n) {
		// event stub
	}
});
