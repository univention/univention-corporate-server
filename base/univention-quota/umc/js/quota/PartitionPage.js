/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojox/string/sprintf",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Grid",
	"umc/widgets/Page",
	"umc/widgets/SearchForm",
	"umc/widgets/Text",
	"umc/widgets/SearchBox",
	"umc/i18n!umc/modules/quota"
], function(declare, lang, array, sprintf, dialog, tools, Grid, Page, SearchForm, Text, SearchBox, _) {
	return declare("umc.modules.quota.PartitionPage", [ Page ], {

		moduleStore: null,
		standby: null,
		standbyDuring: null,
		partitionDevice: null,
		_grid: null,
		_partitionInfo: null,
		_searchForm: null,

		_getPartitionInfo: function() {
			this.standbyDuring(tools.umcpCommand('quota/partitions/info', {'partitionDevice': this.partitionDevice})).then(lang.hitch(this, function(data) {
				var helpText = lang.replace(
					_('Mount point: ') + '{mountPoint} ' +
					_('Filesystem: ') + '{filesystem} ' +
					_('Options: ') + ' {options}',
					data.result
				);
				this.set('helpText', helpText);
			}));
		},

		postMixInProperties: function() {
			this.inherited(arguments);
			this.headerButtons = [{
				name: 'close',
				label: _('Back to overview'),
				callback: lang.hitch(this, 'onShowOverview')
			}];
			this.helpText = _('loading...');
		},

		buildRendering: function() {
			this.inherited(arguments);
			this.renderGrid();
			this._getPartitionInfo();
			this.addChild(this._searchForm);
			this.addChild(this._grid);
		},

		postCreate: function() {
			this.inherited(arguments);
			this.startup();
		},

		renderGrid: function() {
			var widgets = [{
				type: SearchBox,
				name: 'filter',
				'class': 'umcTextBoxOnBody',
				value: '',
				inlineLabel: _('Search...'),
				onSearch: lang.hitch(this, function() {
					this._searchForm.submit();
				})
			}];

			this._searchForm = new SearchForm({
				region: 'nav',
				widgets: widgets,
				layout: ['filter'],
				hideSubmitButton: true,
				onSearch: lang.hitch(this, function(data) {
					data.partitionDevice = this.partitionDevice;
					this._grid.filter(data);
				})
			});

			var actions = [{
				name: 'add',
				label: _('Add'),
				iconClass: 'plus',
				isContextAction: false,
				isStandardAction: true,
				isMultiAction: false,
				callback: lang.hitch(this, function() {
					this.onShowDetailPage();
				})
			}, {
				name: 'edit',
				label: _('Configure'),
				iconClass: 'edit-2',
				isStandardAction: true,
				isMultiAction: false,
				callback: lang.hitch(this, function(ids, items) {
					this.onShowDetailPage(items[0]);
				})
			}, {
				name: 'remove',
				label: _('Remove'),
				iconClass: 'trash',
				isStandardAction: true,
				isMultiAction: true,
				callback: lang.hitch(this, function(data) {
					this.onRemoveUsers(data);
				})
			}];

			var columns = [{
				name: 'user',
				label: _('User'),
				width: 'auto'
			}, {
				name: 'sizeLimitUsed',
				label: _('Size (MB) (used/soft/hard)'),
				width: 'adjust',
				formatter: lang.hitch(this, function(id, item) {
					return sprintf('%(sizeLimitUsed).0f/%(sizeLimitSoft).0f/%(sizeLimitHard).0f', item);
				})
			}, {
				name: 'sizeLimitTime',
				label: _('Grace'),
				width: 'adjust'
			}, {
				name: 'fileLimitUsed',
				label: _('Files (used/soft/hard)'),
				width: 'adjust',
				formatter: lang.hitch(this, function(id, item) {
					return lang.replace('{fileLimitUsed}/{fileLimitSoft}/{fileLimitHard}', item);
				})
			}, {
				name: 'fileLimitTime',
				label: _('Grace'),
				width: 'adjust'
			}];

			this._grid = new Grid({
				region: 'main',
				actions: actions,
				columns: columns,
				moduleStore: this.moduleStore,
				query: {
					filter: '*',
					partitionDevice: this.partitionDevice
				}
			});
		},

		filter: function() {
			var data = this._searchForm.get('value');
			data.partitionDevice = this.partitionDevice;
			this._grid.filter(data);
		},

		onShowOverview: function() {
			return true;
		},

		onShowDetailPage: function(/*data*/) {
			return true;
		},

		onClosePage: function() {
			return true;
		},

		onRemoveUsers: function(ids) {
			var dialogMessage = '';
			var usernames = array.map(ids, lang.hitch(this, function(id) {
				var item = this._grid.getItem(id);
				return item.user;
			}));
			if (usernames.length === 0) {
				return;
			} else if (usernames.length === 1) {
				dialogMessage = _('Please confirm to remove the following user: %s', usernames);
			} else {
				dialogMessage = _('Please confirm to remove the following %(length)s users: %(usernames)s', {'usernames': usernames, 'length': usernames.length});
			}
			dialog.confirm(dialogMessage, [{
				label: _('Cancel'),
				'default': true
			}, {
				label: _('OK'),
				callback: lang.hitch(this, function() {
					var transaction = this.moduleStore.transaction();
					array.forEach(ids, function(iid) {
						this.moduleStore.remove(iid);
					}, this);
					this.standbyDuring(transaction.commit());
				})
			}]);
		}
	});
});
