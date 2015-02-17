/*
 * Copyright 2011-2015 Univention GmbH
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
	"umc/widgets/Grid",
	"umc/modules/uvmm/InterfaceWizard",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, Dialog, dialog, Grid, InterfaceWizard, types, _) {

	return declare("umc.modules.uvmm.InterfaceGrid", [ Grid ], {
		moduleStore: null,

		domain: null,

		query: {},

		sortIndex: null,

		style: 'width: 100%; height: 200px;',

		constructor: function() {
			lang.mixin(this, {
				cacheRowWidgets: false,
				columns: [{
					name: 'type',
					label: _('Type'),
					formatter: lang.hitch(this, function(type) {
						var label = _('unknown');
						array.some( types.interfaceTypes, function( itype ) {
							if ( itype.id == type ) {
								label = itype.label;
								return false;
							}
						} );
						return label;
					})
				}, {
					name: 'source',
					label: _('Source')
				}, {
					name: 'model',
					label: _('Driver'),
					formatter: lang.hitch(this, function(model) {
						return types.interfaceModels[model] || _('unknown');
					})
				}, {
					name: 'mac_address',
					label: _('MAC address'),
					formatter: lang.hitch(this, function(mac) {
						if (!mac) {
							return _('automatic');
						}
						return mac;
					})
				}],
				actions: [{
					name: 'edit',
					label: _('Edit'),
					isMultiAction: false,
					isContextAction: true,
					isStandardAction: true,
					iconClass: 'umcIconEdit',
					callback: lang.hitch(this, '_editInterface'),
					canExecute: lang.hitch(this, function(item) {
						// when creating an machine drives can not be edited
						return !this.disabled && undefined !== this.domain.domainURI;
					} )
				}, {
					name: 'remove',
					label: _('Remove'),
					isMultiAction: false,
					isStandardAction: true,
					iconClass: 'umcIconDelete',
					callback: lang.hitch(this, '_removeInterface'),
					canExecute: lang.hitch(this, function(item) {
						return !this.disabled && undefined !== this.domain.domainURI;
					})
				}, {
					name: 'add',
					label: _('Add network interface'),
					isMultiAction: false,
					isContextAction: false,
					iconClass: 'umcIconAdd',
					callback: lang.hitch(this, '_editInterface')
				}]
			});
		},

		_removeInterface: function(ids) {
			var msg = _('Should the network interface be removed?');
			if (ids.length > 1) {
				msg = _('Should the %d network interfaces be removed?', ids.length);
			}
			dialog.confirm(msg, [{
				name: 'remove',
				label: _('Remove')
			}, {
				name: 'cancel',
				'default': true,
				label: _('Cancel')
			}]).then(lang.hitch(this, function(response) {
				if (response == 'cancel') {
					return;
				}

				array.forEach(ids, function(iid) {
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
			var item = items.length ? items[0] : null;

			var _dialog = null, wizard = null;

			var _cleanup = function() {
				_dialog.hide();
				_dialog.destroyRecursive();
				wizard.destroyRecursive();
			};

			var _finished = lang.hitch(this, function(values) {
				if (id !== null) {
					// replace existing id
					this.moduleStore.put(lang.mixin({
						$id$: id
					}, values));
					this.filter();
				} else {
					// generate a new pseudo ID
					id = this.moduleStore.data.length + 1;

					// add the new interface to the store
					this.moduleStore.add(lang.mixin({
						$id$: id
					}, values));
				}
				_cleanup();
			});

			wizard = new InterfaceWizard({
				style: 'width: 500px; height:510px;',
				onFinished: _finished,
				onCancel: _cleanup
			}, this.domain.domain_type, item);
			_dialog = new Dialog({
				title: item ? _('Edit network interface') : _('Add network interface'),
				content: wizard
			});
			_dialog.show();
		},

		filter: function() {
			this.inherited(arguments, [{}]);
		},

		onUpdateProgress: function(i, n) {
			// event stub
		}
	});
});
