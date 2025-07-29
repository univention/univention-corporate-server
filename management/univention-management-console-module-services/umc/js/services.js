/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/Grid",
	"umc/widgets/SearchForm",
	"umc/widgets/SearchBox",
	"umc/i18n!umc/modules/services"
], function(declare, lang, array, dialog, tools, Module, Page, Grid, SearchForm, SearchBox, _) {
	return declare("umc.modules.services", [ Module ], {

		moduleStore: null,
		_grid: null,
		_page: null,
		_searchWidget: null,

		idProperty: 'service',

		buildRendering: function() {
			this.inherited(arguments);

			this._page = new Page({
				helpText: _('This module shows the system services and their current status. Specified services can be configured, started and stopped.'),
				fullWidth: true
			});
			this.addChild(this._page);

			var actions = [{
				name: 'start',
				label: _('Start'),
				iconClass: 'play',
				callback: lang.hitch(this, function(data) {
					if (data.length) {
						var command = 'services/start';
						var confirmMessage = _('Please confirm to start the following services: ');
						this._changeState(data, command, confirmMessage);
					}
				}),
				canExecute: function(item) { return !item.isRunning; },
				enablingMode: 'some',
				isStandardAction: true,
				isMultiAction: true
			}, {
				name: 'stop',
				label: _('Stop'),
				iconClass: 'square',
				callback: lang.hitch(this, function(data) {
					if (data.length) {
						var command = 'services/stop';
						var confirmMessage = _('Please confirm to stop the following services: ');
						this._changeState(data, command, confirmMessage);
					}
				}),
				canExecute: function(item) { return item.isRunning; },
				enablingMode: 'some',
				isStandardAction: true,
				isMultiAction: true
			}, {
				name: 'restart',
				label: _('Restart'),
				iconClass: 'refresh-ccw',
				callback: lang.hitch(this, function(data) {
					if (data.length) {
						var command = 'services/restart';
						var confirmMessage = _('Please confirm to restart the following services: ');
						this._changeState(data, command, confirmMessage);
					}
				}),
//				canExecute: function(item) { return item.isRunning; },
				enablingMode: 'some',
				isStandardAction: true,
				isMultiAction: true
			}, {
				name: 'startAutomatically',
				label: _('Start automatically'),
				callback: lang.hitch(this, function(data) {
					var command = 'services/start_auto';
					var confirmMessage = _('Please confirm to automatically start the following services: ');
					this._changeState(data, command, confirmMessage);
				}),
				canExecute: function(item) { return item.autostart !== 'yes'; },
				enablingMode: 'some',
				isStandardAction: false,
				isMultiAction: true
			}, {
				name: 'startManually',
				label: _('Start manually'),
				callback: lang.hitch(this, function(data) {
					var command = 'services/start_manual';
					var confirmMessage = _('Please confirm to manually start the following services: ');
					this._changeState(data, command, confirmMessage);
				}),
				canExecute: function(item) { return item.autostart !== 'manually'; },
				enablingMode: 'some',
				isStandardAction: false,
				isMultiAction: true
			}, {
				name: 'startNever',
				label: _('Start never'),
				callback: lang.hitch(this, function(data) {
					var command = 'services/start_never';
					var confirmMessage = _('Please confirm to never start the following services: ');
					this._changeState(data, command, confirmMessage);
				}),
				canExecute: function(item) { return item.autostart !== 'no'; },
				enablingMode: 'some',
				isStandardAction: false,
				isMultiAction: true
			}];

			var columns = [{
				name: 'service',
				label: _('Name')//,
			}, {
				name: 'isRunning',
				label: _('Status'),
//				width: 'adjust',  // FIXME: the label must be longer than entries
				width: '15%',
				formatter: lang.hitch(this, function(value) {
					if (value === true) {
						return _('running');
					} else {
						return _('stopped');
					}
				})
			}, {
				name: 'autostart',
				label: _('Start type'),
//				width: 'adjust',  // FIXME: the label must be longer than entries
				width: '15%',
				formatter: lang.hitch(this, function(value) {
					if (value == 'no') {
						return _('Never');
					} else if (value == 'manually') {
						return _('Manually');
					} else {
						return _('Automatically');
					}
				})
			}, {
				name: 'description',
				label: _('Description'),
				formatter: lang.hitch(this, function(value) {
					if (value === null) {
						return '-';
					} else {
						return value;
					}
				})
			}];

			this._grid = new Grid({
				region: 'main',
				actions: actions,
				columns: columns,
				moduleStore: this.moduleStore,
				query: {
					pattern: ''
				}
			});

			var widgets = [{
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
				layout: ['pattern'],
				onSearch: lang.hitch(this._grid, 'filter')
			});

			this._page.addChild(this._searchWidget);
			this._page.addChild(this._grid);

			this._page.startup();
		},

		reloadGrid: function() {
			data = this._searchWidget.get('value');
			this._grid.filter(data);
		},

		_changeState: function(data, command, confirmMessage) {
			confirmMessage += '<ul>';
			//test if stopping this service breaks UMC
			var umcRequirements = ['apache2', 'univention-management-console-server'];
			var umcDisablers = ['services/stop', 'services/restart', 'services/start_manual', 'services/start_never'];
			var breaksUMC = false;
			array.forEach(data, function(idata) {
				if (umcRequirements.indexOf(idata) >= 0 && umcDisablers.indexOf(command) >= 0) {
					breaksUMC = true;
				}
				confirmMessage += '<li>' + idata + '</li>';
			});
			confirmMessage += '</ul>';
			if (breaksUMC) {
				confirmMessage += '<b>' + _('Warning: Stopping apache or UMC services will interrupt all current connections to the Univention Management Console. It might be necessary for all users to login again.') + '</b>';
			}

			dialog.confirm(confirmMessage, [{
				'default': true,
				label: _('Cancel')
			}, {
				label: _('OK'),
				callback: lang.hitch(this, function() {
					this.standbyDuring(tools.umcpCommand(command, data)).then(lang.hitch(this, function(response) {
						this.reloadGrid();
					}));
				})
			}]);
		}
	});
});
