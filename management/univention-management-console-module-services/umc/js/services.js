/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.services");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.SearchForm");

dojo.declare("umc.modules.services", [ umc.widgets.Module, umc.i18n.Mixin ], {

	moduleStore: null,
	_grid: null,
	_page: null,
	_searchWidget: null,

	i18nClass: 'umc.modules.services',
	idProperty: 'service',

	buildRendering: function() {
		this.inherited(arguments);

		this._page = new umc.widgets.Page({
			headerText: this._('System services')
		});
		this.addChild(this._page);

		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('List of services')
		});
		this._page.addChild(titlePane);

		var actions = [{
			name: 'start',
			label: this._('Start services'),
			callback: dojo.hitch(this, function(data) {
				if (data.length) {
					var command = 'services/start';
					var confirmMessage = this._('Please confirm to start the following services: ');
					var errorMessage = this._('Starting the following services failed: ');
					this._changeState(data, command, confirmMessage, errorMessage);
				}
			}),
			isStandardAction: false,
			isMultiAction: true
		}, {
			name: 'stop',
			label: this._('Stop services'),
			callback: dojo.hitch(this, function(data) {
				if (data.length) {
					var command = 'services/stop';
					var confirmMessage = this._('Please confirm to stop the following services: ');
					var errorMessage = this._('Stopping the following services failed: ');
					this._changeState(data, command, confirmMessage, errorMessage);
				}
			}),
			isStandardAction: false,
			isMultiAction: true
		}, {
			name: 'restart',
			label: this._('Restart services'),
			callback: dojo.hitch(this, function(data) {
				if (data.length) {
					var command = 'services/restart';
					var confirmMessage = this._('Please confirm to restart the following services: ');
					var errorMessage = this._('Restarting the following services failed: ');
					this._changeState(data, command, confirmMessage, errorMessage);
				}
			}),
			isStandardAction: false,
			isMultiAction: true
		}, {
			name: 'startAutomatically',
			label: this._('Start automatically'),
			callback: dojo.hitch(this, function(data) {
				var command = 'services/start_auto';
				var confirmMessage = this._('Please confirm to automatically start the following services: ');
				var errorMessage = this._('Could not change start type of the following services: ');
				this._changeState(data, command, confirmMessage, errorMessage);
			}),
			isStandardAction: false,
			isMultiAction: true
		}, {
			name: 'startManually',
			label: this._('Start manually'),
			callback: dojo.hitch(this, function(data) {
				var command = 'services/start_manual';
				var confirmMessage = this._('Please confirm to manually start the following services: ');
				var errorMessage = this._('Could not change start type of the following services: ');
				this._changeState(data, command, confirmMessage, errorMessage);
			}),
			isStandardAction: false,
			isMultiAction: true
		}, {
			name: 'startNever',
			label: this._('Start never'),
			callback: dojo.hitch(this, function(data) {
				var command = 'services/start_never';
				var confirmMessage = this._('Please confirm to never start the following services: ');
				var errorMessage = this._('Could not change start type of the following services: ');
				this._changeState(data, command, confirmMessage, errorMessage);
			}),
			isStandardAction: false,
			isMultiAction: true
		}];

		var columns = [{
			name: 'service',
			label: this._('Name'),
            width: '200px'
		}, {
			name: 'isRunning',
			label: this._('Status'),
            width: 'adjust',
			formatter: dojo.hitch(this, function(value) {
				if (value === true) {
					return this._('running');
				} else {
					return this._('stopped');
				}
			})
		}, {
			name: 'autostart',
			label: this._('Start type'),
            width: '100px',
			formatter: dojo.hitch(this, function(value) {
				if (value == 'no') {
					return this._('Never');
				} else if (value == 'manually') {
					return this._('Manually');
				} else {
					return this._('Automatically');
				}
			})
		}, {
			name: 'description',
			label: this._('Description'),
            width: 'auto',
			formatter: dojo.hitch(this, function(value) {
				if (value === null) {
					return '-';
				} else {
					return value;
				}
			})
		}];

		this._grid = new umc.widgets.Grid({
			region: 'center',
			actions: actions,
			columns: columns,
			moduleStore: this.moduleStore,
			query: {
                filter: '*'
            }
		});
		titlePane.addChild(this._grid);

		var widgets = [{
			type: 'TextBox',
			name: 'filter',
			value: '*',
			label: this._('Keyword')
		}];

		this._searchWidget = new umc.widgets.SearchForm({
			region: 'top',
			widgets: widgets,
			layout: [[ 'filter', 'submit', 'reset' ]],
			onSearch: dojo.hitch(this._grid, 'filter')
		});

		titlePane.addChild(this._searchWidget);

		this._page.startup();
    },

	_changeState: function(data, command, confirmMessage, errorMessage) {
		confirmMessage += '<ul>';
		dojo.forEach(data, function(idata) {
			confirmMessage += '<li>' + idata + '</li>';
		});
		confirmMessage += '</ul>';

		umc.dialog.confirm(confirmMessage, [{
			label: this._('OK'),
			callback: dojo.hitch(this, function() {
				this.standby(true);
				umc.tools.umcpCommand(command, data).then(
					dojo.hitch(this, function(response) {
						this.standby(false);
						if (response.result.success === false) {
							errorMessage += '<ul>';
							dojo.forEach(response.result.objects, function(item) {
								errorMessage += '<li>' + item + '</li>';
							});
							errorMessage += '</ul>';
							umc.dialog.alert(errorMessage);
						}
						data = this._searchWidget.gatherFormValues();
						this._grid.filter(data);
					}), dojo.hitch(this, function() {
						this.standby(false);
					})
				);
			})
		}, {
			label: this._('Cancel')
		}]);
	}
});
