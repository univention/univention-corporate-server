/*
 * Copyright 2013-2019 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/array",
	"dojo/_base/declare",
	"dojo/_base/lang",
	"umc/dialog",
	"umc/store",
	"umc/modules/firewall/DetailDialog",
	"umc/widgets/ComboBox",
	"umc/widgets/Grid",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/SearchForm",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/Tooltip",
	"umc/i18n!umc/modules/firewall"
], function(array, declare, lang, dialog, store, DetailDialog, ComboBox,
            Grid, Module, Page, SearchForm, Text, TextBox, Tooltip, _) {
	return declare("umc.modules.firewall", [Module], {

		moduleStore: null,

		_grid: null,
		_page: null,
		_searchWidget: null,
		_detailDialog: null,

		idProperty: 'identifier',

		postMixInProperties: function() {
			this.inherited(arguments);
			this.moduleStore = store(this.idProperty, this.moduleID + '/rules');
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._page = new Page({
				headerText: _('Firewall'),
				headerText: _('List of rules')
			});
			this.addChild(this._page);

			var actions = [{
				name: 'add',
				label: _('Add'),
				iconClass: 'umcIconAdd',
				isContextAction: false,
				callback: lang.hitch(this, function() {
					this._detailDialog.newRule();
				})
			}, {
				name: 'edit',
				label: _('Edit'),
				iconClass: 'umcIconEdit',
				isStandardAction: true,
				callback: lang.hitch(this, function(ids) {
					this._detailDialog.editRule(ids[0]);
				})
			}, {
				name: 'delete',
				label: _('Delete'),
				iconClass: 'umcIconDelete',
				isStandardAction: true,
				isMultiAction: true,
				callback: lang.hitch(this, 'deleteRules')
			}];

			var columns = [{
				name: 'address',
				label: _('Local address'),
				width: 'auto',
				formatter: lang.hitch(this, '_descriptionTooltip')
			}, {
				name: 'portStart',
				label: _('Port'),
				width: '100px',
				formatter: lang.hitch(this, '_portFormatter')
			}, {
				name: 'protocol',
				label: _('Protocol'),
				width: '50px',
				formatter: function(item) {
					return item.toUpperCase();
				}
			}, {
				name: 'action',
				label: _('Action'),
				width: '75px',
				formatter: function(item) {
					return item.toUpperCase();
				}
			}, {
				name: 'packageName',
				label: _('Package'),
				width: '175px'
			}];

			this._grid = new Grid({
				region: 'main',
				actions: actions,
				columns: columns,
				sortIndex: 2,
				moduleStore: this.moduleStore,
				query: {
					pattern: '*'
				}
			});
			this._page.addChild(this._grid);

			var widgets = [{
				type: ComboBox,
				name: 'category',
				value: 'port',
				label: _('Category'),
				staticValues: [
					{id: 'address', label: _('Local address')},
					{id: 'port', label: _('Port')},
					{id: 'protocol', label: _('Protocol')},
					{id: 'action', label: _('Action')},
					{id: 'packageName', label: _('Package')},
					{id: 'description', label: _('Description')}
				]
			}, {
				type: TextBox,
				name: 'pattern',
				value: '*',
				label: _('Keyword')
			}];

			this._searchWidget = new SearchForm({
				region: 'nav',
				widgets: widgets,
				layout: [['category', 'pattern', 'submit']],
				onSearch: lang.hitch(this._grid, 'filter')
			});

			this._page.addChild(this._searchWidget);

			this._grid.on('FilterDone', lang.hitch(this, function() {
				var gridItems = this._grid.getAllItems();
				array.forEach(gridItems, lang.hitch(this, function(item) {
					if (item.packageName) {
						this._grid.setDisabledItem(item.identifier, true);
					}
				}));
			}));

			this._page.startup();

			this._detailDialog = new DetailDialog({
				moduleStore: this.moduleStore
			});
			this.own(this._detailDialog);
			this._detailDialog.startup();
		},

		_portFormatter: function(id, rowIndex) {
			var item = this._grid._grid.getItem(rowIndex);
			var portStart = item.portStart;
			var portEnd = item.portEnd;
			if (portStart === portEnd) {
				return portStart;
			} else {
				return portStart + '-' + portEnd;
			}
		},

		_descriptionTooltip: function(label, rowIndex) {
			var widget = new Text({
				content: label
			});

			var item = this._grid.getRowValues(rowIndex);
			if (item.description) {
				var tooltip = new Tooltip({
					label: item.description,
					connectId: [widget.domNode],
					position: ['below']
				});
				widget.own(tooltip);
			}
			return widget;
		},

		deleteRules: function(ids) {
			ids = array.filter(ids, lang.hitch(this, function(id) {
				return ! this._grid.getDisabledItem(id);
			}));

			var _confirmDialog = lang.hitch(this, function() {
				var message = _('Are you sure to delete the %d selected firewall rule(s)?', ids.length);
				dialog.confirm(message, [{
					label: _('Cancel'),
					'default': true
				}, {
					label: _('Delete'),
					callback: _remove
				}]);
			});

			var _resultDialog = lang.hitch(this, function(result) {
				var failedObjects = array.map(array.filter(result, function(item) {
					return !item.success;
				}), lang.hitch(this, function(item) {
					return this._grid.getItem(item.object);
				}));

				if (failedObjects.length < 1) {
					return;
				}

				var msg = '<p>' + _('The following rule(s) could not be deleted:') + '</p><table>';
				array.forEach(failedObjects, function(object) {
					msg += '<tr>';
					msg += '<th>' + _('Local address: %s', object.address) + '</th>';
					msg += '<th>' + _('Port: %s', object.portStart) + '</th>';
					msg += '<th>' + _('Protocol: %s', object.protocol) + '</th>';
					msg += '</tr>';
				});
				msg += '</table>';

				dialog.alert(msg);
			});

			var _remove = lang.hitch(this, function() {
				this.standby(true);
				var transaction = this.moduleStore.transaction();
				array.forEach(ids, lang.hitch(this.moduleStore, 'remove'));
				transaction.commit().then(lang.hitch(this, function(result) {
					this.standby(false);
					_resultDialog(result);
				}), lang.hitch(this, function() {
					this.standby(false);
				}));
			});

			_confirmDialog();
		}
	});
});
