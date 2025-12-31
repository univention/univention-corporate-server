/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojox/string/sprintf",
	"umc/dialog",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/Grid",
	"umc/widgets/SearchForm",
	"umc/widgets/ComboBox",
	"umc/widgets/SearchBox",
	"umc/i18n!umc/modules/top"
], function(declare, lang, sprintf, dialog, Module, Page, Grid, SearchForm, ComboBox, SearchBox, _) {
	return declare("umc.modules.top", [ Module ], {

		_grid: null,
		_store: null,
		_searchWidget: null,
		_contextVariable: null,
		_page: null,

		idProperty: 'pid',

		killProcesses: function(signal, pids) {
			var params = {
				signal: signal,
				pid: pids
			};
			var msg;
			if (pids.length == 1) {
				msg = _('Please confirm sending %s to the selected process!', signal);
			}
			else {
				msg = _('Please confirm sending %(signal)s to the %(processid)s selected processes!', {signal: signal, processid: pids.length});
			}
			dialog.confirm(msg, [{
				'default': true,
				label: _('Cancel')
			}, {
				label: _('OK'),
				callback: lang.hitch(this, function() {
					this.standbyDuring(this.umcpCommand('top/kill', params)).then(lang.hitch(this, function() {
						this.addNotification(_('Signal (%s) sent successfully', signal));
						this.reloadGrid();
					}));
				})
			}]);
		},

		reloadGrid: function() {
			this._grid.filter(this._grid.query);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._page = new Page({
				helpText: _('This module generates an overview of all running processes. The search function can reduce the number of results. Specified processes can be selected and terminated. If a process can\'t be normally terminated (using SIGTERM signal), the termination can be forced (using SIGKILL signal).'),
				fullWidth: true
			});
			this.addChild(this._page);

			var actions = [{
				name: 'terminate',
				label: _('Terminate'),
				callback: lang.hitch(this, 'killProcesses', 'SIGTERM'),
				isStandardAction: true,
				isMultiAction: true
			}, {
				name: 'kill',
				label: _('Force termination'),
				callback: lang.hitch(this, 'killProcesses', 'SIGKILL'),
				isStandardAction: true,
				isMultiAction: true
			}];

			var columns = [{
				name: 'user',
				label: _('User'),
				width: '100px'
			}, {
				name: 'pid',
				label: _('PID'),
				width: '70px'
			}, {
				name: 'cpu',
				label: _('CPU (%)'),
				width: 'adjust',
				formatter: function(value) {
					return sprintf('%.1f', value);
				}
			}, {
				name: 'mem',
				label: _('Memory (%)'),
				width: 'adjust',
				formatter: function(value) {
					return sprintf('%.1f', value);
				}
			}, {
				name: 'command',
				label: _('Command'),
				width: 'auto'
			}];

			this._grid = new Grid({
				region: 'main',
				actions: actions,
				columns: columns,
				moduleStore: this.moduleStore,
				sortIndex: -3,
				query: {
					category: 'all',
					pattern: ''
				}
			});

			var widgets = [{
				type: ComboBox,
				name: 'category',
				value: 'all',
				label: _('Category'),
				staticValues: [
					{id: 'all', label: _('All')},
					{id: 'user', label: _('User')},
					{id: 'pid', label: _('PID')},
					{id: 'command', label: _('Command')}
				],
				'class': 'umcTextBoxOnBody'
			}, {
				type: SearchBox,
				name: 'pattern',
				value: '',
				inlineLabel: _('Search...'),
				onSearch: lang.hitch(this, function() {
					this._searchWidget.submit();
				}),
				'class': 'umcTextBoxOnBody'
			}];

			this._searchWidget = new SearchForm({
				region: 'nav',
				hideSubmitButton: true,
				widgets: widgets,
				layout: [['category', 'pattern']],
				onSearch: lang.hitch(this._grid, 'filter')
			});

			this._page.addChild(this._searchWidget);
			this._page.addChild(this._grid);

			this._page.startup();
		}
	});
});
